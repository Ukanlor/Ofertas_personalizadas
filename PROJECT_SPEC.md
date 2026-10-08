# Especificación del proyecto

## 1. Objetivo

Construir un sistema personal que rastree ofertas de videojuegos, conserve un
historial útil y avise por Telegram de acuerdo con los intereses del usuario.
Debe cubrir:

- PC: juegos que se activen en Steam, con región y condiciones verificadas.
- Nintendo Switch y Switch 2: juegos físicos disponibles en Chile.
- Recomendaciones graduales de juegos conocidos y desconocidos, siempre con una
  explicación comprensible y sin reemplazar la valoración explícita del usuario.

La prioridad es obtener avisos fiables y útiles. La cantidad de tiendas y la
sofisticación del recomendador son secundarias.

## 2. Alcance inicial

El sistema será para un solo usuario, con un proceso principal y persistencia
local en SQLite. Telegram será la primera interfaz bidireccional.

No forman parte del alcance inicial:

- compra automática;
- servicio público o multiusuario;
- panel web o aplicación móvil;
- catálogo mundial exhaustivo;
- microservicios, colas externas o infraestructura en la nube;
- modelos pagados o llamadas a un LLM como requisito de funcionamiento.

## 3. Entornos y compatibilidad

El desarrollo y las pruebas se realizan directamente en el entorno Windows
actual de Codex. La ejecución permanente se hará más adelante en otro notebook
con Windows 11. Ese equipo se actualizará o preparará cuando el proyecto llegue
a la etapa que necesite operación continua.

Decisiones actuales:

- Lenguaje base: Python.
- Versión inicial de desarrollo: Python 3.12.
- Persistencia: SQLite local con migraciones versionadas.
- Terminal de referencia: PowerShell.
- Zona horaria de presentación y reglas horarias: `America/Santiago`.
- Fechas almacenadas: UTC.

La versión y las dependencias del notebook servidor se verificarán antes de su
puesta en marcha. No se asumirán rutas POSIX, Bash, servicios systemd ni otras
dependencias exclusivas de Linux.

## 4. Modelo conceptual

### Juego

Identidad editorial de un título. Conserva el título canónico, alias y, cuando
corresponda, características utilizadas para recomendar.

### Variante

Producto comparable de un juego: plataforma, edición, formato, región, estado y
DRM o sistema de activación. Un juego de Steam y su edición física para Switch
son variantes distintas.

### Publicación y observación

Una publicación identifica el producto ofrecido por una tienda. Una observación
registra precio, moneda, stock, envío, fecha y procedencia. Un fallo de una fuente
no equivale a precio cero, falta de stock ni desaparición del producto.

### Preferencia y propiedad

El interés visible utiliza una única escala canónica:

- `null`: el usuario todavía no ha puntuado el juego;
- `0`: el usuario lo ha ignorado y se bloquean avisos y sugerencias automáticas;
- `1` a `10`: interés explícito.

No se añadirá un segundo indicador de ignorado que pueda contradecir esa escala.
Reactivar un juego será una acción explícita que cambie el `0` a `null` o a una
nueva puntuación elegida por el usuario.

La propiedad se registra por variante. Poseer un juego en Steam no bloquea por
sí solo una oportunidad de la versión física para Switch. Propiedad, interés de
compra y gusto son conceptos distintos; una importación nunca debe borrar una
decisión manual.

## 5. Invariantes

1. Sin puntuar no equivale a ignorado, e ignorado tiene precedencia sobre
   objetivos de precio y oportunidades excepcionales.
2. La valoración explícita del usuario prevalece sobre cualquier predicción.
3. La propiedad se asocia a una variante y no demuestra gusto o desagrado.
4. Toda oferta pertenece a una variante y una publicación identificables.
5. No se mezclan monedas, regiones, ediciones, formatos o condiciones al calcular
   referencias de precio.
6. Los estados desconocidos se conservan como desconocidos; no se convierten en
   cero, falso o agotado.
7. Una capa solo se cierra cuando su resultado, pruebas y validación pendiente o
   realizada quedan registrados.
