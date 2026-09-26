# Riot API 데이터 수집

Riot API에서 PUUID 기반 경기 ID와 경기 상세 정보를 수집하는 코드입니다. 이 브랜치에는 **수집 코드만** 두며, API 키·PUUID 목록·수집 CSV/DB는 포함하지 않습니다.

## 실행

PowerShell에서 `data_collection` 폴더로 이동한 뒤:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:RIOT_API_KEY = "발급받은 Riot API 키"
python riot_churn_vscode.py --help
```

실행 모드와 입력 파일은 스크립트의 `--help`를 확인하세요. API 키와 PUUID 입력 파일은 로컬에서만 준비하고 Git에 추가하지 마세요. Riot API rate limit에 맞춰 수집되며, 생성되는 사용자·경기 파일은 별도 데이터 저장소에서 관리해야 합니다.

`riot_churn_self_seed_fixed.py`와 `riot_churn_self_seed.py`는 API를 통한 seed/cohort 구성 및 수집 흐름의 대안 스크립트입니다. 같은 출력 폴더에서 여러 방식을 동시에 실행하지 마세요.
