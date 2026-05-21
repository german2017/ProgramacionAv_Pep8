"""Funciones para cargar, guardar y documentar datasets.

Las constantes de diccionario de datos documentan la metadata oficial del
dataset de siniestros viales sin modificar el dataset original ni alterar los
pipelines de carga existentes.
"""

from pathlib import Path
from zipfile import BadZipFile

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


SD_VALUE = "SD"
SD_MEANING = "Sin Datos"

OFFICIAL_DATA_SOURCE = {
    "dataset": "Siniestros viales",
    "organismo": (
        "Secretaria de Transporte - Subsecretaria de Planificacion de la "
        "Movilidad - Observatorio de Movilidad y Seguridad Vial"
    ),
    "jurisdiccion": "Ciudad Autonoma de Buenos Aires",
    "periodo": "2019-2024",
    "portal": "Buenos Aires Data",
}

OFFICIAL_DATA_DICTIONARY = {
    "id_siniestro": "Identificador unico del siniestro.",
    "fecha_siniestro": "Fecha en formato aaaa-mm-dd en la que sucedio el siniestro.",
    "anio_siniestro": "Anio del siniestro.",
    "modo_desplazamiento_victima": (
        "Vehiculo que ocupaba quien haya fallecido o se haya lastimado a raiz "
        "del hecho, o bien peaton/a."
    ),
    "sexo_victima": "Sexo de la victima informado por fuente policial.",
    "edad_victima": "Edad de la victima al momento del siniestro.",
    "gravedad_victima": (
        "Nivel maximo conocido de gravedad de la lesion de la victima del "
        "siniestro en funcion del tiempo de hospitalizacion."
    ),
    "rol_victima": (
        "Posicion relativa al vehiculo que presentaba la victima en el momento "
        "del siniestro."
    ),
    "fecha_fallecimiento_victima": "Fecha de fallecimiento de las victimas mortales.",
}

GRAVEDAD_VICTIMA_ORDER = {
    "LEVE": 1,
    "GRAVE": 2,
    "MORTAL": 3,
}

OFFICIAL_CATEGORY_DEFINITIONS = {
    "gravedad_victima": {
        "LEVE": (
            "Personas lesionadas que reciben el alta medica dentro de las 24hs "
            "siguientes al siniestro o hechos sin datos sobre la gravedad de "
            "las lesiones provocadas."
        ),
        "GRAVE": (
            "Toda persona cuya lesion exige la hospitalizacion de al menos "
            "24 hs o una atencion especializada, como fracturas, conmocion, "
            "shock grave y laceraciones importantes."
        ),
        "MORTAL": (
            "Victima que fallece dentro de los 30 dias de producido el "
            "siniestro vial por causas directa o indirectamente atribuibles al "
            "hecho."
        ),
    },
    "modo_desplazamiento_victima": {
        "AUTO": (
            "Vehiculo a motor destinado al transporte de personas, diferente "
            "de los motovehiculos, y que tenga hasta nueve plazas incluyendo "
            "el asiento del conductor."
        ),
        "BICICLETA": (
            "Vehiculo con al menos dos ruedas, generalmente accionado por el "
            "esfuerzo muscular de sus ocupantes mediante pedales o manivelas; "
            "incluye bicicletas de pedaleo asistido y/o con motor."
        ),
        "CAMION": (
            "Vehiculo a motor disenado para transporte de mercancias con masa "
            "maxima autorizada superior a 3.500 kg."
        ),
        "MIXTO": "Mas de un tipo de usuario/a de la via victima.",
        "MONOPATIN": "Dispositivo de movilidad personal, electrico o no.",
        "MOTO": "Vehiculo a motor no carrozado que incluye motocicleta, ciclomotor y cuatriciclo.",
        "MOVIL": "Vehiculos de emergencia: moviles policiales, ambulancias, autobombas.",
        "OTRO": "Otros vehiculos.",
        "PEATON": (
            "Victima distinta de cualquier ocupante de un vehiculo, ya sea "
            "conductor/a o pasajero/a; incluye personas que empujan o arrastran "
            "coche de bebe, silla de ruedas u otro vehiculo sin motor de "
            "pequenas dimensiones, y personas que caminan empujando bicicleta "
            "o ciclomotor."
        ),
        "SD": "Sin datos sobre el tipo de victima.",
        "TAXI": (
            "Automovil de alquiler no sujeto a itinerario predeterminado, sin "
            "tarifa prefijada para el recorrido total."
        ),
        "TRANSPORTE PUBLICO": (
            "Personas lesionadas dentro, descendiendo o ascendiendo de unidades "
            "de autotransporte publico de pasajeros/as."
        ),
        "UTILITARIO": (
            "Vehiculo a motor disenado para transporte de mercancias con masa "
            "maxima autorizada de hasta 3.500 kg."
        ),
    },
    "rol_victima": {
        "CICLISTA": "Toda persona a bordo de una bicicleta al momento de ocurrido el siniestro.",
        "CONDUCTOR": (
            "Cualquier persona implicada en un siniestro vial con victimas que "
            "estuviera conduciendo un vehiculo en el momento del hecho."
        ),
        "PASAJERO": (
            "Toda persona que, sin ser conductor, se encuentra dentro o sobre "
            "un vehiculo en el momento del siniestro vial, o es arrollada "
            "mientras esta subiendo o bajando del vehiculo."
        ),
        "PEATON": (
            "Cualquier persona implicada en un hecho de transito con victimas, "
            "distinta de un conductor, pasajero o ciclista."
        ),
        "SD": "Sin datos sobre el rol de la victima.",
    },
}