8. Tiempo alto, bajo o ausente en Steam no equivale a gusto, desagrado ni falta
   de experiencia: el usuario puede haber jugado en otra plataforma.
9. Las exclusiones de importación son reglas locales reversibles y no generan
   automáticamente una valoración negativa.

## 6. Arquitectura prevista

- **Dominio:** juego, variante, dinero, preferencia, propiedad y observación.
- **Servicios:** altas, cambios, importaciones, evaluación y preparación de
  alertas.
- **Persistencia:** consultas, transacciones, índices y migraciones SQLite.
- **Adaptadores:** Steam, fuentes de precios y Telegram.
- **Recomendador:** candidatos explicables sin modificar notas explícitas.
- **Motor de alertas:** elegibilidad, prioridad, deduplicación y registro.

El dominio y los servicios no dependerán de Telegram, HTML de tiendas ni una API
concreta. Los adaptadores obtienen o presentan datos, pero no deciden las reglas
centrales.

Para la capa 2, Telegram usa la Bot API oficial por HTTPS y long polling. El bot
solo procesa mensajes privados del ID numérico autorizado. El token se recibe
mediante variable de entorno y nunca se persiste. Los offsets y callbacks ya
procesados sí se guardan en SQLite para soportar reinicios y evitar cambios
duplicados. Webhooks y servidores públicos quedan fuera de esta capa.

## 7. Capas de desarrollo

0. **Especificación:** documentación, decisiones, límites y estado verificable.
1. **Núcleo de datos:** CLI, SQLite, juegos, variantes, preferencias y propiedad.
2. **Telegram de preferencias:** buscar, puntuar, ignorar, reactivar y marcar
   propiedad.
3. **Steam personal:** importar biblioteca y actividad sin alterar decisiones
   manuales.
4. **Recomendador v1:** candidatos y razones mediante un método sencillo.
5. **Motor de precios:** evaluar históricos ficticios y evidencia comparable.
6. **Primera fuente PC:** incorporar una única fuente regional real.
7. **Alertas personalizadas:** combinar oportunidad, preferencias y límites.
8. **Primera tienda Switch:** integrar una tienda chilena y validar productos.
9. **Comparación multi-tienda:** comparar publicaciones equivalentes.
10. **Operación en Windows 11:** arranque, diagnóstico, logs, backups y
    recuperación en el notebook servidor.
11. **Evolución aplazada:** mejoras que requieran evidencia y petición explícita.

La compatibilidad con Windows se verifica desde la capa 1. La capa 10 no es una
migración desde Linux; es la estabilización operativa en el notebook servidor.

## 8. Método de trabajo

Cada capa o subresultado sigue este ciclo:

1. Revisar el repositorio y el estado documentado.
2. Acordar un resultado pequeño y verificable, sus exclusiones y bloqueos.
3. Implementar únicamente ese alcance.
4. Ejecutar pruebas reproducibles sin depender de claves o redes reales cuando
   no sean necesarias.
5. Mostrar una demostración breve y separar pruebas automáticas de validación
   manual.
6. Corregir defectos y registrar decisiones, comandos y resultados reales.
7. Detenerse antes de ampliar el alcance a la siguiente capa.

## 9. Definición de terminado

Una capa requiere un entregable funcional, comprobaciones relevantes ejecutadas,
una demostración reproducible, conservación de datos anteriores y documentación
actualizada. Si falta una prueba de integración o validación manual, debe quedar
indicada explícitamente y la capa no se presentará como completamente validada.

## 10. Decisiones pendientes por etapa

- Capa 4: diferencia práctica entre gusto e interés de compra; fuente de metadata
  y catálogo candidato.
- Capa 5: histórico mínimo, frescura y fórmula de calidad de oferta.
- Capa 6: fuente PC y tipos de tiendas o claves aceptados.
- Capa 7: horario, cuota, cooldown y excepciones de alertas.
- Capa 8: primera tienda física, formatos aceptados, nuevo/usado y despacho.
- Capa 10: forma de arranque, cadencias, recursos y preparación exacta del
  notebook servidor con Windows 11.

Estas decisiones se resolverán cuando bloqueen su capa; no es necesario fijarlas
todas antes de comenzar el núcleo de datos.
