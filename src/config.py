"""Configuracion central del proyecto."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODELS_DIR = OUTPUTS_DIR / "models"
METRICS_DIR = OUTPUTS_DIR / "metrics"
FIGURES_DIR = OUTPUTS_DIR / "figures"

# TODO: Definir nombre del archivo fuente cuando se confirme el dataset.
RAW_DATA_FILE = RAW_DATA_DIR / "siniestros_viales.csv"

# TODO: Mover credenciales reales a un archivo .env.
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "tp_siniestros_viales"
