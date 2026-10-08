# Instrucciones para agentes

Este repositorio contiene el proyecto personal Ofertas personalizadas.

## Antes de modificar

1. Lee `PROJECT_SPEC.md` y `PROGRESS.md` completos.
2. Revisa la rama, los cambios pendientes y el último commit.
3. Identifica la capa activa y la próxima tarea autorizada.
4. Conserva cambios existentes y datos del usuario.

## Alcance

- Implementa solo la capa o subresultado solicitado.
- No implementes elementos de `BACKLOG.md` sin petición explícita.
- No añadas infraestructura o abstracciones para necesidades futuras.
- Detente al completar el alcance; no comiences otra capa por iniciativa propia.

## Reglas del dominio

- `null` significa sin puntuar; `0`, ignorado; `1-10`, interés explícito.
- Un juego ignorado no recibe avisos automáticos ni excepciones de precio.
- La nota explícita nunca se reemplaza por una predicción.
- La propiedad se registra por variante y no equivale a gusto.
- No unas productos, ediciones o variantes ambiguas solo por el título.
- No mezcles monedas, regiones, formatos, condiciones o ediciones en mínimos.
- Un fallo de red o fuente no equivale a precio cero, sin stock o no poseído.

## Entorno

- El desarrollo y las pruebas son nativos de Windows.
- El servidor futuro será otro notebook con Windows 11.
- Usa Python 3.12 como base inicial y documenta cualquier cambio de versión.
- Mantén comandos de uso y pruebas compatibles con PowerShell.
- No introduzcas dependencias exclusivas de Linux.

## Seguridad y datos

- No guardes tokens, `.env` reales, claves, bases personales ni logs privados en
  Git.
- Usa fixtures ficticios o sanitizados.
- No registres cuentas, compres servicios, envíes mensajes reales ni actives
  tareas programadas salvo autorización expresa de la tarea correspondiente.

## Verificación y continuidad

- Usa migraciones para cualquier cambio de datos persistidos.
- Ejecuta pruebas relacionadas con los riesgos del cambio.
- No declares validación manual que el usuario no realizó.
- No declares una integración real terminada solo porque sus fixtures funcionan.
- Actualiza `PROGRESS.md` con archivos modificados, comandos ejecutados,
  resultados reales, limitaciones y el siguiente paso acotado.
- Un commit local no implica autorización para hacer `push`.
