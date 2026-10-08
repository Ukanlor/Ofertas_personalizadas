# Ofertas personalizadas

Proyecto personal para descubrir ofertas relevantes de videojuegos y recibirlas
por Telegram. El alcance inicial incluye juegos de PC que se activen en Steam y
juegos físicos de Nintendo Switch y Switch 2 disponibles en Chile.

El sistema conservará preferencias, propiedad por plataforma o variante e
historial de precios. Las recomendaciones empezarán con reglas explicables y
datos explícitos del usuario; OpenRouter, modelos avanzados y nuevas interfaces
no forman parte del MVP.

## Estado actual

Las **capas 1, 2 y 3** están completas y validadas: el núcleo de datos funciona
de forma local, el bot de Telegram administra preferencias y la biblioteca
personal de Steam importa propiedad y actividad. La **capa 4** todavía no ha
comenzado. No existen consulta de precios ni alertas espontáneas. El estado
verificable y el siguiente trabajo autorizado se mantienen en
[`PROGRESS.md`](PROGRESS.md).

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
marcar o desmarcar propiedad por variante. En Windows, `Ctrl+C` puede tardar
aproximadamente 30 segundos en devolver el control a PowerShell mientras termina
la espera activa de long polling; se considera un comportamiento conocido y
aceptable por ahora.

## Steam: configuración local

La capa 3 usa `IPlayerService/GetOwnedGames` de la
[Web API oficial de Steam](https://partner.steamgames.com/doc/webapi/iplayerservice?language=english).
Solo importa títulos cuyo tiempo total sea mayor que cero. La clave y el SteamID
se reciben por variables de entorno; la clave no se guarda en Git ni SQLite.

En PowerShell, carga la clave sin escribirla en el historial:

```powershell
$steamKeySeguro = Read-Host "Clave Web API de Steam" -AsSecureString
$env:STEAM_WEB_API_KEY = [System.Net.NetworkCredential]::new("", $steamKeySeguro).Password
Remove-Variable steamKeySeguro
$env:STEAM_USER_ID = "TU_STEAM_ID_NUMERICO"
```

Primero comprueba la conexión sin modificar el catálogo:

```powershell
.\scripts\ofertas.cmd steam check
```

Para revisar los títulos y sus horas sin escribir en la base:

```powershell
.\scripts\ofertas.cmd steam preview
```

Las exclusiones personales se guardan solamente en la base local:

```powershell
.\scripts\ofertas.cmd steam exclude add APP_ID "Nombre" --reason "Motivo"
.\scripts\ofertas.cmd steam exclude list
.\scripts\ofertas.cmd steam exclude remove APP_ID
```

Después de revisar la vista previa, la importación explícita se ejecuta con:

```powershell
.\scripts\ofertas.cmd steam import
```

La importación añade propiedad y actividad, pero no asigna puntuaciones ni
reemplaza una propiedad manual. La disponibilidad histórica de juegos prestados
por Steam Families se comprobará con la respuesta real de la cuenta. El tiempo
jugado tampoco se interpreta como una medida de gusto: una ausencia o pocas
horas pueden deberse a que el juego se utilizó en otra plataforma.
