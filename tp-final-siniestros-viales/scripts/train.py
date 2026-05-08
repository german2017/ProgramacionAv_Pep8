"""Script principal de entrenamiento."""

from src.config import RAW_DATA_FILE
from src.data_loader import load_raw_data
from src.feature_engineering import build_features
from src.preprocessing import clean_data


def main() -> None:
    """Ejecuta el pipeline inicial de carga, limpieza y feature engineering."""
    # TODO: Definir variable objetivo y columnas predictoras.
    # TODO: Entrenar dos modelos y guardar metricas/resultados.
    data = load_raw_data(RAW_DATA_FILE)
    clean = clean_data(data)
    features = build_features(clean)
    print(f"Dataset preparado con shape: {features.shape}")


if __name__ == "__main__":
    main()