def get_official_metadata() -> dict[str, object]:
    """Devuelve la metadata oficial documentada para analisis reproducible."""
    return {
        "source": OFFICIAL_DATA_SOURCE,
        "data_dictionary": OFFICIAL_DATA_DICTIONARY,
        "category_definitions": OFFICIAL_CATEGORY_DEFINITIONS,
        "gravedad_victima_order": GRAVEDAD_VICTIMA_ORDER,
        "sd_value": SD_VALUE,
        "sd_meaning": SD_MEANING,
    }


def cargar_dataset(ruta_archivo: str | Path, hoja: str | int | None = None) -> pd.DataFrame:
    """Carga un dataset desde un archivo CSV o Excel.

    Parameters
    ----------
    ruta_archivo:
        Ruta del archivo a cargar.
    hoja:
        Hoja de Excel a cargar. Si no se indica, se usa la primera hoja.

    Returns
    -------
    pd.DataFrame
        Dataset cargado en memoria.

    Raises
    ------
    ValueError
        Si el formato del archivo no es compatible o el archivo no puede leerse.
    FileNotFoundError
        Si la ruta indicada no existe.
    """
    ruta = Path(ruta_archivo)
    extension = ruta.suffix.lower()

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontro el archivo: {ruta}")

    if extension in {".xlsx", ".xls"}:
        try:
            archivo_excel = pd.ExcelFile(ruta)
            hojas_disponibles = archivo_excel.sheet_names
            hoja_usada = hoja if hoja is not None else hojas_disponibles[0]

            print(f"Archivo Excel detectado: {ruta.name}")
            print(f"Hojas disponibles: {hojas_disponibles}")
            print(f"Hoja usada: {hoja_usada}")

            data = pd.read_excel(archivo_excel, sheet_name=hoja_usada)
        except BadZipFile as exc:
            raise ValueError(
                f"No se pudo leer el archivo Excel '{ruta}'. "
                "Puede estar corrupto o no ser un Excel valido."
            ) from exc
        except ImportError as exc:
            raise ValueError(
                f"No se pudo leer el archivo Excel '{ruta}'. "
                "Falta una dependencia para leer este formato "
                "(por ejemplo, openpyxl para .xlsx o xlrd para .xls)."
            ) from exc
        except ValueError as exc:
            raise ValueError(
                f"No se pudo leer la hoja '{hoja}' del archivo '{ruta}'. "
                f"Hojas disponibles: {hojas_disponibles if 'hojas_disponibles' in locals() else 'no disponibles'}."
            ) from exc
        except Exception as exc:
            raise ValueError(
                f"No se pudo leer el archivo Excel '{ruta}'. "
                "Puede estar corrupto o tener un formato invalido."
            ) from exc

        print(f"Dataset cargado: {data.shape[0]} filas x {data.shape[1]} columnas")
        return data

    if extension == ".csv":
        try:
            print(f"Archivo CSV detectado: {ruta.name}")
            print("Separador: deteccion automatica")

            data = pd.read_csv(ruta, sep=None, engine="python", encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"No se pudo leer el CSV '{ruta}' con encoding utf-8. "
                "Revise la codificacion del archivo."
            ) from exc
        except EmptyDataError as exc:
            raise ValueError(
                f"No se pudo leer el CSV '{ruta}'. El archivo esta vacio o corrupto."
            ) from exc
        except ParserError as exc:
            raise ValueError(
                f"No se pudo parsear el CSV '{ruta}'. "
                "Revise separadores, comillas, saltos de linea o filas corruptas."
            ) from exc
        except Exception as exc:
            raise ValueError(
                f"No se pudo leer el CSV '{ruta}'. "
                "Puede estar corrupto o tener un formato invalido."
            ) from exc

        print("Hoja usada: no aplica")
        print(f"Dataset cargado: {data.shape[0]} filas x {data.shape[1]} columnas")
        return data

    raise ValueError(
        f"Formato de archivo no compatible: '{extension}'. "
        "Use un archivo Excel (.xlsx, .xls) o CSV (.csv)."
    )


def save_processed_data(data: pd.DataFrame, file_path: Path) -> None:
    """Guarda un dataset procesado en formato CSV."""
    # TODO: Evaluar uso de Parquet si el dataset es grande.
    data.to_csv(file_path, index=False)
