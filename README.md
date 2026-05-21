# Prediccion y Analisis de Siniestros Viales

Trabajo practico final universitario de ciencia de datos orientado al analisis, procesamiento y modelado predictivo de un dataset de siniestros viales.

El proyecto busca aplicar un flujo completo de trabajo de ciencia de datos: carga de datos, analisis exploratorio, limpieza, transformacion de variables, entrenamiento de modelos predictivos, evaluacion, persistencia en base de datos y generacion de visualizaciones finales.

## Objetivo General

Desarrollar una solucion de ciencia de datos que permita analizar siniestros viales y construir modelos predictivos capaces de estimar una variable objetivo definida a partir del dataset disponible.

## Data Understanding / Diccionario de Datos

El proyecto incorpora el diccionario oficial del dataset **Siniestros viales** publicado en Buenos Aires Data por la Secretaria de Transporte, la Subsecretaria de Planificacion de la Movilidad y el Observatorio de Movilidad y Seguridad Vial de la Ciudad Autonoma de Buenos Aires.

La documentacion completa se encuentra en `docs/data_dictionary.md`. Esa seccion registra el significado oficial de las variables, las definiciones institucionales de categorias y los riesgos de interpretacion asociados al uso de codigos administrativos.

Puntos clave para el analisis:

- `SD` se interpreta como **Sin Datos**. No debe tratarse como categoria sustantiva del fenomeno vial.
- `gravedad_victima` representa la severidad de la lesion y debe considerarse una variable ordinal: `LEVE < GRAVE < MORTAL`.
- `LEVE` identifica personas lesionadas con alta medica dentro de las 24hs siguientes al siniestro o hechos sin datos sobre gravedad de lesiones.
- `GRAVE` identifica lesiones que exigen hospitalizacion de al menos 24 hs o atencion especializada.
- `MORTAL` identifica victimas que fallecen dentro de los 30 dias de producido el siniestro vial por causas directa o indirectamente atribuibles al hecho.
- Las categorias de `modo_desplazamiento_victima` y `rol_victima` tienen semantica de dominio y no deben interpretarse solo por su etiqueta textual.

El uso del diccionario de datos mejora la calidad analitica porque conecta cada variable con su definicion institucional y con el proceso de produccion de la informacion. Esta metadata reduce riesgos de sesgo conceptual, evita codificaciones incorrectas y ayuda a definir tratamientos consistentes para faltantes, categorias ambiguas y variables ordinales.

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

Notebooks principales:

- `notebooks/01_eda.ipynb`: analisis exploratorio con seccion de diccionario oficial y tratamiento ordinal de `gravedad_victima`.
- `notebooks/02_preprocessing.ipynb`: criterios de preprocesamiento basados en metadata, sin modificar el dataset original ni alterar pipelines existentes.

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
