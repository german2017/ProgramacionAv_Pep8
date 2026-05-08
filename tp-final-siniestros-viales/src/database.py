"""Utilidades para almacenar datos y resultados en MongoDB."""

from typing import Iterable

from pymongo import MongoClient


def get_mongo_client(uri: str) -> MongoClient:
    """Crea un cliente de MongoDB."""
    # TODO: Leer URI desde variables de entorno.
    return MongoClient(uri)


def insert_documents(client: MongoClient, database: str, collection: str, documents: Iterable[dict]) -> None:
    """Inserta documentos en una coleccion de MongoDB."""
    # TODO: Agregar validaciones, manejo de errores y logs.
    client[database][collection].insert_many(list(documents))
