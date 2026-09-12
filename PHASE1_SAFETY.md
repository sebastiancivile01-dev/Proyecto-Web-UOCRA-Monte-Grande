# Fase 1: seguridad previa a Azure

Se mantienen app.py, sus pantallas y esquemas existentes. safety.py contiene
únicamente las protecciones testeables de persistencia, sesión y GeoJSON.
No hay migraciones de datos ni cambios de secretos.

## Persistencia y concurrencia

- Una lectura fallida invalida la versión de sesión y detiene la ejecución;
  no devuelve una tabla vacía ni habilita formularios sobre datos fallidos.
- La caché de Sheets conserva éxitos y fallos por hoja durante 120 segundos.
  Un fallo se representa con None, distinto de una hoja vacía válida, y no
  elimina las entradas de las otras hojas ni se reintenta en cada rerun.
- guardar_db devuelve bool y sus 34 callers se detienen ante False.
- Una única petición RAW guarda encabezados, datos y blancos para las filas
  eliminadas. Se conservan columnas y orden existentes, sin clear previo.
- Antes de escribir se compara la hoja actual con la lectura original. Ante
  conflicto se debe actualizar y revisar antes de intentar otra vez.
- Todo intento de escritura con lectura válida consume la versión de sesión
  e invalida únicamente su clave de caché original, incluso ante conflicto o
  respuesta incierta. No elimina las otras hojas. Sin lectura válida no se
  consulta ni escribe Sheets y se conserva el fallo cacheado.
  Una respuesta perdida puede ocultar una escritura aplicada: verificar antes
  de repetir. El botón manual Actualizar Datos conserva su borrado global.

El RLock compartido serializa comprobación y escritura entre sesiones del MISMO
proceso. Desplegar esta fase con UNA instancia y UN proceso escritor. No ejecutar
otra copia de la app ni editar directamente la hoja durante esas operaciones.
La comparación NO es compare-and-swap distribuido: un editor externo podría
escribir entre la lectura de comprobación y la actualización. Antes de habilitar
más instancias/escritores se necesita coordinación distribuida; queda fuera de
esta fase. La atomicidad de cada petición no incluye la lectura previa:
https://developers.google.com/workspace/sheets/api/limits

## Sesión y permisos

Logout y nuevo login limpian session_state (navegación, chat, recibos, formularios
y versiones). ABM y Reclamos exigen Admin al ejecutar el módulo. Se preservan
los flujos ya habilitados de reclamos desde Calculadoras; no se redefine la
matriz de permisos de otros módulos.

## Mapa y credenciales

assets/README.md documenta la fuente oficial Datos Argentina (Departamentos
GeoJSON, CC BY 4.0), atribución y hashes. Se conservan los 135 partidos de Buenos
Aires, incluidos los diez de la jurisdicción; departamento es un alias de nombre.
Reemplaza el asset anterior sin licencia declarada. Un recurso ausente o dañado
produce un aviso y omite límites, conservando marcadores. Las teselas
siguen siendo externas. La demo de login usa las mismas claves de secrets que
app.py. Las contraseñas retiradas siguen en el historial: si siguen vigentes,
rotarlas fuera de este cambio. No se leyó ni modificó secrets.toml.

## Pruebas y pendientes

Windows: `.venv/Scripts/python.exe -B -m unittest discover -s tests -v`.
Linux: `.venv/bin/python -B -m unittest discover -s tests -v`.
Los tests bloquean HTTP y usan hojas falsas. Ejecutan segmentos reales de app.py
sin importar la app completa ni acceder a secretos o producción. Incluyen
lectura/escritura fallida, eliminación de filas, columnas, dos usuarios,
resultado incierto, los 34 guards, alta de obra, roles, logout y mapa sin red.

Pendientes fuera de alcance: reorganización general, identidad territorial,
otros cálculos y despliegue. Una subida a Storage seguida de fallo en Sheets
puede dejar un objeto sin registro; no hay transacción entre esos servicios.
Validar en staging antes de producción: no se hizo un recorrido con datos reales.

La regla de .gitattributes reconoce los CRLF existentes de app.py sin desactivar
los controles de espacios finales. Durante el test de Folium, la versión local
emitió un aviso sobre API key de CartoDB; verificar ese proveedor en staging.
No se cambió el mapa base ni se inventó una clave.
