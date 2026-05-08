"""Funciones para cargar y guardar datasets."""

from pathlib import Path

import pandas as pd


def load_raw_data(file_path: Path) -> pd.DataFrame:
    """Carga el dataset original desde disco."""
    # TODO: Validar extension y columnas esperadas del dataset.
    return pd.read_csv(file_path)


def save_processed_data(data: pd.DataFrame, file_path: Path) -> None:
    """Guarda un dataset procesado en formato CSV."""
    # TODO: Evaluar uso de Parquet si el dataset es grande.
    data.to_csv(file_path, index=False)
