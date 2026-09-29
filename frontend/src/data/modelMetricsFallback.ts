import type { ModelExperimentDetails, ModelMetricsResponse } from '../api/types'

// backend/app/data/core_model_experiment.json과 동일한 발표용 모델 평가 스냅샷입니다.
// API가 일시적으로 실패하거나 pending을 반환해도 모델 성능 페이지 전체를 유지합니다.
const details: ModelExperimentDetails = {
  "model_version": "core-reselected-2026-08-01",
  "selected_candidate": {
    "feature_set": "aggregate33",
    "treatment": "class_weight_balanced"
  },
  "nested_selection_oof": {
    "all_core": {
      "users": 2381,
      "churners": 363,
      "prevalence": 0.1524569508609828,
      "pr_auc_ap": 0.38156845775001147,
      "roc_auc": 0.7775475268042167,
      "top_10pct": {
        "selected": 239,
        "found_churn": 116,
        "false_alarms": 123,
        "precision": 0.48535564853556484,
        "recall": 0.31955922865013775,
        "f1": 0.3853820598006645
      },
      "top_20pct": {
        "selected": 477,
        "found_churn": 186,
        "false_alarms": 291,
        "precision": 0.389937106918239,
        "recall": 0.512396694214876,
        "f1": 0.4428571428571429
      }
    },
    "solo_focused": {
      "users": 1026,
      "churners": 139,
      "prevalence": 0.1354775828460039,
      "pr_auc_ap": 0.352601263566878,
      "roc_auc": 0.7519972747844567,
      "top_10pct": {
        "selected": 103,
        "found_churn": 43,
        "false_alarms": 60,
        "precision": 0.4174757281553398,
        "recall": 0.30935251798561153,
        "f1": 0.35537190082644626
      },
      "top_20pct": {
        "selected": 206,
        "found_churn": 65,
        "false_alarms": 141,
        "precision": 0.3155339805825243,
        "recall": 0.4676258992805755,
        "f1": 0.37681159420289856
      }
    },
    "other": {
      "users": 1355,
      "churners": 224,
      "prevalence": 0.16531365313653137,
      "pr_auc_ap": 0.4063860112215471,
      "roc_auc": 0.7915482505999747,
      "top_10pct": {
        "selected": 136,
        "found_churn": 70,
        "false_alarms": 66,
        "precision": 0.5147058823529411,
        "recall": 0.3125,
        "f1": 0.3888888888888889
      },
      "top_20pct": {
        "selected": 271,
        "found_churn": 122,
        "false_alarms": 149,
        "precision": 0.45018450184501846,
        "recall": 0.5446428571428571,
        "f1": 0.49292929292929294
      }
    }
  },
  "selected_candidate_oof_exploratory": {
    "all_core": {
      "users": 2381,
      "churners": 363,
      "prevalence": 0.1524569508609828,
      "pr_auc_ap": 0.41024351517280916,
      "roc_auc": 0.7830011985791786,
      "top_10pct": {
        "selected": 239,
        "found_churn": 118,
        "false_alarms": 121,
        "precision": 0.49372384937238495,
        "recall": 0.325068870523416,
        "f1": 0.39202657807308966
      },
      "top_20pct": {
        "selected": 477,
        "found_churn": 190,
        "false_alarms": 287,
        "precision": 0.39832285115303984,
        "recall": 0.5234159779614325,
        "f1": 0.45238095238095233
      }
    },
    "solo_focused": {
      "users": 1026,
      "churners": 139,
      "prevalence": 0.1354775828460039,
      "pr_auc_ap": 0.36405069859340805,
      "roc_auc": 0.7435701945771453,
      "top_10pct": {
        "selected": 103,
        "found_churn": 45,
        "false_alarms": 58,
        "precision": 0.4368932038834951,
        "recall": 0.3237410071942446,
        "f1": 0.371900826446281
      },
      "top_20pct": {
        "selected": 206,
        "found_churn": 64,
        "false_alarms": 142,
        "precision": 0.3106796116504854,
        "recall": 0.460431654676259,
        "f1": 0.37101449275362314
      }
    },
    "other": {
      "users": 1355,
      "churners": 224,
      "prevalence": 0.16531365313653137,
      "pr_auc_ap": 0.43985619186569713,
      "roc_auc": 0.8035951117847671,
      "top_10pct": {
        "selected": 136,
        "found_churn": 71,
        "false_alarms": 65,
        "precision": 0.5220588235294118,
        "recall": 0.3169642857142857,
        "f1": 0.39444444444444443
      },
      "top_20pct": {
        "selected": 271,
        "found_churn": 123,
        "false_alarms": 148,
        "precision": 0.45387453874538747,
        "recall": 0.5491071428571429,
        "f1": 0.496969696969697
      }
    }
  },
  "candidates": [
    {
      "feature_set": "aggregate33",
      "treatment": "class_weight_balanced",
      "ap": "0.41024351517280916",
      "roc_auc": "0.7830011985791786",
      "recall_10": "0.325068870523416",
      "precision_10": "0.49372384937238495",
      "f1_10": "0.39202657807308966",
      "recall_20": "0.5234159779614325",
      "precision_20": "0.39832285115303984",
      "f1_20": "0.45238095238095233",
      "found_20": "190",
      "false_alarms_20": "287"
    },
    {
      "feature_set": "shap15",
      "treatment": "class_weight_balanced",
      "ap": "0.40783331744488033",
      "roc_auc": "0.785279591117955",
      "recall_10": "0.3168044077134986",
      "precision_10": "0.4811715481171548",
      "f1_10": "0.38205980066445183",
      "recall_20": "0.5206611570247934",
      "precision_20": "0.39622641509433965",
      "f1_20": "0.45",
      "found_20": "189",
      "false_alarms_20": "288"
    },
    {
      "feature_set": "engineered40",
      "treatment": "none",
      "ap": "0.406412332738567",
      "roc_auc": "0.788334739411413",
      "recall_10": "0.34710743801652894",
      "precision_10": "0.5271966527196653",
      "f1_10": "0.4186046511627907",
      "recall_20": "0.5261707988980716",
      "precision_20": "0.40041928721174",
      "f1_20": "0.45476190476190476",
      "found_20": "191",
      "false_alarms_20": "286"
    },
    {
      "feature_set": "engineered40",
      "treatment": "class_weight_balanced",
      "ap": "0.4046337763590286",
      "roc_auc": "0.7771366243751143",
      "recall_10": "0.3305785123966942",
      "precision_10": "0.502092050209205",
      "f1_10": "0.39867109634551495",
      "recall_20": "0.5151515151515151",
      "precision_20": "0.3920335429769392",
      "f1_20": "0.4452380952380952",
      "found_20": "187",
      "false_alarms_20": "290"
    },
    {
      "feature_set": "shap15",
      "treatment": "ros",
      "ap": "0.40287150396302596",
      "roc_auc": "0.7817521097996816",
      "recall_10": "0.31129476584022037",
      "precision_10": "0.47280334728033474",
      "f1_10": "0.3754152823920266",
      "recall_20": "0.512396694214876",
      "precision_20": "0.389937106918239",
      "f1_20": "0.4428571428571429",
      "found_20": "186",
      "false_alarms_20": "291"
    },
    {
      "feature_set": "engineered40",
      "treatment": "smote",
      "ap": "0.40085744922414024",
      "roc_auc": "0.7822271730731951",
      "recall_10": "0.31129476584022037",
      "precision_10": "0.47280334728033474",
      "f1_10": "0.3754152823920266",
      "recall_20": "0.5013774104683195",
      "precision_20": "0.38155136268343814",
      "f1_20": "0.4333333333333333",
      "found_20": "182",
      "false_alarms_20": "295"
    },
    {
      "feature_set": "engineered40",
      "treatment": "class_weight_2",
      "ap": "0.39908221327957794",
      "roc_auc": "0.785025677989008",
      "recall_10": "0.3305785123966942",
      "precision_10": "0.502092050209205",
      "f1_10": "0.39867109634551495",
      "recall_20": "0.512396694214876",
      "precision_20": "0.389937106918239",
      "f1_20": "0.4428571428571429",
      "found_20": "186",
      "false_alarms_20": "291"
    },
    {
      "feature_set": "aggregate33",
      "treatment": "smote",
      "ap": "0.39858401871191373",
      "roc_auc": "0.7777550257052914",
      "recall_10": "0.31129476584022037",
      "precision_10": "0.47280334728033474",
      "f1_10": "0.3754152823920266",
      "recall_20": "0.4903581267217631",
      "precision_20": "0.3731656184486373",
      "f1_20": "0.42380952380952386",
      "found_20": "178",
      "false_alarms_20": "299"
    },
    {
      "feature_set": "aggregate33",
      "treatment": "class_weight_2",
      "ap": "0.398448033914567",
      "roc_auc": "0.7817056955718096",
      "recall_10": "0.31955922865013775",
      "precision_10": "0.48535564853556484",
      "f1_10": "0.3853820598006645",
      "recall_20": "0.509641873278237",
      "precision_20": "0.38784067085953877",
      "f1_20": "0.4404761904761905",
      "found_20": "185",
      "false_alarms_20": "292"
    },
    {
      "feature_set": "shap15",
      "treatment": "smote",
      "ap": "0.39754892468834385",
      "roc_auc": "0.7806368032064039",
      "recall_10": "0.3140495867768595",
      "precision_10": "0.4769874476987448",
      "f1_10": "0.37873754152823913",
      "recall_20": "0.5289256198347108",
      "precision_20": "0.4025157232704403",
      "f1_20": "0.45714285714285713",
      "found_20": "192",
      "false_alarms_20": "285"
    },
    {
      "feature_set": "aggregate33",
      "treatment": "ros",
      "ap": "0.39663615407711594",
      "roc_auc": "0.7738507700666454",
      "recall_10": "0.3168044077134986",
      "precision_10": "0.4811715481171548",
      "f1_10": "0.38205980066445183",
      "recall_20": "0.5068870523415978",
      "precision_20": "0.3857442348008386",
      "f1_20": "0.4380952380952381",
      "found_20": "184",
      "false_alarms_20": "293"
    },
    {
      "feature_set": "shap15",
      "treatment": "class_weight_2",
      "ap": "0.39265802375945097",
      "roc_auc": "0.782348669140272",
      "recall_10": "0.31955922865013775",
      "precision_10": "0.48535564853556484",
      "f1_10": "0.3853820598006645",
      "recall_20": "0.5261707988980716",
      "precision_20": "0.40041928721174",
      "f1_20": "0.45476190476190476",
      "found_20": "191",
      "false_alarms_20": "286"
    },
    {
      "feature_set": "aggregate33",
      "treatment": "none",
      "ap": "0.39117392625773045",
      "roc_auc": "0.7816729325874294",
      "recall_10": "0.3278236914600551",
      "precision_10": "0.497907949790795",
      "f1_10": "0.39534883720930236",
      "recall_20": "0.5041322314049587",
      "precision_20": "0.3836477987421384",
      "f1_20": "0.4357142857142857",
      "found_20": "183",
      "false_alarms_20": "294"
    },
    {
      "feature_set": "shap15",
      "treatment": "none",
      "ap": "0.3906990309162189",
      "roc_auc": "0.7849847242585328",
      "recall_10": "0.31955922865013775",
      "precision_10": "0.48535564853556484",
      "f1_10": "0.3853820598006645",
      "recall_20": "0.5041322314049587",
      "precision_20": "0.3836477987421384",
      "f1_20": "0.4357142857142857",
      "found_20": "183",
      "false_alarms_20": "294"
    },
    {
      "feature_set": "engineered40",
      "treatment": "ros",
      "ap": "0.38976029395537065",
      "roc_auc": "0.7724801852200717",
      "recall_10": "0.31955922865013775",
      "precision_10": "0.48535564853556484",
      "f1_10": "0.3853820598006645",
      "recall_20": "0.5289256198347108",
      "precision_20": "0.4025157232704403",
      "f1_20": "0.45714285714285713",
      "found_20": "192",
      "false_alarms_20": "285"
    }
  ],
  "selected_model_shap": [
    {
      "feature": "days_since_last_game",
      "mean_abs_shap": "0.5928562029774813"
    },
    {
      "feature": "games_7d",
      "mean_abs_shap": "0.3467386376162045"
    },
    {
      "feature": "active_days_30d",
      "mean_abs_shap": "0.301032087698979"
    },
    {
      "feature": "mode_switch_rate_20",
      "mean_abs_shap": "0.23510633900833539"
    },
    {
      "feature": "winrate_change_10",
      "mean_abs_shap": "0.1483349406355616"
    },
    {
      "feature": "last_gap",
      "mean_abs_shap": "0.12978968289711423"
    },
    {
      "feature": "avg_cs_per_min_20",
      "mean_abs_shap": "0.12426199369713709"
    },
    {
      "feature": "max_gap_30d",
      "mean_abs_shap": "0.11896574732268807"
    },
    {
      "feature": "avg_vision_per_min_20",
      "mean_abs_shap": "0.10484831200237996"
    },
    {
      "feature": "avg_kda_20",
      "mean_abs_shap": "0.10458723773967125"
    },
    {
      "feature": "unique_modes_30d",
      "mean_abs_shap": "0.10115355950434127"
    },
    {
      "feature": "games_30d",
      "mean_abs_shap": "0.09411225437628004"
    },
    {
      "feature": "games_prev30d",
      "mean_abs_shap": "0.07918510190524136"
    },
    {
      "feature": "winrate_20",
      "mean_abs_shap": "0.0717870035763282"
    },
    {
      "feature": "games_90d",
      "mean_abs_shap": "0.06949981254886796"
    },
    {
      "feature": "avg_gap_30d",
      "mean_abs_shap": "0.06320350274773796"
    },
    {
      "feature": "losing_streak",
      "mean_abs_shap": "0.052701900509332565"
    },
    {
      "feature": "activity_change_30d",
      "mean_abs_shap": "0.05268333361113162"
    },
    {
      "feature": "ranked_flex_ratio_30d",
      "mean_abs_shap": "0.05004858582677706"
    },
    {
      "feature": "avg_deaths_20",
      "mean_abs_shap": "0.049484903929558476"
    },
    {
      "feature": "avg_kills_20",
      "mean_abs_shap": "0.04945904399611136"
    },
    {
      "feature": "avg_game_duration_20",
      "mean_abs_shap": "0.045846928782819714"
    },
    {
      "feature": "avg_damage_per_min_20",
      "mean_abs_shap": "0.0442093589428908"
    },
    {
      "feature": "ranked_solo_ratio_30d",
      "mean_abs_shap": "0.03527160189773928"
    },
    {
      "feature": "top_champion_ratio_20",
      "mean_abs_shap": "0.03496748030353217"
    },
    {
      "feature": "avg_gold_per_min_20",
      "mean_abs_shap": "0.031079158717338205"
    },
    {
      "feature": "other_ratio_30d",
      "mean_abs_shap": "0.02531261749908623"
    },
    {
      "feature": "unique_champions_20",
      "mean_abs_shap": "0.02358637142207919"
    },
    {
      "feature": "avg_assists_20",
      "mean_abs_shap": "0.021488954657827693"
    },
    {
      "feature": "normal_ratio_30d",
      "mean_abs_shap": "0.015155317655065441"
    },
    {
      "feature": "aram_ratio_30d",
      "mean_abs_shap": "0.011640663947815058"
    },
    {
      "feature": "arena_ratio_30d",
      "mean_abs_shap": "0.0"
    },
    {
      "feature": "rotating_ratio_30d",
      "mean_abs_shap": "0.0"
    }
  ],
  "selected_features": [
    "games_7d",
    "games_30d",
    "games_90d",
    "games_prev30d",
    "activity_change_30d",
    "active_days_30d",
    "days_since_last_game",
    "avg_gap_30d",
    "max_gap_30d",
    "last_gap",
    "winrate_20",
    "avg_kda_20",
    "avg_kills_20",
    "avg_deaths_20",
    "avg_assists_20",
    "losing_streak",
    "winrate_change_10",
    "avg_game_duration_20",
    "avg_gold_per_min_20",
    "avg_cs_per_min_20",
    "avg_damage_per_min_20",
    "avg_vision_per_min_20",
    "unique_champions_20",
    "top_champion_ratio_20",
    "unique_modes_30d",
    "mode_switch_rate_20",
    "ranked_solo_ratio_30d",
    "ranked_flex_ratio_30d",
    "normal_ratio_30d",
    "aram_ratio_30d",
    "arena_ratio_30d",
    "rotating_ratio_30d",
    "other_ratio_30d"
  ],
  "feature_engineering": {
    "source_aggregate_features": [
      "games_7d",
      "games_30d",
      "games_90d",
      "games_prev30d",
      "activity_change_30d",
      "active_days_30d",
      "days_since_last_game",
      "avg_gap_30d",
      "max_gap_30d",
      "last_gap",
      "winrate_20",
      "avg_kda_20",
      "avg_kills_20",
      "avg_deaths_20",
      "avg_assists_20",
      "losing_streak",
      "winrate_change_10",
      "avg_game_duration_20",
      "avg_gold_per_min_20",
      "avg_cs_per_min_20",
      "avg_damage_per_min_20",
      "avg_vision_per_min_20",
      "unique_champions_20",
      "top_champion_ratio_20",
      "unique_modes_30d",
      "mode_switch_rate_20",
      "ranked_solo_ratio_30d",
      "ranked_flex_ratio_30d",
      "normal_ratio_30d",
      "aram_ratio_30d",
      "arena_ratio_30d",
      "rotating_ratio_30d",
      "other_ratio_30d"
    ],
    "engineered_features": [
      "recent_activity_ratio",
      "last_week_share",
      "games_per_active_day",
      "last_vs_typical_gap",
      "gap_spread",
      "ranked_share",
      "mode_concentration"
    ],
    "uses_only_pre_cutoff_features": true
  },
  "limitations": [
    "Single cutoff only; no forward-time validation or independent holdout.",
    "Full-data candidate CV metrics are optimistic after selecting the maximum; use nested-selection OOF for the selection procedure.",
    "Nested-selection OOF may use different configurations per outer fold, unlike the saved final model.",
    "SHAP magnitudes are model dependence, not causal effects.",
    "Scores are not probability-calibrated."
  ],
  "boosting_comparison": [
    {
      "model": "CatBoost",
      "users": "2381",
      "churners": "363",
      "pr_auc_ap": "0.41024351517280916",
      "roc_auc": "0.7830011985791786",
      "recall_10": "0.325068870523416",
      "precision_10": "0.49372384937238495",
      "recall_20": "0.5234159779614325",
      "precision_20": "0.39832285115303984",
      "f1_20": "0.45238095238095233",
      "found_20": "190",
      "false_alarms_20": "287"
    },
    {
      "model": "XGBoost",
      "users": "2381",
      "churners": "363",
      "pr_auc_ap": "0.3896234341102675",
      "roc_auc": "0.7695792959780706",
      "recall_10": "0.30303030303030304",
      "precision_10": "0.4602510460251046",
      "recall_20": "0.5179063360881543",
      "precision_20": "0.3941299790356394",
      "f1_20": "0.44761904761904764",
      "found_20": "188",
      "false_alarms_20": "289"
    },
    {
      "model": "LightGBM",
      "users": "2381",
      "churners": "363",
      "pr_auc_ap": "0.39809740622217527",
      "roc_auc": "0.7687602213685645",
      "recall_10": "0.2975206611570248",
      "precision_10": "0.45188284518828453",
      "recall_20": "0.5234159779614325",
      "precision_20": "0.39832285115303984",
      "f1_20": "0.45238095238095233",
      "found_20": "190",
      "false_alarms_20": "287"
    }
  ],
  "boosting_comparison_manifest": {
    "cutoff": "2026-08-01",
    "users": 2381,
    "churners": 363,
    "features": [
      "games_7d",
      "games_30d",
      "games_90d",
      "games_prev30d",
      "activity_change_30d",
      "active_days_30d",
      "days_since_last_game",
      "avg_gap_30d",
      "max_gap_30d",
      "last_gap",
      "winrate_20",
      "avg_kda_20",
      "avg_kills_20",
      "avg_deaths_20",
      "avg_assists_20",
      "losing_streak",
      "winrate_change_10",
      "avg_game_duration_20",
      "avg_gold_per_min_20",
      "avg_cs_per_min_20",
      "avg_damage_per_min_20",
      "avg_vision_per_min_20",
      "unique_champions_20",
      "top_champion_ratio_20",
      "unique_modes_30d",
      "mode_switch_rate_20",
      "ranked_solo_ratio_30d",
      "ranked_flex_ratio_30d",
      "normal_ratio_30d",
      "aram_ratio_30d",
      "arena_ratio_30d",
      "rotating_ratio_30d",
      "other_ratio_30d"
    ],
    "feature_count": 33,
    "models": [
      "CatBoost",
      "XGBoost",
      "LightGBM"
    ],
    "folds": 5,
    "seed": 42,
    "split": "Same stratified 5-fold split for every model; no time holdout.",
    "imputation": "Median fitted on each training fold only.",
    "imbalance": "Positive-to-negative inverse prevalence weight computed on each training fold.",
    "hyperparameters": "Fixed modest-depth configurations; not equally tuned or optimized.",
    "limitations": [
      "One cutoff; no independent future-date test.",
      "Comparing and choosing the highest OOF row on the same folds is exploratory.",
      "Different library weighting implementations and fixed parameter choices remain a comparison limitation.",
      "Class-weighted output scores are not calibrated probabilities."
    ]
  }
}

const nested = details.nested_selection_oof.all_core

export const modelMetricsFallback: ModelMetricsResponse = {
  model_status: 'ready',
  model_version: details.model_version,
  metrics: {
    pr_auc_ap: nested.pr_auc_ap,
    roc_auc: nested.roc_auc,
    recall_20: nested.top_20pct.recall,
    precision_20: nested.top_20pct.precision,
    f1_20: nested.top_20pct.f1,
  },
  message: '로컬 모델 평가 스냅샷을 사용 중입니다.',
  details,
}
