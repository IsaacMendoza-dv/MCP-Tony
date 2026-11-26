# tony-estandares: servidor MCP de estándares

Servidor MCP de solo lectura que expone las reglas de estándares guardadas como archivos Markdown en `reglas/`. Este repositorio es el material de un ejercicio: poner el servidor en línea con Render y conectarlo a Kiro.

## Empieza aquí

Requisitos previos: una cuenta de GitHub, una cuenta de Render y Kiro.

Haz fork de este repositorio, clónalo y ábrelo en Kiro. Los pasos están en [docs/flujo-render.md](docs/flujo-render.md).

Pregúntale a tu Kiro:

```
Explícame el flujo de este repo de punta a punta
```

```
Guíame para desplegarlo en Render
```

```
¿Cómo compruebo que mi servicio está en línea?
```

Cuando termines la parte b del ejercicio:

```
Usa tony-estandares-remoto para listar las reglas
```

```
Usa tony-estandares-remoto para obtener la regla nombres-de-variables
```

```
Usa tony-estandares-remoto para buscar "commit" en las reglas
```

## Herramientas

- `listar_reglas`: sin parámetros; devuelve los nombres de las reglas.
- `obtener_regla(nombre)`: devuelve el contenido de una regla.
- `buscar_reglas(texto)`: devuelve las reglas y las líneas donde aparece el texto.

## Guía del ejercicio

[docs/flujo-render.md](docs/flujo-render.md)

Modo local, fuera del ejercicio: [docs/instalacion-local.md](docs/instalacion-local.md)
