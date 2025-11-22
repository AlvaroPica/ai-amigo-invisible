# Secret Santa Django App

Aplicación web para gestionar juegos de Amigo Invisible.

## Requisitos

- Python 3.x
- `uv` (gestor de paquetes)

## Instalación

1. Clonar el repositorio.
2. Crear entorno virtual e instalar dependencias:
   ```bash
   uv sync
   ```

## Configuración

1. Aplicar migraciones:
   ```bash
   uv run python manage.py migrate
   ```

2. Crear un superusuario (opcional, para admin):
   ```bash
   uv run python manage.py createsuperuser
   ```

3. Configuración de Email (SMTP):
   Por defecto, la aplicación usa el backend de consola (`django.core.mail.backends.console.EmailBackend`), por lo que los correos se mostrarán en la terminal donde corre el servidor.
   
   Para configurar un SMTP real (ej. Gmail), edita `secretsanta_project/settings.py` y descomenta/configura las variables `EMAIL_BACKEND`, `EMAIL_HOST`, etc.

## Ejecución

1. Iniciar el servidor de desarrollo:
   ```bash
   uv run python manage.py runserver
   ```

2. Acceder a `http://127.0.0.1:8000/`.

## Uso

1. **Registro/Login**: Crea una cuenta o inicia sesión.
2. **Crear Juego**: Define un nombre y descripción.
3. **Añadir Jugadores**: Añade participantes (nombre, email). Mínimo 3.
4. **Restricciones**: Define excepciones (quién no puede regalar a quién).
5. **Dependientes**: Marca jugadores como "dependientes" si necesitan un proxy.
6. **Sorteo**: Cuando estés listo, lanza el sorteo.
7. **Enviar Emails**: Envía los resultados a los participantes.
8. **Errores**: Si algún email falla, puedes corregirlo y reintentar desde la interfaz.

## Tests

Para ejecutar los tests unitarios:
```bash
uv run python manage.py test secretsanta.tests
```
