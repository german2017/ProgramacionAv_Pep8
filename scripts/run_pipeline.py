"""Ejecuta el pipeline completo de notebooks con Papermill."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import papermill as pm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
EXECUTED_NOTEBOOKS_DIR = PROJECT_ROOT / "outputs" / "executed_notebooks"
REPORT_FILE = PROJECT_ROOT / "outputs" / "pipeline_execution_report.json"
LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"
IPYTHON_DIR = PROJECT_ROOT / ".ipython_papermill"
DASHBOARD_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "dashboards"

PIPELINE_NOTEBOOKS = [
    ("01_eda.ipynb", "01_eda.ipynb"),
    ("02_preprocessing.ipynb", "02_preprocessing.ipynb"),
    ("03_analisis.ipynb", "03_analisis.ipynb"),
    ("04_modelado.ipynb", "04_modelado.ipynb"),
    ("05_entrenamiento.ipynb", "05_entrenamiento.ipynb"),
    ("06_comparacion_modelos.ipynb", "06_comparacion_modelos.ipynb"),
    ("07_cross_val.ipynb", "07_cross_validation.ipynb"),
    ("08_firebase.ipynb", "08_firebase.ipynb"),
    ("09_dashboard_storytelling.ipynb", "09_dashboard_storytelling.ipynb"),
]


def configure_logging() -> logging.Logger:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("papermill_pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8-sig")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def ensure_directories() -> None:
    EXECUTED_NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    IPYTHON_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("IPYTHONDIR", str(IPYTHON_DIR))


def get_kernel_name() -> str | None:
    return os.getenv("PIPELINE_KERNEL_NAME") or None


def write_report(report: dict[str, Any]) -> None:
    REPORT_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def remove_plotly_fallbacks(logger: logging.Logger) -> int:
    if not DASHBOARD_OUTPUT_DIR.exists():
        return 0

    removed = 0
    for path in DASHBOARD_OUTPUT_DIR.glob("plotly_render_fallback_*.html"):
        path.unlink()
        removed += 1

    if removed:
        logger.info("HTML temporales de Plotly removidos: %s", removed)

    return removed


def execute_notebook(
    requested_name: str,
    actual_name: str,
    kernel_name: str | None,
    logger: logging.Logger,
) -> dict[str, Any]:
    input_path = NOTEBOOKS_DIR / actual_name
    output_path = EXECUTED_NOTEBOOKS_DIR / requested_name

    if not input_path.exists():
        raise FileNotFoundError(f"No existe el notebook requerido: {input_path}")

    if requested_name != actual_name:
        logger.warning(
            "Notebook solicitado %s no existe con ese nombre; se ejecuta %s",
            requested_name,
            actual_name,
        )

    started_at = datetime.now()
    start = time.perf_counter()
    logger.info("Inicio notebook: %s", actual_name)

    pm.execute_notebook(
        input_path=str(input_path),
        output_path=str(output_path),
        kernel_name=kernel_name,
        progress_bar=False,
        cwd=str(PROJECT_ROOT),
    )

    duration_seconds = round(time.perf_counter() - start, 3)
    finished_at = datetime.now()
    logger.info(
        "Fin notebook: %s | duracion %.3f segundos | salida %s",
        actual_name,
        duration_seconds,
        output_path,
    )

    return {
        "notebook": requested_name,
        "input_notebook": str(input_path.relative_to(PROJECT_ROOT)),
        "executed_notebook": str(output_path.relative_to(PROJECT_ROOT)),
        "estado": "ok",
        "inicio": started_at.isoformat(timespec="seconds"),
        "fin": finished_at.isoformat(timespec="seconds"),
        "duracion_segundos": duration_seconds,
        "error": None,
    }


def main() -> int:
    ensure_directories()
    logger = configure_logging()
    kernel_name = get_kernel_name()
    started_at = datetime.now()
    total_start = time.perf_counter()

    report: dict[str, Any] = {
        "fecha": started_at.isoformat(timespec="seconds"),
        "estado_final": "running",
        "duracion_total_segundos": None,
        "notebooks_ejecutados": [],
        "errores": [],
    }
    write_report(report)

    logger.info("Inicio del pipeline automatizado con Papermill")
    logger.info("Directorio del proyecto: %s", PROJECT_ROOT)
    logger.info("Directorio de notebooks ejecutados: %s", EXECUTED_NOTEBOOKS_DIR)
    logger.info("Kernel configurado: %s", kernel_name or "metadata del notebook")

    try:
        for requested_name, actual_name in PIPELINE_NOTEBOOKS:
            result = execute_notebook(
                requested_name=requested_name,
                actual_name=actual_name,
                kernel_name=kernel_name,
                logger=logger,
            )
            report["notebooks_ejecutados"].append(result)
            write_report(report)

        remove_plotly_fallbacks(logger)
        report["estado_final"] = "ok"
        logger.info("Pipeline automatizado finalizado correctamente")
        exit_code = 0
    except Exception as exc:
        duration_seconds = round(time.perf_counter() - total_start, 3)
        error_payload = {
            "tipo": exc.__class__.__name__,
            "mensaje": str(exc),
            "duracion_hasta_error_segundos": duration_seconds,
        }
        report["errores"].append(error_payload)
        report["estado_final"] = "error"
        logger.exception("Error durante el pipeline automatizado")
        exit_code = 1
    finally:
        finished_at = datetime.now()
        report["fin"] = finished_at.isoformat(timespec="seconds")
        report["duracion_total_segundos"] = round(time.perf_counter() - total_start, 3)
        write_report(report)
        logger.info(
            "Fin del pipeline automatizado | estado=%s | duracion=%.3f segundos",
            report["estado_final"],
            report["duracion_total_segundos"],
        )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
