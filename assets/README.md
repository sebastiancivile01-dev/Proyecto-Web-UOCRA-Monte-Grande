# Límites territoriales oficiales — Buenos Aires

## Fuente y atribución

Datos Argentina / Jefatura de Gabinete de Ministros, Secretaría de Innovación
Pública, Subsecretaría de Servicios y País Digital. Dataset **Servicio de
normalización de datos geográficos**, recurso **Departamentos (GeoJSON)**,
elaborado en base a datos del Instituto Geográfico Nacional (IGN).

- [Dataset oficial](https://datos.gob.ar/dataset/jgm-servicio-normalizacion-datos-geograficos).
- [Ficha del recurso jgm_8.17](https://datos.gob.ar/dataset/jgm-servicio-normalizacion-datos-geograficos/archivo/jgm_8.17).
- [Descarga oficial utilizada](https://infra.datos.gob.ar/georef/departamentos.geojson).
- [Ficha del catálogo consultada con licencia explícita](https://datos.gob.ar/ar/dataset/jgm-servicio-normalizacion-datos-geograficos).
- Licencia del dataset: **Creative Commons Attribution 4.0 International
  (CC BY 4.0)** — https://creativecommons.org/licenses/by/4.0/.
- Fecha de descarga: 2026-09-12.

Atribución: «Datos Argentina / Jefatura de Gabinete de Ministros — Servicio de
normalización de datos geográficos, Departamentos (GeoJSON), basado en IGN.
Licencia CC BY 4.0. Adaptación para UOCRA Monte Grande: selección de Provincia de
Buenos Aires y agregado de la propiedad departamento como alias de nombre».
Esta adaptación no implica aval del organismo de origen.

## Transformaciones y validación

- Features descargados (Argentina): **529**.
- Features conservados (Buenos Aires): **135**, filtrando exactamente
  `properties.provincia.id == "06"`.
- Se conservaron sin cambios geometrías, coordenadas, identificadores y todas
  las propiedades oficiales. No se simplificaron ni redondearon coordenadas.
- Única propiedad agregada: `properties.departamento = properties.nombre`.
  Permite mantener intactos `filtrar_partidos()` y `safety.py`.
- Serialización JSON compacta UTF-8. Se validaron los 529 features originales
  (con el alias) y los 135 locales como Polygon/MultiPolygon.
- SHA-256 de la descarga: `31afdfe5983b6d7648eba1eafc7a5a8fe3c591abdca4b17c311c08c75d361e92`.
- SHA-256 del archivo local: `a90b9f8c172dc0a935368da3ba282146707cf686689ce7ee174635b5414e93a1`.

## Jurisdicciones actuales verificadas

| ID oficial | Partido |
| --- | --- |
| 06260 | Esteban Echeverría |
| 06270 | Ezeiza |
| 06134 | Cañuelas |
| 06693 | Roque Pérez |
| 06483 | Lobos |
| 06707 | Saladillo |
| 06547 | Monte |
| 06301 | General Belgrano |
| 06329 | General Las Heras |
| 06574 | Navarro |

El nombre oficial «General Las Heras» corresponde a «Las Heras» en la lista
actual de jurisdicciones de la app. El filtro existente ya lo reconoce.
Se verificó que el filtro selecciona exactamente estos diez partidos y excluye,
entre otros, Monte Hermoso y General Viamonte.

## Uso sin red y actualización

La aplicación usa exclusivamente la copia local para los límites. Si falta o
está dañada, avisa y conserva obras, polos y marcadores sin esa capa. Las teselas
del mapa base siguen siendo externas. No hay descargas de GeoJSON en runtime.

Para actualizar: descargar el recurso oficial, filtrar por provincia.id 06,
agregar el alias departamento, validar con safety.validar_geojson y comprobar
las diez jurisdicciones antes de reemplazar. Actualizar fecha, conteos y hashes,
conservar esta atribución y ejecutar los tests. No usar la respuesta de la API
/departamentos?formato=geojson: devuelve centroides Point, no estos polígonos.

Esta copia reemplaza completamente el asset anterior del repositorio
mgaitan/departamentos_argentina, cuya licencia no estaba declarada.
