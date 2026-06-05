"""Sube metadata y resultados de modelado a Firebase Firestore.

Ejecucion real:
    python scripts/upload_results_firebase.py

Validacion sin escritura:
    python scripts/upload_results_firebase.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.firebase_client import get_firestore_client, get_pipeline_logger, load_env_file
from src.firestore_repository import (
    guardar_dataset_metadata,
    guardar_log_evento,
    guardar_metricas_modelo,
    guardar_modelo_seleccionado,
    guardar_resultado_cross_validation,
)


DATASET_ID = "siniestros_limpio_enriquecido"
DATASET_VERSION = "v1_enriquecido"
MODEL_RESULTS_DOC_ID = "modelo_ganador"
CROSS_VALIDATION_DOC_ID = "experimento_actual"

DATA_FILE = PROJECT_ROOT / "data" / "processed" / "siniestros_limpio_enriquecido.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"

MODEL_METRICS_FILE = OUTPUTS_DIR / "model_metrics.json"
MODEL_COMPARISON_FILE = OUTPUTS_DIR / "model_comparison.json"
CROSS_VALIDATION_FILE = OUTPUTS_DIR / "cross_validation_results.json"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path, logger: logging.Logger) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el archivo requerido: {path}")

    logger.info("Carga de archivo JSON: %s", path.relative_to(PROJECT_ROOT))
    return json.loads(path.read_text(encoding="utf-8"))


def read_dataset_metadata(path: Path, created_at: str, logger: logging.Logger) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el dataset procesado: {path}")

    logger.info("Carga de metadata del dataset: %s", path.relative_to(PROJECT_ROOT))
    df = pd.read_csv(path)
    return {
        "nombre": DATASET_ID,
        "fecha_carga": created_at,
        "cantidad_filas": int(df.shape[0]),
        "cantidad_columnas": int(df.shape[1]),
        "columnas": list(df.columns),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "fuente": str(path.relative_to(PROJECT_ROOT)),
        "version_dataset": DATASET_VERSION,
    }


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
        "target": cross_validation["target"],
        "accuracy": selected_holdout_metrics.get("accuracy"),
        "precision": selected_holdout_metrics.get("precision"),
        "recall": selected_holdout_metrics.get("recall"),
        "f1": selected_holdout_metrics.get("f1"),
        "f1_mean": selected_cv_metrics.get("f1_mean"),
        "f1_std": selected_cv_metrics.get("f1_std"),
        "cv_folds": cross_validation["cv_strategy"]["n_splits"],
        "selected_model": True,
        "created_at": created_at,
        "baseline": {
            "model_name": baseline_metrics.get("model"),
            "metrics": baseline_metrics.get("metrics", {}),
        },
        "comparison_table": model_comparison.get("comparison_table", []),
        "selection_criteria": cross_validation.get("selection_criteria", []),
    }


def build_cross_validation_payload(
    cross_validation: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    return {
        "experiment_id": CROSS_VALIDATION_DOC_ID,
        "target": cross_validation["target"],
        "best_model": cross_validation["best_model"],
        "best_model_metrics": cross_validation["best_model_metrics"],
        "cv_strategy": cross_validation["cv_strategy"],
        "selection_criteria": cross_validation["selection_criteria"],
        "features": cross_validation["features"],
        "data": cross_validation["data"],
        "comparison_table": cross_validation["comparison_table"],
        "fold_scores": cross_validation["fold_scores"],
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


def build_payloads(logger: logging.Logger) -> dict[str, Any]:
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
    cross_validation_results = build_cross_validation_payload(cross_validation, created_at)
    selected_model = build_selected_model_payload(
        model_metrics,
        cross_validation,
        created_at,
    )

    return {
        "dataset_metadata": dataset_metadata,
        "model_metrics": model_metrics,
        "cross_validation_results": cross_validation_results,
        "selected_model": selected_model,
    }


def upload_payloads(payloads: dict[str, Any], logger: logging.Logger) -> None:
    logger.info("Inicio de conexion a Firestore")
    db = get_firestore_client()
    logger.info("Conexion exitosa a Firestore")

    guardar_log_evento(
        db,
        {
            "event": "inicio_carga_firestore",
            "status": "INFO",
            "message": "Inicio de persistencia de resultados del TP final.",
        },
        logger,
    )
    guardar_dataset_metadata(db, DATASET_ID, payloads["dataset_metadata"], logger)
    guardar_metricas_modelo(db, MODEL_RESULTS_DOC_ID, payloads["model_metrics"], logger)
    guardar_resultado_cross_validation(
        db,
        CROSS_VALIDATION_DOC_ID,
        payloads["cross_validation_results"],
        logger,
    )
    guardar_modelo_seleccionado(db, payloads["selected_model"], logger)
    guardar_log_evento(
        db,
        {
            "event": "fin_carga_firestore",
            "status": "INFO",
            "message": "Persistencia completada correctamente.",
            "dataset_id": DATASET_ID,
            "model_results_doc": MODEL_RESULTS_DOC_ID,
            "cross_validation_doc": CROSS_VALIDATION_DOC_ID,
        },
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
            "Payloads generados: dataset_metadata, model_metrics, cross_validation_results, selected_model"
        )

        if args.dry_run:
            logger.info("Dry run solicitado: no se escribira en Firestore")
            print("Dry run correcto. No se escribio en Firestore.")
            print(f"datasets/{DATASET_ID}")
            print(f"model_results/{MODEL_RESULTS_DOC_ID}")
            print(f"cross_validation/{CROSS_VALIDATION_DOC_ID}")
            print("logs/eventos/items")
            return 0

        upload_payloads(payloads, logger)
        logger.info("Proceso de persistencia Firebase/Firestore finalizado correctamente")
        return 0
    except Exception:
        logger.exception("Error durante el proceso de persistencia Firebase/Firestore")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
