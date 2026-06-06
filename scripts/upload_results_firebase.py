"""Sube metadata y resultados de modelado a Firebase Firestore.

Ejecucion real:
    python scripts/upload_results_firebase.py

Validacion sin escritura:
    python scripts/upload_results_firebase.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import sys
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.firebase_client import get_firestore_client, get_pipeline_logger, load_env_file
from src.firestore_repository import (
    guardar_cross_validation,
    guardar_dataset_metadata,
    guardar_metricas_modelo,
    guardar_model_config,
    guardar_modelo_seleccionado,
    guardar_pipeline_log,
    guardar_predicciones,
)


DATASET_ID = "siniestros_limpio_enriquecido"
DATASET_VERSION = "v1_enriquecido"
MODEL_RESULTS_DOC_ID = "modelo_ganador"
CROSS_VALIDATION_DOC_ID = "resultados_validacion_cruzada"
MODEL_CONFIG_DOC_ID = "configuracion_modelo_ganador"
PREDICTIONS_DOC_ID = "predicciones_experimento_actual"
DATASET_SAMPLE_ROWS = 200

DATA_FILE = PROJECT_ROOT / "data" / "processed" / "siniestros_limpio_enriquecido.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"

MODEL_METRICS_FILE = OUTPUTS_DIR / "model_metrics.json"
MODEL_COMPARISON_FILE = OUTPUTS_DIR / "model_comparison.json"
CROSS_VALIDATION_FILE = OUTPUTS_DIR / "cross_validation_results.json"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_null_logger() -> logging.Logger:
    logger = logging.getLogger("firebase_upload.null")
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


def read_json(path: Path, logger: logging.Logger) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el archivo requerido: {path}")

    logger.info("Carga de archivo JSON: %s", path.relative_to(PROJECT_ROOT))
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sanitize_for_firestore(value: Any) -> Any:
    """Convierte valores de pandas/numpy no serializables a tipos compatibles."""
    if isinstance(value, dict):
        return {str(key): sanitize_for_firestore(item) for key, item in value.items()}
    if isinstance(value, list):
        sanitized = [sanitize_for_firestore(item) for item in value]
        if any(isinstance(item, list) for item in sanitized):
            return [
                {"index": index, "values": item} if isinstance(item, list) else item
                for index, item in enumerate(sanitized)
            ]
        return sanitized
    if pd.isna(value):
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if hasattr(value, "item"):
        return sanitize_for_firestore(value.item())
    return value


def matrix_to_records(matrix: list[list[Any]]) -> list[dict[str, Any]]:
    return [
        {"row": row_index, "values": sanitize_for_firestore(row)}
        for row_index, row in enumerate(matrix)
    ]


def read_dataset_metadata(path: Path, created_at: str, logger: logging.Logger) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el dataset procesado: {path}")

    logger.info("Carga de metadata del dataset: %s", path.relative_to(PROJECT_ROOT))
    df = pd.read_csv(path)
    sample = df.head(DATASET_SAMPLE_ROWS).where(pd.notna(df.head(DATASET_SAMPLE_ROWS)), None)
    return sanitize_for_firestore({
        "nombre": DATASET_ID,
        "fecha_carga": created_at,
        "fecha_ejecucion": created_at,
        "cantidad_filas": int(df.shape[0]),
        "cantidad_columnas": int(df.shape[1]),
        "columnas": list(df.columns),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "nulos_por_columna": {
            column: int(count) for column, count in df.isna().sum().items()
        },
        "fuente": str(path.relative_to(PROJECT_ROOT)),
        "ruta_local_archivo_procesado": str(path),
        "dataset_hash_sha256": file_sha256(path),
        "version_dataset": DATASET_VERSION,
        "muestra_tipo": "primeras_200_filas",
        "muestra_cantidad_filas": int(sample.shape[0]),
        "muestra_registros": sample.to_dict(orient="records"),
    })


def build_model_metrics_payload(
    baseline_metrics: dict[str, Any],
    model_comparison: dict[str, Any],
    cross_validation: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    selected_model = cross_validation["best_model"]
    selected_cv_metrics = cross_validation["best_model_metrics"]
    selected_holdout_metrics = model_comparison.get("best_model_metrics", {})

    return {
        "experiment_id": MODEL_RESULTS_DOC_ID,
        "model_name": selected_model,
        "modelo_seleccionado": selected_model,
        "target": cross_validation["target"],
        "accuracy": selected_holdout_metrics.get("accuracy"),
        "precision": selected_holdout_metrics.get("precision"),
        "recall": selected_holdout_metrics.get("recall"),
        "f1": selected_holdout_metrics.get("f1"),
        "f1_mean": selected_cv_metrics.get("f1_mean"),
        "f1_std": selected_cv_metrics.get("f1_std"),
        "cv_folds": cross_validation["cv_strategy"]["n_splits"],
        "selected_model": True,
        "features": cross_validation["features"],
        "fecha_ejecucion": created_at,
        "created_at": created_at,
        "baseline": {
            "model_name": baseline_metrics.get("model"),
            "metrics": baseline_metrics.get("metrics", {}),
        },
        "comparison_table": model_comparison.get("comparison_table", []),
        "cross_validation": {
            "best_model_metrics": selected_cv_metrics,
            "cv_strategy": cross_validation["cv_strategy"],
            "fold_scores": cross_validation.get("fold_scores", {}),
        },
        "selection_criteria": cross_validation.get("selection_criteria", []),
    }


def build_model_config_payload(
    baseline_metrics: dict[str, Any],
    model_comparison: dict[str, Any],
    cross_validation: dict[str, Any],
    dataset_metadata: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    features = cross_validation["features"]
    return {
        "experiment_id": MODEL_CONFIG_DOC_ID,
        "dataset_id": DATASET_ID,
        "dataset_version": dataset_metadata["version_dataset"],
        "dataset_hash_sha256": dataset_metadata["dataset_hash_sha256"],
        "target": cross_validation["target"],
        "modelo_seleccionado": cross_validation["best_model"],
        "modelos_evaluados": [
            row.get("modelo") for row in model_comparison.get("comparison_table", [])
        ],
        "baseline_model": baseline_metrics.get("model"),
        "model_parameters": {
            "class_weight": "balanced",
            "random_state": cross_validation["cv_strategy"].get("random_state"),
            "selection_metric": "f1_mean",
            "selection_criteria": cross_validation.get("selection_criteria", []),
        },
        "cv_strategy": cross_validation["cv_strategy"],
        "features": cross_validation["features"],
        "features_usadas": features.get("numeric", []) + features.get("categorical", []),
        "features_numericas": features.get("numeric", []),
        "features_categoricas": features.get("categorical", []),
        "features_excluidas": features.get("excluded_leakage_or_target", []),
        "preprocessing_config": {
            "categorical_encoder": "OneHotEncoder(handle_unknown='ignore')",
            "numeric_transformer": "passthrough",
            "missing_categorical": "fillna('SIN_DATO')",
            "leakage_exclusions": features.get("excluded_leakage_or_target", []),
        },
        "fecha_ejecucion": created_at,
        "created_at": created_at,
    }


def build_predictions_payload(
    model_comparison: dict[str, Any],
    cross_validation: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    selected_model = cross_validation["best_model"]
    selected_model_results = model_comparison.get("models", {}).get(selected_model, {})
    return {
        "experiment_id": PREDICTIONS_DOC_ID,
        "dataset_id": DATASET_ID,
        "target": cross_validation["target"],
        "modelo_seleccionado": selected_model,
        "tipo": "resumen_predicciones_holdout",
        "predicciones_fila_a_fila_disponibles": False,
        "nota": (
            "No se reentrenan modelos ni se generan inferencias nuevas en esta carga. "
            "Se persiste el resumen de predicciones disponible en los artefactos existentes."
        ),
        "prediction_distribution": selected_model_results.get("prediction_distribution", {}),
        "confusion_matrix": matrix_to_records(
            selected_model_results.get("confusion_matrix", [])
        ),
        "classification_report": selected_model_results.get("classification_report", {}),
        "models_prediction_distribution": {
            model_name: model_payload.get("prediction_distribution", {})
            for model_name, model_payload in model_comparison.get("models", {}).items()
        },
        "test_rows": model_comparison.get("data", {}).get("test_rows"),
        "positive_rate_test": model_comparison.get("data", {}).get("test_positive_rate"),
        "fecha_ejecucion": created_at,
        "created_at": created_at,
    }


def build_selected_model_payload(
    model_metrics: dict[str, Any],
    cross_validation: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    features = cross_validation["features"]
    return {
        "experiment_id": "modelo_seleccionado_produccion",
        "model_name": model_metrics["model_name"],
        "target": model_metrics["target"],
        "selected_model": True,
        "selection_metric": "f1_mean",
        "metrics": {
            "accuracy": model_metrics.get("accuracy"),
            "precision": model_metrics.get("precision"),
            "recall": model_metrics.get("recall"),
            "f1": model_metrics.get("f1"),
            "f1_mean": model_metrics.get("f1_mean"),
            "f1_std": model_metrics.get("f1_std"),
        },
        "features": features,
        "excluded_features": features.get("excluded_leakage_or_target", []),
        "preprocessing": {
            "categorical": "OneHotEncoder(handle_unknown='ignore')",
            "numeric": "passthrough",
            "missing_categorical": "fillna('SIN_DATO')",
        },
        "class_weight": "balanced",
        "random_state": cross_validation["cv_strategy"]["random_state"],
        "notes": (
            "Modelo seleccionado por mayor F1 promedio y menor desviacion "
            "estandar en Cross Validation."
        ),
        "created_at": created_at,
    }


def build_firestore_payloads(logger: logging.Logger | None = None) -> dict[str, Any]:
    """Construye payloads locales para Firestore sin abrir conexion a Firebase."""
    logger = logger or get_null_logger()
    created_at = utc_now_iso()
    baseline_metrics = read_json(MODEL_METRICS_FILE, logger)
    model_comparison = read_json(MODEL_COMPARISON_FILE, logger)
    cross_validation = read_json(CROSS_VALIDATION_FILE, logger)
    dataset_metadata = read_dataset_metadata(DATA_FILE, created_at, logger)
    model_metrics = build_model_metrics_payload(
        baseline_metrics,
        model_comparison,
        cross_validation,
        created_at,
    )
    model_config = build_model_config_payload(
        baseline_metrics,
        model_comparison,
        cross_validation,
        dataset_metadata,
        created_at,
    )
    predictions = build_predictions_payload(model_comparison, cross_validation, created_at)
    selected_model = build_selected_model_payload(
        model_metrics,
        cross_validation,
        created_at,
    )
    logs = {
        "inicio_carga_firestore": {
            "event": "inicio_carga_firestore",
            "status": "INFO",
            "message": "Inicio de persistencia de resultados del TP final.",
            "created_at": created_at,
        },
        "fin_carga_firestore": {
            "event": "fin_carga_firestore",
            "status": "INFO",
            "message": "Persistencia completada correctamente.",
            "dataset_id": DATASET_ID,
            "model_results_doc": MODEL_RESULTS_DOC_ID,
            "cross_validation_doc": CROSS_VALIDATION_DOC_ID,
            "model_config_doc": MODEL_CONFIG_DOC_ID,
            "predictions_doc": PREDICTIONS_DOC_ID,
            "created_at": created_at,
        },
    }

    return {
        "datasets": {DATASET_ID: dataset_metadata},
        "model_results": {
            MODEL_RESULTS_DOC_ID: model_metrics,
            "modelo_seleccionado_produccion": selected_model,
        },
        "cross_validation": {
            CROSS_VALIDATION_DOC_ID: sanitize_for_firestore(
                {
                    **deepcopy(cross_validation),
                    "dataset_id": DATASET_ID,
                    "created_at": created_at,
                }
            )
        },
        "model_config": {MODEL_CONFIG_DOC_ID: model_config},
        "logs": logs,
        "predictions": {PREDICTIONS_DOC_ID: predictions},
        # Claves de compatibilidad para el script y notebooks previos.
        "dataset_metadata": dataset_metadata,
        "model_metrics": model_metrics,
        "model_config_payload": model_config,
        "predictions_payload": predictions,
        "selected_model": selected_model,
    }


def build_payloads(logger: logging.Logger | None = None) -> dict[str, Any]:
    return build_firestore_payloads(logger)


def upload_payloads(
    payloads: dict[str, Any],
    logger: logging.Logger | None = None,
) -> None:
    logger = logger or get_null_logger()
    dataset_metadata = payloads.get("dataset_metadata")
    if dataset_metadata is None:
        dataset_metadata = payloads["datasets"][DATASET_ID]

    model_metrics = payloads.get("model_metrics")
    if model_metrics is None:
        model_metrics = payloads["model_results"][MODEL_RESULTS_DOC_ID]

    model_config = payloads.get("model_config_payload")
    if model_config is None:
        model_config = payloads["model_config"][MODEL_CONFIG_DOC_ID]

    predictions = payloads.get("predictions_payload")
    if predictions is None:
        predictions = payloads["predictions"][PREDICTIONS_DOC_ID]

    cross_validation = payloads["cross_validation"][CROSS_VALIDATION_DOC_ID]
    selected_model = payloads["selected_model"]
    logs = payloads.get("logs", {})

    logger.info("Inicio de conexion a Firestore")
    db = get_firestore_client()
    logger.info("Conexion exitosa a Firestore")

    guardar_pipeline_log(
        db,
        logs.get(
            "inicio_carga_firestore",
            {
                "event": "inicio_carga_firestore",
                "status": "INFO",
                "message": "Inicio de persistencia de resultados del TP final.",
            },
        ),
        logger,
    )
    guardar_dataset_metadata(db, DATASET_ID, dataset_metadata, logger)
    guardar_metricas_modelo(db, MODEL_RESULTS_DOC_ID, model_metrics, logger)
    guardar_cross_validation(
        db,
        CROSS_VALIDATION_DOC_ID,
        cross_validation,
        logger,
    )
    guardar_model_config(
        db,
        MODEL_CONFIG_DOC_ID,
        model_config,
        logger,
    )
    guardar_predicciones(db, PREDICTIONS_DOC_ID, predictions, logger)
    guardar_modelo_seleccionado(db, selected_model, logger)
    guardar_pipeline_log(
        db,
        logs.get(
            "fin_carga_firestore",
            {
                "event": "fin_carga_firestore",
                "status": "INFO",
                "message": "Persistencia completada correctamente.",
                "dataset_id": DATASET_ID,
                "model_results_doc": MODEL_RESULTS_DOC_ID,
                "cross_validation_doc": CROSS_VALIDATION_DOC_ID,
                "model_config_doc": MODEL_CONFIG_DOC_ID,
                "predictions_doc": PREDICTIONS_DOC_ID,
            },
        ),
        logger,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sube resultados de modelado a Firebase Firestore."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida archivos y payloads sin escribir en Firestore.",
    )
    parser.add_argument(
        "--env-file",
        default=str(PROJECT_ROOT / ".env"),
        help="Ruta opcional al archivo .env local.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = get_pipeline_logger(LOG_FILE)
    logger.info("Inicio del proceso de persistencia Firebase/Firestore")

    try:
        load_env_file(args.env_file)
        payloads = build_payloads(logger)
        logger.info(
            "Payloads generados: datasets, model_results, cross_validation, model_config, logs"
        )

        if args.dry_run:
            logger.info("Dry run solicitado: no se escribira en Firestore")
            print("Dry run correcto. No se escribio en Firestore.")
            print(f"datasets/{DATASET_ID}")
            print(f"model_results/{MODEL_RESULTS_DOC_ID}")
            print(f"cross_validation/{CROSS_VALIDATION_DOC_ID}")
            print(f"model_config/{MODEL_CONFIG_DOC_ID}")
            print(f"predictions/{PREDICTIONS_DOC_ID}")
            print("pipeline_logs/eventos/items")
            return 0

        upload_payloads(payloads, logger)
        logger.info("Proceso de persistencia Firebase/Firestore finalizado correctamente")
        return 0
    except Exception:
        logger.exception("Error durante el proceso de persistencia Firebase/Firestore")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
