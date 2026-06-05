"""Cliente y utilidades para persistir resultados en Firebase Firestore."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any


LOGGER_NAME = "firebase_upload"


def load_env_file(env_path: str | Path = ".env") -> None:
    """Carga variables simples desde .env sin depender de python-dotenv."""
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_pipeline_logger(log_file: str | Path) -> logging.Logger:
    """Devuelve un logger que escribe en logs/pipeline.log."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8-sig")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    logger.addHandler(stream_handler)
    return logger


def _resolve_credentials_path() -> Path | None:
    credentials = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not credentials:
        return None
    return Path(credentials).expanduser().resolve()


def get_firestore_client(project_id: str | None = None) -> Any:
    """Inicializa Firebase Admin y devuelve un cliente Firestore."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:
        raise ImportError(
            "Falta instalar firebase-admin. Ejecute: pip install firebase-admin"
        ) from exc

    credentials_path = _resolve_credentials_path()
    firebase_project_id = project_id or os.getenv("FIREBASE_PROJECT_ID")

    if not credentials_path:
        raise ValueError(
            "No se encontro la variable de entorno FIREBASE_CREDENTIALS_PATH. "
            "Configurela con la ruta local al JSON de service account, por ejemplo: "
            "FIREBASE_CREDENTIALS_PATH=<ruta-local-al-service-account.json>"
        )
    if not credentials_path.exists():
        raise FileNotFoundError(f"No existe el archivo de credenciales: {credentials_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(credentials_path)
        options = {"projectId": firebase_project_id} if firebase_project_id else None
        firebase_admin.initialize_app(cred, options=options)

    return firestore.client()

