# Screens

Las pantallas existentes se ejecutan mediante `legacy_runtime.py` para conservar
exactamente el comportamiento de la Fase 1 durante esta migracion estructural.
El bootstrap lo ejecuta de forma diferida; importar `screens`, `screens.router` o
los boundaries nuevos no conecta servicios productivos.

El siguiente paso funcional puede extraer cada bloque del runtime en modulos
individuales usando los contratos de `data/`, `services/`, `domain/` y `auth/`.
