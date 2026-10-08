# Progreso

## Estado actual

- Última capa cerrada: **2 - Telegram de preferencias**.
- Próxima capa: **3**, todavía no iniciada.
- Estado: implementación, pruebas automáticas e integración manual real de la
  capa 2 completas.
- Rama inspeccionada: `main`.
- Punto de partida: commit inicial `e12c2b6`.
- Punto de control funcional de capas 0-1: commit local `f5f4c51`.
- Código de producto: núcleo local, CLI y bot de Telegram disponibles.

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

## Trabajo realizado en la capa 2

- Se añadió la migración 003 para offset de Telegram y callbacks procesados.
- Se implementó un cliente HTTPS de la Bot API con la biblioteca estándar.
- Se implementó long polling con offset persistente y reanudación tras reinicio.
- Se limitó el bot a un único ID de usuario y chat privado.
- Se añadieron `/start`, `/help` y `/search texto`.
- Las tarjetas permiten puntuar 1-10, ignorar, reactivar y cambiar propiedad por
  variante reutilizando los servicios del núcleo.
- Los callbacks son acciones idempotentes, no interruptores; repetir un ID no
  duplica el cambio.
- Si el guardado funciona y la edición del mensaje falla, el dato se conserva y
  el usuario recibe una indicación para volver a buscar.
- Se añadieron `bot check`, `bot identify` y `bot run` a la CLI.
- Token e ID autorizado se reciben por variables de entorno. Las credenciales
  permanecieron únicamente en el entorno local y no se guardaron en el proyecto.

### Verificación de capa 2

- `python -m compileall -q src tests`: correcto.
- `python -m unittest discover -s tests -v`: 29 pruebas correctas.
- Casos cubiertos: autorización, búsqueda, botones, callback repetido o
  malformado, propiedad por variante, offset, reinicio, fallo de edición y
  respuestas HTTP de Telegram simuladas.
- La migración 003 se aplicó sobre la base local real; Hades conservó interés 8,
  Steam poseído y Switch no poseído.
- El usuario validó el token con `bot check`, identificó su cuenta con
  `bot identify` y ejecutó el bot real restringido a su ID, sin compartir ni
  persistir esas credenciales en el repositorio.
- `/start` y `/search Hades` respondieron correctamente en Telegram y mostraron
  interés 8/10, Steam poseído y Switch no poseído.
- Los botones se validaron de extremo a extremo: puntuación 9, ignorar,
  reactivar a sin puntuar, marcar y desmarcar propiedad únicamente en la variante
  de Switch, y restaurar el interés a 8.
- Después de detener y reiniciar el proceso, una nueva búsqueda conservó el
  interés y la propiedad esperados.
- En PowerShell, `Ctrl+C` puede tardar aproximadamente 30 segundos en detener el
  proceso mientras finaliza la espera de long polling. El usuario lo registró
  como observación y se acepta por ahora sin modificar el intervalo.

## Límites actuales

No se han creado dependencias de Python externas, importaciones de Steam, fuentes
de precios, tareas programadas ni otras integraciones. El bot de Telegram ya
existe y fue validado, pero su token y el ID autorizado no se guardan en Git ni
en la base de datos. Las bases locales están ignoradas por Git.

## Siguiente tarea propuesta

Conservar el cierre validado de la capa 2. Antes de implementar la capa 3, se
debe revisar su alcance y resolver las decisiones pendientes relacionadas con
Steam. No iniciar esa capa sin la siguiente autorización explícita del usuario.
