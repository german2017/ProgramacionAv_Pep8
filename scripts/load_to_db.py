"""Script para cargar datos o resultados en MongoDB."""

from src.config import MONGO_DATABASE, MONGO_URI
from src.database import get_mongo_client


def main() -> None:
    """Ejecuta la carga inicial hacia MongoDB."""
    # TODO: Cargar datasets procesados, metricas o predicciones segun corresponda.
    # TODO: Convertir DataFrames a documentos antes de insertarlos.
    client = get_mongo_client(MONGO_URI)
    print(f"Cliente MongoDB listo para base: {MONGO_DATABASE}")
    client.close()


if __name__ == "__main__":
    main()
