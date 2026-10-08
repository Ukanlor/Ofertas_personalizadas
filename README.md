# Ofertas personalizadas

Proyecto personal para descubrir ofertas relevantes de videojuegos y recibirlas
por Telegram. El alcance inicial incluye juegos de PC que se activen en Steam y
juegos físicos de Nintendo Switch y Switch 2 disponibles en Chile.

El sistema conservará preferencias, propiedad por plataforma o variante e
historial de precios. Las recomendaciones empezarán con reglas explicables y
datos explícitos del usuario; OpenRouter, modelos avanzados y nuevas interfaces
no forman parte del MVP.

## Estado actual

La **capa 1: núcleo de datos** está completa y validada. La **capa 2: Telegram
de preferencias** tiene su implementación offline terminada; falta conectarla y
validarla con el bot real del usuario. No existen importación de Steam, consulta
de precios ni alertas espontáneas. El estado verificable y el siguiente trabajo
autorizado se mantienen en [`PROGRESS.md`](PROGRESS.md).

## Entornos previstos

- Desarrollo y pruebas: el entorno Windows actual de Codex.
- Operación futura: otro notebook con Windows 11, que se preparará cuando el
  proyecto alcance la etapa operativa correspondiente.
- Base técnica propuesta: Python 3.12 y SQLite local.

El proyecto no depende de Linux. Desde la primera implementación, las rutas,
comandos y pruebas deben funcionar de forma nativa en Windows.

## Documentación

- [`PROJECT_SPEC.md`](PROJECT_SPEC.md): alcance, reglas, arquitectura y capas.
- [`PROGRESS.md`](PROGRESS.md): estado real, comprobaciones y siguiente paso.
- [`BACKLOG.md`](BACKLOG.md): ideas aplazadas y condiciones para retomarlas.
- [`AGENTS.md`](AGENTS.md): límites de trabajo para Codex y otros agentes.

Las credenciales, tokens, bases personales y registros privados no se guardarán
en Git. Los ejemplos y fixtures que se incorporen más adelante deberán ser
ficticios o estar sanitizados.

## Preparación en Windows

Se requiere Python 3.12. Desde PowerShell, en la raíz del repositorio:

```powershell
.\scripts\bootstrap.cmd "C:\ruta\a\python.exe"
.\scripts\ofertas.cmd db init
```

La capa 1 usa únicamente la biblioteca estándar. El entorno virtual se crea sin
`pip` porque todavía no hay paquetes externos que instalar. La base personal
predeterminada se guarda en `data/ofertas.db`, una ruta ignorada por Git.
Los lanzadores `.cmd` funcionan aunque la política de ejecución de PowerShell
bloquee scripts `.ps1`; no es necesario cambiar esa política del sistema.

## Uso actual de la CLI

```powershell
.\scripts\ofertas.cmd game add "Hades"
.\scripts\ofertas.cmd variant add 1 --platform pc --format digital --region cl --drm steam
.\scripts\ofertas.cmd variant add 1 --platform "Nintendo Switch" --format cartucho --region cl --condition nuevo
.\scripts\ofertas.cmd interest set 1 8
.\scripts\ofertas.cmd ignore 1
.\scripts\ofertas.cmd reactivate 1
.\scripts\ofertas.cmd owned set 1
.\scripts\ofertas.cmd game show 1
.\scripts\ofertas.cmd game search "Hades"
```

El identificador de cada juego o variante aparece al crearlo. `interest set 0`
equivale a ignorar; `reactivate` vuelve a dejar el juego sin puntuar.

## Pruebas

```powershell
$env:PYTHONPATH = "$PWD\src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Telegram: configuración local

El adaptador usa la [Bot API oficial de Telegram](https://core.telegram.org/bots/api)
mediante long polling. Solo acepta mensajes privados del ID numérico configurado.
El token no se guarda en Git, SQLite ni archivos del proyecto.

1. Crea el bot mediante [`@BotFather`](https://t.me/BotFather) y abre su chat.
2. En PowerShell, carga el token sin escribirlo en el historial:

```powershell
$tokenSeguro = Read-Host "Token de Telegram" -AsSecureString
$env:TELEGRAM_BOT_TOKEN = [System.Net.NetworkCredential]::new("", $tokenSeguro).Password
Remove-Variable tokenSeguro
.\scripts\ofertas.cmd bot check
```

3. Envía `/start` al bot desde Telegram y ejecuta:

```powershell
.\scripts\ofertas.cmd bot identify
```

4. Copia únicamente tu ID numérico mostrado y configura el acceso:

```powershell
$env:TELEGRAM_ALLOWED_USER_ID = "TU_ID_NUMERICO"
.\scripts\ofertas.cmd bot run
```

El proceso funciona hasta presionar `Ctrl+C`. Actualmente reconoce `/start`,
`/help` y `/search texto`; las tarjetas permiten puntuar, ignorar, reactivar y
marcar o desmarcar propiedad por variante.
