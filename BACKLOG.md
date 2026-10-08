# Backlog

Este archivo contiene ideas deliberadamente aplazadas. No son requisitos de la
capa activa ni deben implementarse sin una petición explícita y una condición de
entrada cumplida.

## Recomendación avanzada

- Ampliar TF-IDF o representación textual cuando exista metadata limpia y una
  evaluación básica reproducible.
- Probar embeddings locales solo después de medir calidad, memoria y tiempo en el
  hardware real.
- Evaluar regresión o learning-to-rank cuando haya suficientes etiquetas
  comparables y un conjunto de evaluación separado.
- Incorporar aprendizaje activo cuando la interacción de calibración ya sea
  cómoda y el dataset estable.

## Servicios de IA

- Considerar OpenRouter para una tarea limitada únicamente si la versión sin IA
  deja un problema medible.
- Antes de activarlo: acordar presupuesto, modelo, caché, límites, validación y
  comportamiento alternativo sin servicio.
- El objetivo histórico de USD 5-10 al mes es contexto, no autorización de gasto.

## Experiencia de usuario

- Acción "Más como esto" con una semántica distinta de cambiar el interés.
- Gráficos o exploración del historial de precios en Telegram.
- Preferencias diferenciadas por plataforma o formato.
- Otras interfaces además de Telegram.

## Cobertura y operación

- Más fuentes y tiendas después de estabilizar el núcleo y añadirlas de una en
  una.
- Servicios en la nube únicamente si aparece una necesidad operativa concreta.
- Panel web, aplicación móvil, multiusuario y catálogo mundial exhaustivo quedan
  fuera del MVP.

## Condición general de entrada

Cada elemento necesita una solicitud explícita, un problema observado, una
medida de éxito y una comparación con la solución sencilla existente.
