"""Repositorio de escritura para las colecciones Firestore del proyecto."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any


DATASET_COLLECTION = "datasets"
MODEL_RESULTS_COLLECTION = "model_results"
CROSS_VALIDATION_COLLECTION = "cross_validation"
MODEL_CONFIG_COLLECTION = "model_config"
PREDICTIONS_COLLECTION = "predictions"
PIPELINE_LOGS_COLLECTION = "pipeline_logs"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def guardar_dataset_metadata(
    db: Any,
    dataset_id: str,
    dataset_metadata: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Guarda metadata del dataset procesado."""
    logger.info("Subiendo metadata del dataset: %s", dataset_id)
    db.collection(DATASET_COLLECTION).document(dataset_id).set(
        dataset_metadata,
        merge=True,
    )
    logger.info("Metadata subida en %s/%s", DATASET_COLLECTION, dataset_id)


def guardar_model_config(
    db: Any,
    document_id: str,
    model_config: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Guarda configuracion y parametrizacion del modelo y del preprocesamiento."""
    logger.info("Subiendo configuracion del modelo: %s", document_id)
    db.collection(MODEL_CONFIG_COLLECTION).document(document_id).set(
        model_config,
        merge=True,
    )
    logger.info(
        "Configuracion subida en %s/%s",
        MODEL_CONFIG_COLLECTION,
        document_id,
    )


def guardar_metricas_modelo(
    db: Any,
    document_id: str,
    model_metrics: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Guarda metricas y resultados del modelo ganador."""
    logger.info("Subiendo metricas del modelo: %s", document_id)
    db.collection(MODEL_RESULTS_COLLECTION).document(document_id).set(
        model_metrics,
        merge=True,
    )
    logger.info("Metricas subidas en %s/%s", MODEL_RESULTS_COLLECTION, document_id)


def guardar_cross_validation(
    db: Any,
    document_id: str,
    cross_validation_payload: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Guarda resultados de validacion cruzada del experimento."""
    logger.info("Subiendo resultados de Cross Validation: %s", document_id)
    db.collection(CROSS_VALIDATION_COLLECTION).document(document_id).set(
        cross_validation_payload,
        merge=True,
    )
    logger.info(
        "Cross Validation subida en %s/%s",
        CROSS_VALIDATION_COLLECTION,
        document_id,
    )


def guardar_predicciones(
    db: Any,
    document_id: str,
    predictions_payload: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Guarda predicciones o resumen auditable de predicciones disponibles."""
    logger.info("Subiendo predicciones/resumen: %s", document_id)
    db.collection(PREDICTIONS_COLLECTION).document(document_id).set(
        predictions_payload,
        merge=True,
    )
    logger.info(
        "Predicciones/resumen subido en %s/%s",
        PREDICTIONS_COLLECTION,
        document_id,
    )


def guardar_modelo_seleccionado(
    db: Any,
    selected_model_payload: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Guarda un resumen explicito del modelo seleccionado para produccion."""
    document_id = "modelo_ganador"
    logger.info("Subiendo modelo seleccionado: %s", selected_model_payload.get("model_name"))
    db.collection(MODEL_RESULTS_COLLECTION).document(document_id).set(
        selected_model_payload,
        merge=True,
    )
    logger.info("Modelo seleccionado guardado en %s/%s", MODEL_RESULTS_COLLECTION, document_id)


def guardar_pipeline_log(
    db: Any,
    event_payload: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Guarda eventos de auditoria de la carga en Firestore."""
    event = {
        **event_payload,
        "created_at": event_payload.get("created_at", _utc_now_iso()),
    }
    logger.info("Subiendo evento de log a Firestore: %s", event.get("event"))
    logs_doc = db.collection(PIPELINE_LOGS_COLLECTION).document("eventos")
    logs_doc.set({"last_event": event, "updated_at": _utc_now_iso()}, merge=True)
    logs_doc.collection("items").add(event)
    logger.info("Evento registrado en %s/eventos/items", PIPELINE_LOGS_COLLECTION)
