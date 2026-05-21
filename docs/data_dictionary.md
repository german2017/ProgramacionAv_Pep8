# Data Understanding / Diccionario de Datos

Esta seccion documenta el significado institucional de las variables del dataset
oficial **Siniestros viales**, publicado en Buenos Aires Data por la Secretaria
de Transporte, la Subsecretaria de Planificacion de la Movilidad y el
Observatorio de Movilidad y Seguridad Vial de la Ciudad Autonoma de Buenos
Aires. La metadata corresponde a la base de victimas de siniestros viales
2019-2024.

El diccionario de datos es una pieza central del analisis porque traduce nombres
de columnas y codigos categoricos a conceptos observables del dominio vial. Sin
esta capa de metadata, el analisis corre el riesgo de tratar etiquetas
administrativas como si fueran categorias naturales, comparar grupos que no son
equivalentes o imputar valores con supuestos no validados.

## Variables

| Variable | Significado oficial |
| --- | --- |
| `id_siniestro` | Identificador unico del siniestro. |
| `fecha_siniestro` | Fecha en formato aaaa-mm-dd en la que sucedio el siniestro. |
| `anio_siniestro` | Anio del siniestro. |
| `modo_desplazamiento_victima` | Vehiculo que ocupaba quien haya fallecido o se haya lastimado a raiz del hecho, o bien peaton/a. |
| `sexo_victima` | Sexo de la victima informado por fuente policial. |
| `edad_victima` | Edad de la victima al momento del siniestro. |
| `gravedad_victima` | Nivel maximo conocido de gravedad de la lesion de la victima del siniestro en funcion del tiempo de hospitalizacion. |
| `rol_victima` | Posicion relativa al vehiculo que presentaba la victima en el momento del siniestro. |
| `fecha_fallecimiento_victima` | Fecha de fallecimiento de las victimas mortales. |

Nota operativa: en algunos archivos fuente la columna aparece como
`GRAVEdad_victima`. En la documentacion se usa `gravedad_victima`, que es la
denominacion normalizada del diccionario oficial.

## Interpretacion de `SD`

`SD` debe interpretarse como **Sin Datos**. No es una categoria sustantiva del
fenomeno vial, sino una marca de ausencia o falta de especificacion en la fuente.
Por lo tanto, no debe leerse como un modo de desplazamiento, un rol o una
gravedad real. En analisis descriptivos puede mantenerse visible para medir
calidad de datos; en modelado o comparaciones sustantivas requiere tratamiento
explicito.

## `gravedad_victima` como variable ordinal

La variable `gravedad_victima` expresa niveles de severidad con orden de dominio:

| Categoria | Orden analitico | Definicion institucional |
| --- | ---: | --- |
| `LEVE` | 1 | Personas lesionadas que reciben el alta medica dentro de las 24hs siguientes al siniestro o hechos sin datos sobre la gravedad de las lesiones provocadas. |
| `GRAVE` | 2 | Toda persona cuya lesion exige la hospitalizacion de al menos 24 hs o una atencion especializada, como fracturas, conmocion, shock grave y laceraciones importantes. |
| `MORTAL` | 3 | Victima que fallece dentro de los 30 dias de producido el siniestro vial por causas directa o indirectamente atribuibles al hecho. |

El orden `LEVE < GRAVE < MORTAL` debe preservarse en visualizaciones, tablas y
modelos que traten la severidad como escala ordinal. Codificarla como numeros no
implica que la distancia entre niveles sea equivalente; solo representa jerarquia
de severidad.

## Categorias de dominio

### `modo_desplazamiento_victima`

| Categoria | Definicion institucional |
| --- | --- |
| `AUTO` | Vehiculo a motor destinado al transporte de personas, diferente de los motovehiculos, y que tenga hasta nueve plazas incluyendo el asiento del conductor. |
| `BICICLETA` | Vehiculo con al menos dos ruedas, generalmente accionado por esfuerzo muscular mediante pedales o manivelas; incluye bicicletas de pedaleo asistido y/o con motor. |
| `CAMION` | Vehiculo a motor disenado para transporte de mercancias con masa maxima autorizada superior a 3.500 kg. |
| `MIXTO` | Mas de un tipo de usuario/a de la via victima. |
| `MONOPATIN` | Dispositivo de movilidad personal, electrico o no. |
| `MOTO` | Vehiculo a motor no carrozado que incluye motocicleta, ciclomotor y cuatriciclo. |
| `MOVIL` | Vehiculos de emergencia: moviles policiales, ambulancias, autobombas. |
| `OTRO` | Otros vehiculos. |
| `PEATON` | Victima distinta de cualquier ocupante de un vehiculo; incluye personas que empujan o arrastran coche de bebe, silla de ruedas u otro vehiculo sin motor de pequenas dimensiones, y personas que caminan empujando bicicleta o ciclomotor. |
| `SD` | Sin datos sobre el tipo de victima. |
| `TAXI` | Automovil de alquiler no sujeto a itinerario predeterminado, sin tarifa prefijada para el recorrido total. |
| `TRANSPORTE PUBLICO` | Personas lesionadas dentro, descendiendo o ascendiendo de unidades de autotransporte publico de pasajeros/as. |
| `UTILITARIO` | Vehiculo a motor disenado para transporte de mercancias con masa maxima autorizada de hasta 3.500 kg. |

### `rol_victima`

| Categoria | Definicion institucional |
| --- | --- |
| `CONDUCTOR` | Persona implicada en un siniestro vial con victimas que conducia un vehiculo en el momento del hecho. |
| `PASAJERO` | Persona que, sin ser conductor, se encontraba dentro o sobre un vehiculo, o fue arrollada mientras subia o bajaba del vehiculo. |
| `CICLISTA` | Persona a bordo de una bicicleta al momento del siniestro. |
| `PEATON` | Persona implicada en un hecho de transito con victimas, distinta de conductor, pasajero o ciclista. |
| `SD` | Sin datos sobre el rol de la victima. |

## Riesgos de interpretacion incorrecta

- Tratar `SD` como categoria real puede sobredimensionar grupos que en realidad
  expresan falta de informacion.
- Ordenar alfabeticamente `gravedad_victima` rompe la jerarquia de severidad y
  puede distorsionar graficos o reportes.
- Usar `LEVE`, `GRAVE` y `MORTAL` como clases nominales ignora que existe una
  progresion institucional de severidad.
- Interpretar `MIXTO` u `OTRO` sin revisar su definicion puede mezclar perfiles
  de victimas con significados heterogeneos.
- La categoria `LEVE` incluye hechos sin datos sobre gravedad de lesiones, por lo
  que cualquier conclusion sobre baja severidad debe reportar esta limitacion.

## Metadata y calidad analitica

El conocimiento de dominio mejora la calidad analitica porque permite distinguir
errores, faltantes, categorias administrativas y conceptos sustantivos. En este
dataset, la metadata define que la severidad se relaciona con hospitalizacion,
atencion especializada y fallecimiento dentro de los 30 dias del siniestro. Esa
informacion afecta la seleccion de variables, el tratamiento de faltantes, la
codificacion ordinal y la interpretacion de resultados.

La calidad de un analisis no depende solo de la cantidad de registros o de la
tecnica estadistica aplicada. Tambien depende de que las variables sean
comprendidas segun su proceso de produccion institucional. Documentar metadata
es, por lo tanto, una practica de reproducibilidad y una condicion para evitar
conclusiones tecnicamente correctas pero conceptualmente equivocadas.
