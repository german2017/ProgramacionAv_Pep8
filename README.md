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

### Firebase / Firestore

La etapa de Firebase persiste resultados ya generados. No reentrena modelos y no modifica `data/raw/`.

Firebase es la plataforma de backend de Google que provee servicios como autenticacion, hosting y bases de datos. Firestore es la base de datos NoSQL documental dentro de Firebase/Google Cloud. En este proyecto se usa Firestore porque los resultados de experimentos de Machine Learning son documentos semiestructurados: metadata del dataset, metricas, validacion cruzada, configuracion del modelo y eventos de auditoria.

La persistencia aporta trazabilidad al experimento: permite reconstruir que dataset se uso, que modelo fue seleccionado, con que features, bajo que estrategia de validacion y con que metricas. Esto es clave para comparar futuras iteraciones y justificar el candidato que luego podria pasar a produccion.

Configurar credenciales locales:

1. Crear una cuenta de servicio en Firebase / Google Cloud con permisos de Firestore.
2. Descargar el JSON de credenciales en una ruta local fuera del repo.
3. Guardar el JSON en una ruta local segura. Puede estar fuera del repo o en el repo de forma local, pero nunca debe subirse.
4. Copiar `.env.example` como `.env`.
5. Completar:

```env
FIREBASE_CREDENTIALS_PATH=<ruta-local-al-service-account.json>
FIREBASE_PROJECT_ID=nombre-del-proyecto-firebase
```

El archivo `.env` esta ignorado por Git. No subir credenciales ni service accounts al repositorio.

Validar payloads sin escribir:

```bash
python scripts/upload_results_firebase.py --dry-run
```

Ejecutar la carga real a Firestore:

```bash
python scripts/upload_results_firebase.py
```

Tambien se puede revisar la etapa desde:

- `notebooks/08_firebase.ipynb`

Colecciones creadas en Firestore:

- `datasets`: metadata del dataset procesado `siniestros_limpio_enriquecido`, incluyendo filas, columnas, tipos, fuente y version.
- `model_results`: documento `modelo_ganador` con metricas holdout, resumen de comparacion, F1 promedio, desvio estandar y configuracion del modelo seleccionado.
- `cross_validation`: documento `experimento_actual` con estrategia `StratifiedKFold`, tabla comparativa, fold scores y criterio de seleccion.
- `logs`: documento `eventos` y subcoleccion `items` con eventos de auditoria del proceso de carga.

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
