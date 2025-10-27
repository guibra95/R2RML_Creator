# R2RML Creator

Genera mapeos R2RML de calidad a partir de bases de datos MySQL mediante una interfaz web sencilla. El proyecto está enfocado únicamente en la generación de archivos R2RML, sin lógica de creación de ontologías.

## Características
- Conexión a bases de datos MySQL.
- Selección de tablas y configuración de columnas.
- Asignación de URIs para diccionario, localdb y datos.
- Generación y descarga de archivos R2RML (datos y diccionario).
- Interfaz web intuitiva y lista para usar en Docker o local.

## Requisitos
- Python 3.8+
- Docker (opcional, recomendado para despliegue rápido)
- MySQL accesible desde la red

## Uso rápido con Docker
1. Construye la imagen:
   ```sh
   docker build -t r2rml_app .
   ```
2. Ejecuta el contenedor:
   ```sh
   docker run -p 5000:5000 r2rml_app
   ```
3. Accede a la interfaz en tu navegador:
   - http://localhost:5000

## Uso local (sin Docker)
1. Instala las dependencias:
   ```sh
   pip install -r requirements.txt
   ```
2. Ejecuta la app:
   ```sh
   python app.py
   ```
3. Accede a la interfaz en tu navegador:
   - http://localhost:5000

## Estructura del proyecto
- `app.py` — Servidor Flask principal
- `src/` — Lógica de conexión MySQL y generación R2RML
- `templates/` — Interfaz web (HTML)
- `output/` — Archivos R2RML generados

## Notas
- Asegúrate de que tu base de datos MySQL sea accesible desde el contenedor Docker si usas Docker (puedes usar `host.docker.internal` como host en Windows).

## Licencia
Sin licencia: este proyecto es de uso libre para cualquier persona.
