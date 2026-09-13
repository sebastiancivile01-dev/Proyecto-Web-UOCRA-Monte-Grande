# Auditoría funcional posterior a Fase 2

Fecha: 13/09/2026. Rama: `fix/post-phase2-stabilization`.

## Estado inicial y alcance

- Working tree limpio; rama inicial `main`.
- `git fetch origin` completado. `git rev-list --left-right --count main...origin/main`: `0 0`.
- Base: `d322eb9`, merge de Fase 2 (PR #3).
- Rama nueva creada desde esa base; no se cambió de rama después.
- Suite base: **43 tests, OK**.
- Entorno existente: `.venv/Scripts/python.exe`, Streamlit 1.60.0, pandas 3.0.5.
- No se instalaron dependencias. No se realizaron commit, push, merge ni staging.
- No se accedió a producción, ni se leyeron o modificaron Secrets. No se hicieron cargas reales a Storage ni escrituras reales en Sheets.

## A. Bugs confirmados y corregidos

| Hallazgo reproducido | Causa raíz | Corrección mínima y evidencia |
| --- | --- | --- |
| IERIC conserva aportes al cambiar persona o empresa | `quincenas` era estado independiente de la identidad usada para reclamar | Asociación de sesión `(Nombre, Empresa)`; al cambiarla se descartan quincenas, bruto, fecha y motivo. Tests de cambio de ambos campos, recarga, volver al panel, recalcular y reclamo pendiente al cambiar nombre. |
| Calendario falla al abrirse | El servicio extraído usa `df_cierres`, variable del antiguo monolito que no estaba en su ámbito | Bootstrap inyecta explícitamente la tabla al construir servicios. Pruebas desde navegación con tabla vacía y con cronograma. No se alteraron feriados, fechas ni URLs. |
| Subir dos documentos del mismo título reemplaza el primero | Documentación genera `Doc_<título>.pdf`; Galería reutiliza `Media_<título>_<posición>.<extensión>`; Storage subía sin condición de creación | Prefijo UUID completo por carga, basename/extensión conservados y `if_generation_match=0`. Cliente simulado demuestra dos contenidos independientes y rechazo de una colisión forzada. Títulos visibles y enlaces existentes intactos. |
| Ediciones ABM fallan o asignan valores a columnas equivocadas | `.loc[idx] = lista` depende del orden y cantidad de columnas de Sheets | Asignación a columnas explícitas para Predios, Obras, Delegados y Contactos. Ocho escenarios de regresión: columnas invertidas, con y sin una columna adicional que debe conservarse. |
| Borradores de edición sobreviven al cambiar de entidad | Formularios compartidos entre filas mantienen widgets cuyo valor inicial coincide | Identidad del formulario incluye la fila seleccionada en ABM, Cupo de Mujeres y Convenios. Tests con borradores de Contactos, Cupo y Convenios. No se introdujeron IDs persistentes. |
| ABM falla al activar varias pestañas de eliminación | Los tabs se ejecutan juntos y registraban varios botones `Eliminar` con la misma identidad | Keys diferenciadas por operación/tabla para botones y selectores relacionados. Prueba de las tres pestañas de eliminación simultáneas. |
| Eliminar una observación puede borrar la de otra empresa | Se descartaba el índice al ordenar y se recuperaba la primera coincidencia por fecha/texto, ignorando empresa | Se conserva la fila original durante filtrado y orden. Prueba con dos empresas, igual fecha y texto, filtrando la segunda: permanece exclusivamente la primera. También se quitó el import local de `time` que dejaba ese nombre sin inicializar en la ruta de eliminación. |
| Búsquedas como `[` rompen pantallas | `str.contains` interpretaba la entrada como expresión regular | Búsqueda literal y conversión a texto en Nóminas, Convenios, Documentación y Observaciones. Se prueban caracteres especiales y CUIL numérico en las tablas de prueba. |
| Paritarias muestra $60.000 tras guardar $6.000 | El formateador eliminaba el punto decimal del número Python `6000.0` | Los números ya tipados se formatean directamente; se mantiene el tratamiento anterior de textos. Test que fallaba con `$ 60,000.00` y exige `$ 6,000.00`. No cambia el valor guardado ni las fórmulas. |

La batería inicial de regresiones dio 19 fallos en 9 métodos antes de las correcciones; el error de presentación de Paritarias se reprodujo posteriormente con una aserción adicional. La prueba de borrar la última quincena también detectó que el árbol de widgets conservaba la acción de reclamo después del rerun; el borrado se ejecuta ahora en un callback previo al render, y esa prueba pasa. No se atribuyen todos estos defectos a Fase 2: el calendario es una dependencia perdida en la extracción; varios de los demás defectos ya estaban presentes en los flujos conservados.

## Recorrido funcional

El harness `tests/offline_app.py` ejecuta el bootstrap y las pantallas reales. Sustituye tablas y clientes por datos ficticios y bloquea conexiones de red. `st.secrets` se reemplaza temporalmente por un diccionario sintético en memoria; no se abre ningún archivo de secretos.

| Pantalla/flujo | Verificación |
| --- | --- |
| Login/logout | Contraseña incorrecta, ingreso Admin/Restringido, borrado de recibos, chat, quincenas, identidad IERIC y snapshots al salir. |
| Permisos | ABM y Reclamos detienen ejecución para Restringido, aun seleccionándolos en sesión. Paritarias no expone guardado a Restringido. Se mantiene la matriz existente, incluidos reclamos desde calculadoras. |
| Mapa | Render vacío/poblado, ambos roles, límites ausentes con aviso; la suite original valida GeoJSON y render sin red. No se validan teselas externas. |
| ABM | Alta cubierta por suite original; edición con columnas reordenadas/adicionales; cambio de entidad; tabs de eliminación simultáneos. |
| Nóminas | Tres repositorios, tablas vacías/pobladas, filtro literal y CUIL numérico. |
| Quincena | Manual y automática con jornada ficticia de 8 horas: neto esperado $772,80. Cambiar nombre después del cálculo mantiene el reclamo asociado al nombre del recibo calculado. |
| IERIC | Carga, rerun sin cambio de identidad, cambio de nombre/empresa, volver atrás, recalcular, borrar última quincena, intento pendiente de reclamo y fallo de guardado. |
| Vacaciones/SAC | Se verifica la pantalla existente «Próximamente». No se implementaron calculadoras nuevas. |
| Paritarias | Guardado local, lectura del historial, importe mostrado y acceso por rol. |
| Reclamos | Render y bloqueo por rol; altas desde calculadoras con datos ficticios; guardas de persistencia originales. |
| Mujeres | Tablas vacías/pobladas, agenda y cupo; borrador de cupo aislado al cambiar obra. |
| Documentación/Convenios | Render, búsquedas y borrador por convenio; servicio de subida probado con bucket simulado. Suite original comprueba éxito solo tras confirmar Sheets. |
| Estadísticas | Tablas vacías/pobladas y ambos roles. |
| Galería | Render vacío/poblado y roles; protección común de Storage, incluidos basename y extensión de multimedia. |
| Asistente | Configuración/modelo/chat simulados; prompt, selección de contexto e historial de respuesta sin llamar Gemini. |
| Auditoría | Escaneo de tablas ficticias con faltantes y tablas vacías; generación del reporte existente. |
| Observaciones | Búsqueda literal y borrado de la fila de la empresa realmente mostrada. |
| Propuestas | Se renderiza en cada pantalla autorizada; envío y registro simulados. |

La matriz de render comprende **12 pantallas × 2 roles × 2 estados de tablas = 48 escenarios**, además de las interacciones anteriores. Esto no equivale a probar todas las combinaciones de datos productivos ni todas las operaciones de cada formulario.

## Sheets, contexto y bootstrap

- No se modificaron `safety.py`, `data/runtime.py`, snapshots ni caché.
- Se conservan los tests originales de lectura fallida, snapshot, conservación de columnas, escritura única RAW, conflicto entre dos usuarios, respuesta incierta, 429, TTL e invalidación selectiva.
- Las pantallas reciben las dependencias que usan en los recorridos comprobados. El análisis de símbolos encontró `df_cierres` como referencia global faltante; se corrigió.
- Imports de entrypoint, bootstrap, runtimes, auth y todas las pantallas completaron sin conectarse a servicios.
- El bootstrap usa su tabla de handlers directamente; `screens/router.py` conserva su prueba. No se rediseñó `ScreenContext`.

## B. Riesgos confirmados pendientes por reglas o arquitectura

1. **Concurrencia entre procesos y editores externos.** El `RLock` protege un único proceso. No existe compare-and-swap distribuido entre la comprobación de versión y la escritura de Sheets. Limitación previa de Fase 1, sin regresión nueva demostrada ni implementación para Azure.
2. **Identidad Obra/Polo/Empresa.** ABM y Mujeres seleccionan obras por `Predio (Empresa)` y resuelven la primera coincidencia. Los formularios no establecen unicidad; dos filas con la misma etiqueta resultan ambiguas. Predios se editan por nombre y se borran por filtro de nombre. Determinar si son duplicados o entidades distintas requiere las reglas de Fase 3. No se redefinieron Obra, Obra_ID, Predio_ID ni relaciones.
3. **Otras identidades por texto.** Delegados, Contactos, Reclamos y Convenios contienen selecciones por nombres o etiquetas compuestas. La política de homónimos/duplicados sigue pendiente; no se impuso unicidad nueva ni se eliminaron datos.
4. **Storage y Sheets no forman una transacción.** Una carga confirmada seguida de fallo de Sheets puede dejar un objeto sin registro. Preexistente y documentado en Fase 1; no se eliminaron objetos ni se implementó compensación automática.
5. **Calendario estático 2026.** El servicio agrega una lista fija de 2026 a lo que devuelve la API del año actual. Puede duplicar fechas y no es una solución válida general para otros años. Elegir fuente canónica, precedencia y actualización queda pendiente; esta corrección solo repara la dependencia del cronograma.

## C. Riesgos potenciales y límites

- Los índices de fila son identidades de presentación, no IDs estables: queda pendiente verificar con un diseño de sesión/versionado más amplio la interacción entre refresco de datos, reordenamiento externo y acciones ya mostradas. Los tests de concurrencia actuales cubren la escritura respecto del snapshot, no todas las carreras entre navegador y un nuevo render.
- No se inspeccionaron datos productivos. Encabezados faltantes, coordenadas inválidas, radios fuera del mínimo de widgets, valores negativos históricos o formatos numéricos textuales ambiguos requieren una revisión de datos separada. No se normalizó ni migró Sheets.
- IERIC conserva el modelo actual de identidad textual `(Nombre, Empresa)`; no puede distinguir homónimos idénticos que la aplicación no identifica por otro dato.
- AppTest no reproduce íntegramente el rerun de fragmentos de un navegador. Para comprobar el contenido del diálogo del calendario se reabre desde el botón después de cambiar el selector.
- BCRA, feriados, Gemini, autenticación de Google, permisos efectivos del bucket, videos y teselas no se probaron contra servicios reales.

## D. Mejoras futuras

- Contextos por pantalla más pequeños y contratos explícitos, sin otro refactor en esta tarea.
- Actualizar los README de paquetes que todavía describen `legacy_runtime.py`, ya inexistente.
- Evaluar migración del SDK `google.generativeai` y APIs Streamlit obsoletas (`use_container_width`), avisadas por las dependencias instaladas. No se cambiaron dependencias, diseño ni integración.
- Revisar rangos de fechas y validaciones de entrada en calculadoras/ABM en una tarea específica, sin modificar reglas gremiales aquí.

## Archivos y revisión de alcance

Archivos de aplicación modificados: `bootstrap.py`, `services/runtime.py`, `services/storage.py`, `screens/abm.py`, `screens/calculadoras.py`, `screens/documentacion.py`, `screens/mujeres.py`, `screens/nominas.py`, `screens/observaciones.py`.

Archivos nuevos: `tests/offline_app.py`, `tests/test_post_phase2.py` y este informe. Los tres archivos de tests originales permanecen intactos. Hay 20 métodos nuevos de prueba, varios con múltiples escenarios.

Se revisó el diff completo. Los cambios de ABM solo reparan la correspondencia columna/valor y la identidad de widgets/formularios; no alteran las relaciones de dominio. No se modificaron fórmulas de liquidación, CER o porcentajes IERIC. No hay CSS nuevo, assets, URLs de servicio, hojas o columnas renombradas, cambios de permisos, credenciales reales, archivos temporales ni contenido de `.venv` añadido. No se creó un monolito nuevo.

## Verificación final

- Comando obligatorio: `.venv\Scripts\python.exe -B -m unittest discover -s tests -v`.
- Resultado definitivo: **63 tests en 174,815 segundos, OK; exit code 0**. Se conservan los 43 originales y se agregan 20 tests. No hay fallos, errores ni tests omitidos.
- Compilación con `compile()` de los 47 archivos Python del proyecto, excluyendo `.venv`/`.git`: OK, sin escribir bytecode.
- Imports relevantes con conexiones bloqueadas: OK.
- Smoke local: `streamlit run app.py`, ligado a `127.0.0.1`, directorio temporal sin Secrets, sin navegador ni telemetría; `/_stcore/health` devolvió HTTP 200 y `ok`. Proceso detenido y directorio eliminado. Es una prueba de arranque; el recorrido funcional lo cubre AppTest.
- `git diff --check`: OK.
- No se hizo commit, push, merge ni staging. Los cambios quedan disponibles para revisión en la rama indicada.

## Estado Git al cierre

`git status --short --branch`:

```text
## fix/post-phase2-stabilization
 M bootstrap.py
 M screens/abm.py
 M screens/calculadoras.py
 M screens/documentacion.py
 M screens/mujeres.py
 M screens/nominas.py
 M screens/observaciones.py
 M services/runtime.py
 M services/storage.py
?? POST_PHASE2_AUDIT.md
?? tests/offline_app.py
?? tests/test_post_phase2.py
```

`git diff --stat`:

```text
 bootstrap.py             |  2 +-
 screens/abm.py           | 32 ++++++++++++++++----------------
 screens/calculadoras.py  | 28 ++++++++++++++++++++--------
 screens/documentacion.py |  6 +++---
 screens/mujeres.py       |  2 +-
 screens/nominas.py       | 16 +++++++++++-----
 screens/observaciones.py | 10 ++++------
 services/runtime.py      | 11 +++++++----
 services/storage.py      | 11 +++++++++++
 9 files changed, 74 insertions(+), 44 deletions(-)
```

El diff de Git no incluye los tres archivos nuevos sin seguimiento; no se agregaron al ?ndice.
