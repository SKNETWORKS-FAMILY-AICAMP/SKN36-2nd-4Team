"""Build a queryable SQLite copy of the final LoL churn datasets.

Usage:
    python -m data_pipeline.build_sqlite_db
    python -m data_pipeline.build_sqlite_db --replace  # rebuild an existing generated DB

The script reads CSV sources and writes only
lol_churn_all_data/database/lol_churn.db.
It requires only Python's standard library.
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import tempfile
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


from data_pipeline.paths import DATA_DIR as ROOT
ML_CSV = ROOT / "final" / "final_ml_features.csv"
SEQUENCE_CSV = ROOT / "final" / "final_transformer_sequence.csv"
DB_DIR = ROOT / "database"
DB_PATH = DB_DIR / "lol_churn.db"

ML_FEATURES = (
    ("games_7d", "INTEGER"),
    ("games_30d", "INTEGER"),
    ("games_90d", "INTEGER"),
    ("games_prev30d", "INTEGER"),
    ("activity_change_30d", "INTEGER"),
    ("active_days_30d", "INTEGER"),
    ("days_since_last_game", "REAL"),
    ("avg_gap_30d", "REAL"),
    ("max_gap_30d", "REAL"),
    ("last_gap", "REAL"),
    ("winrate_20", "REAL"),
    ("avg_kda_20", "REAL"),
    ("avg_kills_20", "REAL"),
    ("avg_deaths_20", "REAL"),
    ("avg_assists_20", "REAL"),
    ("losing_streak", "INTEGER"),
    ("winrate_change_10", "REAL"),
    ("avg_game_duration_20", "REAL"),
    ("avg_gold_per_min_20", "REAL"),
    ("avg_cs_per_min_20", "REAL"),
    ("avg_damage_per_min_20", "REAL"),
    ("avg_vision_per_min_20", "REAL"),
    ("unique_champions_20", "INTEGER"),
    ("top_champion_ratio_20", "REAL"),
    ("unique_modes_30d", "INTEGER"),
    ("mode_switch_rate_20", "REAL"),
    ("ranked_solo_ratio_30d", "REAL"),
    ("ranked_flex_ratio_30d", "REAL"),
    ("normal_ratio_30d", "REAL"),
    ("aram_ratio_30d", "REAL"),
    ("arena_ratio_30d", "REAL"),
    ("rotating_ratio_30d", "REAL"),
    ("other_ratio_30d", "REAL"),
    ("actual_history_matches", "INTEGER"),
)

SEQUENCE_FIELDS = (
    ("sequenceIndex", "sequence_index", "INTEGER"),
    ("eventTime", "event_time", "TEXT"),
    ("timeGapDays", "time_gap_days", "REAL"),
    ("daysBeforeCutoff", "days_before_cutoff", "REAL"),
    ("queueId", "queue_id", "INTEGER"),
    ("modeGroup", "mode_group", "TEXT"),
    ("championId", "champion_id", "INTEGER"),
    ("teamPosition", "team_position", "TEXT"),
    ("win", "win", "INTEGER"),
    ("kills", "kills", "INTEGER"),
    ("deaths", "deaths", "INTEGER"),
    ("assists", "assists", "INTEGER"),
    ("kda", "kda", "REAL"),
    ("gameDurationMin", "game_duration_min", "REAL"),
    ("goldPerMin", "gold_per_min", "REAL"),
    ("csPerMin", "cs_per_min", "REAL"),
    ("damagePerMin", "damage_per_min", "REAL"),
    ("visionPerMin", "vision_per_min", "REAL"),
)


def csv_rows(path: Path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"Missing or duplicated header: {path}")
        yield from reader


def typed(value: str | None, sql_type: str):
    if value is None or value.strip() == "":
        return None
    if sql_type == "INTEGER":
        number = float(value)
        if not number.is_integer():
            raise ValueError(f"Expected integer, got {value!r}")
        return int(number)
    if sql_type == "REAL":
        return float(value)
    return value.strip()


def required(value: str | None, label: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f"Missing required value: {label}")
    return value.strip()


def create_schema(conn: sqlite3.Connection) -> None:
    ml_columns = ",\n            ".join(f"{name} {sql_type}" for name, sql_type in ML_FEATURES)
    sequence_columns = ",\n            ".join(
        f"{db_name} {sql_type}" for _, db_name, sql_type in SEQUENCE_FIELDS
        if db_name != "sequence_index"
    )
    conn.executescript(
        f"""
        PRAGMA foreign_keys = ON;

        CREATE TABLE users (
            team_id INTEGER NOT NULL CHECK (team_id BETWEEN 1 AND 4),
            player_id TEXT NOT NULL,
            PRIMARY KEY (team_id, player_id)
        ) WITHOUT ROWID;

        CREATE TABLE batches (
            team_id INTEGER NOT NULL CHECK (team_id BETWEEN 1 AND 4),
            batch_id INTEGER NOT NULL CHECK (batch_id > 0),
            batch_name TEXT NOT NULL UNIQUE,
            PRIMARY KEY (team_id, batch_id)
        ) WITHOUT ROWID;

        CREATE TABLE user_batches (
            team_id INTEGER NOT NULL,
            player_id TEXT NOT NULL,
            batch_id INTEGER NOT NULL,
            PRIMARY KEY (team_id, player_id, batch_id),
            FOREIGN KEY (team_id, player_id) REFERENCES users(team_id, player_id),
            FOREIGN KEY (team_id, batch_id) REFERENCES batches(team_id, batch_id)
        ) WITHOUT ROWID;

        CREATE TABLE targets (
            team_id INTEGER NOT NULL,
            player_id TEXT NOT NULL,
            cutoff_date TEXT NOT NULL,
            churn INTEGER NOT NULL CHECK (churn IN (0, 1)),
            future30d_has_match INTEGER NOT NULL CHECK (future30d_has_match IN (0, 1)),
            PRIMARY KEY (team_id, player_id, cutoff_date),
            CHECK (churn + future30d_has_match = 1),
            FOREIGN KEY (team_id, player_id) REFERENCES users(team_id, player_id)
        ) WITHOUT ROWID;

        CREATE TABLE ml_features (
            team_id INTEGER NOT NULL,
            player_id TEXT NOT NULL,
            cutoff_date TEXT NOT NULL,
            source_batch_id INTEGER NOT NULL,
            {ml_columns},
            PRIMARY KEY (team_id, player_id, cutoff_date),
            FOREIGN KEY (team_id, player_id, cutoff_date)
                REFERENCES targets(team_id, player_id, cutoff_date),
            FOREIGN KEY (team_id, source_batch_id) REFERENCES batches(team_id, batch_id)
        ) WITHOUT ROWID;

        CREATE TABLE sequence_events (
            team_id INTEGER NOT NULL,
            player_id TEXT NOT NULL,
            cutoff_date TEXT NOT NULL,
            sequence_index INTEGER NOT NULL CHECK (sequence_index BETWEEN 0 AND 29),
            source_batch_id INTEGER NOT NULL,
            match_id TEXT,
            {sequence_columns},
            PRIMARY KEY (team_id, player_id, cutoff_date, sequence_index),
            FOREIGN KEY (team_id, player_id, cutoff_date)
                REFERENCES targets(team_id, player_id, cutoff_date),
            FOREIGN KEY (team_id, source_batch_id) REFERENCES batches(team_id, batch_id)
        ) WITHOUT ROWID;

        CREATE INDEX idx_sequence_mode ON sequence_events(cutoff_date, mode_group);
        CREATE INDEX idx_sequence_time ON sequence_events(cutoff_date, event_time);
        CREATE UNIQUE INDEX idx_sequence_match_id
            ON sequence_events(team_id, player_id, cutoff_date, match_id)
            WHERE match_id IS NOT NULL;

        CREATE VIEW v_team_churn AS
            SELECT cutoff_date, team_id, COUNT(*) AS users,
                   SUM(churn) AS churn_users,
                   ROUND(100.0 * SUM(churn) / COUNT(*), 2) AS churn_percent
            FROM targets
            GROUP BY cutoff_date, team_id;

        CREATE VIEW v_mode_usage AS
            WITH user_mode AS (
                SELECT cutoff_date, team_id, player_id, mode_group,
                       COUNT(*) AS games
                FROM sequence_events
                GROUP BY cutoff_date, team_id, player_id, mode_group
            )
            SELECT cutoff_date, mode_group, COUNT(*) AS users,
                   SUM(games) AS games
            FROM user_mode
            GROUP BY cutoff_date, mode_group;
        """
    )


def create_batches(conn: sqlite3.Connection) -> list[tuple[int, int, Path]]:
    batches: list[tuple[int, int, Path]] = []
    for team_id in range(1, 5):
        team_name = f"team{team_id}"
        for batch_dir in sorted((ROOT / team_name).glob(f"{team_name}_batch*")):
            if not batch_dir.is_dir():
                continue
            suffix = batch_dir.name.removeprefix(f"{team_name}_batch")
            if not suffix.isdigit():
                raise ValueError(f"Unexpected batch directory: {batch_dir}")
            batch_id = int(suffix)
            conn.execute(
                "INSERT INTO batches VALUES (?, ?, ?)",
                (team_id, batch_id, batch_dir.name),
            )
            batches.append((team_id, batch_id, batch_dir))
    if not batches:
        raise ValueError("No team batch directories found")
    return batches


def load_ml(conn: sqlite3.Connection, cutoff_expected: str) -> tuple[int, Counter]:
    columns = [name for name, _ in ML_FEATURES]
    placeholders = ", ".join("?" for _ in range(4 + len(columns)))
    column_sql = ", ".join(("team_id", "player_id", "cutoff_date", "source_batch_id", *columns))
    sql = f"INSERT INTO ml_features ({column_sql}) VALUES ({placeholders})"
    total = 0
    churn_counts: Counter = Counter()
    for row in csv_rows(ML_CSV):
        team_id = typed(row.get("team_id"), "INTEGER")
        player_id = required(row.get("player_id"), "player_id")
        cutoff_date = required(row.get("cutoff_date"), "cutoff_date")
        batch_id = typed(row.get("batch_id"), "INTEGER")
        churn = typed(row.get("churn"), "INTEGER")
        future = typed(row.get("future30d_has_match"), "INTEGER")
        if cutoff_date != cutoff_expected:
            raise ValueError(f"Unexpected cutoff date: {cutoff_date}")
        conn.execute("INSERT INTO users VALUES (?, ?)", (team_id, player_id))
        conn.execute(
            "INSERT INTO targets VALUES (?, ?, ?, ?, ?)",
            (team_id, player_id, cutoff_date, churn, future),
        )
        conn.execute(
            sql,
            (team_id, player_id, cutoff_date, batch_id,
             *(typed(row.get(name), sql_type) for name, sql_type in ML_FEATURES)),
        )
        churn_counts[churn] += 1
        total += 1
    return total, churn_counts


def load_batch_memberships(
    conn: sqlite3.Connection, batches: list[tuple[int, int, Path]]
) -> tuple[int, int]:
    source_rows = 0
    for team_id, batch_id, batch_dir in batches:
        path = batch_dir / "06_ml_features.csv"
        for row in csv_rows(path):
            player_id = required(row.get("player_id"), f"{path}: player_id")
            conn.execute(
                "INSERT OR IGNORE INTO user_batches VALUES (?, ?, ?)",
                (team_id, player_id, batch_id),
            )
            source_rows += 1
    membership_count = conn.execute("SELECT COUNT(*) FROM user_batches").fetchone()[0]
    return source_rows, membership_count


def normalize_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"eventTime lacks timezone: {value!r}")
    return parsed.astimezone(timezone.utc)


def load_sequences(conn: sqlite3.Connection, cutoff_date: str) -> tuple[int, int]:
    fields = [name for _, name, _ in SEQUENCE_FIELDS]
    insert_columns = (
        "team_id", "player_id", "cutoff_date", "source_batch_id", "match_id", *fields
    )
    sql = (
        f"INSERT INTO sequence_events ({', '.join(insert_columns)}) "
        f"VALUES ({', '.join('?' for _ in insert_columns)})"
    )
    targets = {
        (team_id, player_id): churn
        for team_id, player_id, churn in conn.execute(
            "SELECT team_id, player_id, churn FROM targets"
        )
    }
    cutoff_time = datetime.fromisoformat(cutoff_date).replace(tzinfo=timezone.utc)
    last_key: tuple[int, str] | None = None
    last_time: datetime | None = None
    expected_index = 0
    seen_users: set[tuple[int, str]] = set()
    total = 0
    match_id_present = 0
    pending = []
    for row in csv_rows(SEQUENCE_CSV):
        team_id = typed(row.get("team_id"), "INTEGER")
        player_id = required(row.get("player_id"), "sequence player_id")
        batch_id = typed(row.get("batch_id"), "INTEGER")
        key = (team_id, player_id)
        if key not in targets:
            raise ValueError(f"Sequence user is missing from targets: {key}")
        if typed(row.get("churn"), "INTEGER") != targets[key]:
            raise ValueError(f"Sequence churn differs from target: {key}")
        index = typed(row.get("sequenceIndex"), "INTEGER")
        event_time = normalize_time(required(row.get("eventTime"), "eventTime"))
        if event_time >= cutoff_time:
            raise ValueError(f"Sequence event is on/after cutoff: {key}, {event_time}")
        if key != last_key:
            if key in seen_users:
                raise ValueError(f"Sequence user rows are not contiguous: {key}")
            seen_users.add(key)
            expected_index = 0
            last_time = None
            last_key = key
        if index != expected_index:
            raise ValueError(f"Sequence index gap for {key}: got {index}, expected {expected_index}")
        if last_time is not None and event_time < last_time:
            raise ValueError(f"Sequence event order is not chronological: {key}")
        expected_index += 1
        last_time = event_time
        match_id = row.get("matchId") or row.get("match_id") or None
        match_id_present += match_id is not None
        values = []
        for source_name, _, sql_type in SEQUENCE_FIELDS:
            if source_name == "eventTime":
                values.append(event_time.isoformat(timespec="microseconds"))
            else:
                values.append(typed(row.get(source_name), sql_type))
        pending.append((team_id, player_id, cutoff_date, batch_id, match_id, *values))
        if len(pending) >= 2000:
            conn.executemany(sql, pending)
            pending.clear()
        total += 1
    if pending:
        conn.executemany(sql, pending)
    return total, match_id_present


def verify(conn: sqlite3.Connection, ml_count: int, sequence_count: int) -> None:
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("SQLite integrity_check failed")
    if conn.execute("PRAGMA foreign_key_check").fetchone():
        raise ValueError("SQLite foreign_key_check failed")
    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("users", "batches", "user_batches", "targets", "ml_features", "sequence_events")
    }
    if counts["users"] != ml_count or counts["targets"] != ml_count or counts["ml_features"] != ml_count:
        raise ValueError(f"User/target/ML count mismatch: {counts}")
    if counts["sequence_events"] != sequence_count:
        raise ValueError(f"Sequence count mismatch: {counts}")
    missing_sequence_users = conn.execute(
        """SELECT COUNT(*) FROM targets AS t
           WHERE NOT EXISTS (
               SELECT 1 FROM sequence_events AS s
               WHERE s.team_id=t.team_id AND s.player_id=t.player_id
                 AND s.cutoff_date=t.cutoff_date
           )"""
    ).fetchone()[0]
    if missing_sequence_users:
        raise ValueError(f"Users without sequence rows: {missing_sequence_users}")
    print("Verified tables:")
    for table, count in counts.items():
        print(f"  {table}: {count:,}")
    print("Team churn:")
    for row in conn.execute(
        "SELECT team_id, users, churn_users, churn_percent FROM v_team_churn ORDER BY team_id"
    ):
        print(f"  team{row[0]}: {row[1]:,} users, {row[2]:,} churn ({row[3]:.2f}%)")
    print("Mode usage in the retained sequences:")
    for row in conn.execute(
        "SELECT mode_group, users, games FROM v_mode_usage ORDER BY games DESC"
    ):
        print(f"  {row[0]}: {row[1]:,} users, {row[2]:,} games")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace", action="store_true", help="Replace an existing generated DB after a successful rebuild."
    )
    args = parser.parse_args()
    if DB_PATH.exists() and not args.replace:
        parser.error(f"Database exists: {DB_PATH}. Use --replace to rebuild it.")
    if not ML_CSV.is_file() or not SEQUENCE_CSV.is_file():
        parser.error("Final CSV files are missing. Restore the prepared files in lol_churn_all_data/final before building the database.")
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # Build beside the destination. The existing DB stays usable until all
    # inserts and integrity checks have passed.
    with tempfile.NamedTemporaryFile(
        prefix="lol_churn_build_", suffix=".db", dir=DB_DIR, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with closing(sqlite3.connect(temporary_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            create_schema(conn)
            batches = create_batches(conn)
            ml_count, churn_counts = load_ml(conn, "2026-08-01")
            batch_source_rows, memberships = load_batch_memberships(conn, batches)
            sequence_count, match_id_count = load_sequences(conn, "2026-08-01")
            verify(conn, ml_count, sequence_count)
            print(
                f"Source batch ML rows: {batch_source_rows:,}; unique batch memberships: {memberships:,}"
            )
            print(f"Targets: churn=0 {churn_counts[0]:,}; churn=1 {churn_counts[1]:,}")
            if match_id_count == 0:
                print("Match IDs: absent in the current sequence CSV; match_id is NULL.")
            conn.commit()
        os.replace(temporary_path, DB_PATH)
        print(f"Created: {DB_PATH} ({DB_PATH.stat().st_size:,} bytes)")
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    main()
