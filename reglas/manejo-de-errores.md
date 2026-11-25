# Manejo de errores

Esta regla define cómo detectar, registrar y comunicar errores.

## Principios

- Captura solo las excepciones que sabes manejar; no uses `except Exception` vacío.
- Nunca ignores un error en silencio.
- Falla temprano: valida las entradas antes de procesarlas.

## Mensajes de error

- Redacta los mensajes en español, claros y accionables.
- Indica qué falló y cómo corregirlo.
- No expongas rutas internas, contraseñas ni datos personales.

## Registro

- Registra el error con su contexto (operación, identificador, hora).
- Usa niveles de registro coherentes: `error` para fallos y `warning` para situaciones recuperables.

## Ejemplo

- Correcto: "La regla 'estilo' no existe. Revisa el nombre con listar_reglas."
- Incorrecto: "Error."
