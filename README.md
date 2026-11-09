# PIXEL VAULT · v0.1.0

**Digital Asset Manager & Creative Library** — aplicación de escritorio en español, construida con Python, PySide6, Pillow y SQLite. Compatible en principio con Windows 10/11 y distribuciones Linux con escritorio y librerías Qt disponibles.

## Primer arranque

**Windows**

1. Instala **Python 3.10 o superior**, activando la casilla *Add Python to PATH* si la instalación lo ofrece.
2. Descomprime este proyecto en una carpeta normal (no intentes ejecutar dentro del ZIP).
3. Ejecuta `ejecutar-windows.bat`. Te **preguntará antes** de crear el entorno `.venv` e instalar las dependencias de `requirements.txt`.
4. Tras la instalación, se abrirá PIXEL VAULT. Las siguientes veces usa el mismo archivo.

**Linux**

1. Instala Python 3.10+ con `venv` y sus librerías de escritorio. En Debian/Ubuntu, normalmente `sudo apt install python3 python3-venv python3-pip libxcb-cursor0` (si faltan estos paquetes). En Linux del aula con Python 3.9 o inferior, probablemente necesitarás usar una versión de Python más reciente sin modificar el Python del sistema.
2. En la carpeta del proyecto, ejecuta `./ejecutar-linux.sh`. Confirma la instalación cuando lo solicite.
3. También puedes hacer manualmente: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python launcher.py`.

**Crear EXE para Windows**

En **Windows**, una vez realizado el primer arranque, ejecuta `crear-exe-windows.bat`. Te preguntará antes de instalar PyInstaller. Si finaliza bien, encontrarás `dist/PixelVault.exe`. El EXE resultante no debería necesitar Python en el equipo donde se ejecute; los códecs multimedia y bibliotecas del sistema pueden variar. Debe compilarse **en Windows**: no se puede generar de forma fiable un EXE Windows desde un Linux corriente.

## Qué hace hoy

- Importar archivos o carpetas completas (incluidos subdirectorios), arrastrar y soltar.
- Clasificar automáticamente por extensión y nombre de carpeta. Reasignar categorías libremente.
- Indexar nombre, ruta, tamaño, fecha, dimensiones de imagen, extensión y SHA-256.
- Buscar por nombre, extensión, descripción o etiquetas, filtrar por categoría, favoritos, duplicados, no disponibles y colecciones.
- Ordenar, mostrar de 160 en 160 para no crear decenas de miles de widgets a la vez.
- Ver miniaturas de imágenes, detalles y previsualizar audio y vídeo con el motor multimedia de Qt y los códecs que haya en el sistema.
- Editar etiquetas/descripción, marcar favoritos, crear y gestionar colecciones.
- Menú contextual de recursos: abrir, ver carpeta original, cambiar favorito, quitar de biblioteca.
- Menú contextual de colecciones (clic derecho): renombrar, exportar manifiesto JSON y eliminar la colección.
- Estadísticas por categoría, espacio referenciado, grupos de duplicados y archivos desaparecidos.
- Actualización de referencias: comprueba si los originales siguen ahí y vuelve a calcular metadatos/hash si cambiaron.
- Progreso de importación con cancelación y lectura en un hilo de fondo.

## Seguridad y privacidad

- **Modo vinculado**: no copia ni mueve los archivos originales. Conserva la ruta absoluta del archivo de origen.
- **No borra archivos físicos**: “Quitar de biblioteca” solo elimina el registro en SQLite, tras confirmar.
- Importar otra vez la misma ruta no duplica el registro. Archivos distintos con igual hash se conservan como referencias diferentes para poder detectar duplicados.
- La aplicación no utiliza servidores ni cuentas online. Los archivos y metadatos se mantienen en tu equipo.
- Las miniaturas son copias reducidas que se almacenan en la carpeta de datos de usuario, sin modificar el original.
- Un archivo renombrado o movido puede aparecer como nuevo al importarlo y como desaparecido en la ruta antigua; la reconciliación automática de movimientos no está implementada aún.
- No hay copias de seguridad automáticas: haz una copia del archivo `pixelvault.db` con la aplicación cerrada para conservar las colecciones y etiquetas.

## Ubicación de la base de datos

Se usa el directorio `AppDataLocation` de Qt para PIXEL VAULT (en Windows suele estar en `AppData/Roaming/PixelVault` o equivalente; en Linux en `~/.local/share/PixelVault`). Se muestra la ruta exacta en **Acerca de**. Contiene `pixelvault.db` y `thumbnails/`.

## Arquitectura de la versión 0.1.0

```text
pixel-vault/
├── assets/                       # Icono PNG/ICO
├── src/pixel_vault/
│   ├── main.py                   # Configuración y entrada
│   ├── ui.py                     # Ventana Qt, previsualización, colecciones
│   ├── storage.py                # SQLite y consultas
│   ├── importer.py               # Hilo de indexación y actualización
│   └── media.py                  # Clasificador, hash, miniaturas, metadatos
├── tests/test_storage.py
├── launcher.py
├── requirements.txt
├── ejecutar-windows.bat
├── ejecutar-linux.sh
└── crear-exe-windows.bat
```

## No implementado todavía

- Visor interactivo 3D, miniaturas de vídeos (sí existe reproducción en los formatos compatibles).
- Búsqueda visual, etiquetado por IA o reconocimiento de colores.
- Copia física de archivos al exportar colecciones; por ahora la exportación es un JSON con rutas/metadatos.
- Comparación de imágenes *parecidas*: los duplicados son **exactos** por SHA-256.
- Sincronización en la nube, cambio masivo de rutas o deshacer cambios de clasificación.
- Gestión avanzada de errores/permisos a escala de millones de archivos.

## Pruebas

Sin instalar PySide6, se pueden ejecutar las pruebas del almacenamiento:

```bash
python -m unittest discover -s tests -v
```

**Nota de verificación:** en el entorno donde se generó el código se validaron la sintaxis Python y las pruebas de SQLite. No se pudo ejecutar manualmente una sesión de escritorio Qt por no disponer de PySide6 descargable en ese entorno; prueba el primer arranque en tu ordenador antes de dar por validada la interfaz.