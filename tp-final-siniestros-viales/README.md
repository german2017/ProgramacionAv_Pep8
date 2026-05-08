# Prediccion y Analisis de Siniestros Viales

Trabajo practico final universitario de ciencia de datos orientado al analisis, procesamiento y modelado predictivo de un dataset de siniestros viales.

El proyecto busca aplicar un flujo completo de trabajo de ciencia de datos: carga de datos, analisis exploratorio, limpieza, transformacion de variables, entrenamiento de modelos predictivos, evaluacion, persistencia en base de datos y generacion de visualizaciones finales.

## Objetivo General

Desarrollar una solucion de ciencia de datos que permita analizar siniestros viales y construir modelos predictivos capaces de estimar una variable objetivo definida a partir del dataset disponible.

## Tecnologias Usadas

- Python
- pandas
- NumPy
- matplotlib
- seaborn
- plotly
- scikit-learn
- MongoDB
- PyMongo
- Jupyter Notebook
- joblib

## Estructura del Repositorio

```text
tp-final-siniestros-viales/
├── data/
│   ├── raw/                 # Datos originales sin modificar
│   └── processed/           # Datos limpios o transformados
├── notebooks/               # EDA y experimentacion
├── outputs/
│   ├── figures/             # Visualizaciones generadas
│   ├── metrics/             # Archivos de metricas
│   └── models/              # Modelos serializados
├── scripts/
│   ├── load_to_db.py        # Carga de datos/resultados en MongoDB
│   └── train.py             # Ejecucion del pipeline de entrenamiento
├── src/
│   ├── __init__.py
│   ├── config.py            # Configuracion general del proyecto
│   ├── data_loader.py       # Carga y guardado de datasets
│   ├── database.py          # Conexion y operaciones con MongoDB
│   ├── evaluation.py        # Evaluacion de modelos
│   ├── feature_engineering.py
│   ├── models.py            # Definicion y entrenamiento de modelos
│   └── preprocessing.py     # Limpieza y preparacion de datos
├── .gitignore
├── README.md
└── requirements.txt
```

## Instalacion

Clonar el repositorio:

```bash
git clone <url-del-repositorio>
cd tp-final-siniestros-viales
```

Crear y activar un entorno virtual:

```bash
python -m venv venv
```

En Windows:

```bash
venv\Scripts\activate
```

En Linux/macOS:

```bash
source venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecucion

Colocar el dataset original en la carpeta:

```text
data/raw/
```

Ejecutar notebooks de analisis exploratorio desde:

```text
notebooks/
```

Ejecutar el pipeline principal de entrenamiento:

```bash
python scripts/train.py
```

Ejecutar la carga hacia MongoDB:

```bash
python scripts/load_to_db.py
```

## Estado Actual del Proyecto

El proyecto se encuentra en etapa inicial. Actualmente cuenta con la estructura base del repositorio, archivos de configuracion, dependencias iniciales y modulos preparados con comentarios TODO para futuras implementaciones.

Todavia no se incluyen resultados, metricas ni modelos entrenados.

## Autores

- Nombre Apellido
- Nombre Apellido

## Futuras Mejoras

- Definir la variable objetivo del problema predictivo.
- Completar el analisis exploratorio de datos.
- Implementar reglas de limpieza y validacion del dataset.
- Agregar feature engineering especifico para siniestros viales.
- Entrenar y comparar al menos dos modelos predictivos.
- Evaluar los modelos con RMSE, MAE y R2.
- Persistir datasets procesados, predicciones y metricas en MongoDB.
- Incorporar visualizaciones finales para comunicar hallazgos relevantes.
