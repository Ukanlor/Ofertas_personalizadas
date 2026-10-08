# Progreso

## Estado actual

- Última capa cerrada: **1 - Núcleo de datos**.
- Estado: implementación, pruebas automáticas y validación manual completas.
- Próxima capa planificada: **2 - Telegram de preferencias**, no iniciada.
- Rama inspeccionada: `main`.
- Punto de partida: commit inicial `e12c2b6`.
- Punto de control funcional de capas 0-1: commit local `f5f4c51`.
- Código de producto: núcleo local y CLI disponibles; sin integraciones externas.

## Decisiones registradas

- El desarrollo se realizará directamente en el entorno Windows actual de Codex.
- El servidor futuro será otro notebook con Windows 11.
- La preparación o actualización de ese notebook se hará cuando una etapa la
  necesite.
- Base propuesta: Python 3.12 y SQLite local.
- Interés canónico: `null` sin puntuar, `0` ignorado y `1-10` puntuado.
- Propiedad por variante, no bloqueo global implícito entre plataformas.
- La capa 10 se ocupará de operación continua en Windows 11; no de migrar desde
  Linux.

## Trabajo realizado en la capa 0

- Se inspeccionó el repositorio antes de editar.
- Se amplió `README.md` con objetivo, alcance, entornos y estado.
- Se creó `PROJECT_SPEC.md` con reglas, arquitectura, capas y pendientes.
- Se creó `AGENTS.md` con límites de trabajo y verificación.
- Se creó `BACKLOG.md` para separar las ideas aplazadas del MVP.
- El usuario aprobó la documentación y autorizó comenzar la capa 1.

## Trabajo realizado en la capa 1

- Se creó un entorno virtual Python 3.12 nativo de Windows, sin dependencias
  externas ni `pip` por ahora.
- Se añadieron lanzadores `.cmd` para preparar el entorno y ejecutar la CLI sin
  depender de la política de ejecución de PowerShell. Los scripts `.ps1` se
  mantienen como alternativa.
- Se añadieron migraciones numeradas para catálogo y para
  preferencias/propiedad.
- Se implementaron juegos, alias, variantes, búsqueda, interés, ignorar,
  reactivar y propiedad por variante.
- Se separaron dominio, servicios y persistencia SQLite.
- Se añadieron restricciones de claves foráneas, puntuación, identidad y
  variantes duplicadas.
- Se protegieron las colisiones entre títulos canónicos y alias.
- Se añadió una suite reproducible con datos temporales dentro del repositorio e
  ignorados por Git.

## Verificación

- `git diff --check`: ejecutado sin errores de espacios o formato; Git informó
  únicamente la conversión esperada de LF a CRLF en Windows.
- Enlaces Markdown del `README.md`: todos apuntan a archivos existentes.
- Reglas de entorno, interés y propiedad: contrastadas entre `README.md`,
  `PROJECT_SPEC.md`, `AGENTS.md` y este registro.
- `python -m compileall -q src tests`: correcto.
- `python -m unittest discover -s tests -v`: 10 pruebas correctas.
- Casos cubiertos: `null`, `0`, `1`, `10`, entradas inválidas, duplicados,
  alias, claves foráneas, rollback transaccional, migración con datos existentes,
  reinicio y persistencia.
- Demostración CLI automática: Hades con interés 8; Steam poseído y Switch no
  poseído después de abrir la base desde un proceso nuevo.
- Primer intento de validación manual: el usuario confirmó que Windows bloqueó
  el lanzador `.ps1` por su política de ejecución. No se modificó la política;
  se añadió el lanzador `.cmd`.
- Verificación automática del reemplazo: `bootstrap.cmd`, `ofertas.cmd db init`
  y `ofertas.cmd --help` finalizaron correctamente desde PowerShell.
- Validación manual funcional: completada por el usuario desde dos terminales
  distintas en Windows. Se aplicaron las migraciones 1 y 2, se creó Hades, se
  añadieron variantes Steam y Nintendo Switch, se guardó interés 8 y se marcó
  únicamente Steam como poseído.
- Lectura final confirmada por el usuario: interés 8/10; Steam poseído con origen
  manual; Switch no poseído. La persistencia tras otra ejecución quedó validada.

## Límites actuales

No se han creado dependencias externas, bot, tokens, importaciones de Steam,
fuentes de precios, tareas programadas ni conexiones a servicios externos. Las
bases usadas por las pruebas y la demostración son locales e ignoradas por Git.

## Siguiente tarea propuesta

Conservar este punto como cierre de la capa 1. Antes de implementar la capa 2,
definir su primera subtarea, revisar las decisiones de seguridad del bot y
obtener autorización explícita del usuario. No se ha configurado ningún token ni
se ha contactado Telegram.
