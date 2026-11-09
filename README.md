# PIXEL VAULT · v0.1.0 (MVP)

Gestor local de recursos creativos con **Python, PySide6 y SQLite**. El código se desarrolla aquí, en GitHub, con pruebas automatizadas.

## Funciones implementadas

- Importar uno o varios archivos, o carpetas recursivamente, en un hilo de trabajo.
- Registrar ruta, tamaño, fecha de modificación, SHA-256, extensión y dimensiones de imágenes compatibles.
- Organizar por categoría, descripción, etiquetas, favoritos y colecciones.
- Buscar por nombre, extensión, descripción o etiquetas; filtrar, ordenar y paginar.
- Previsualizar imágenes compatibles y reproducir algunos audios/vídeos (según códecs de Qt).
- Detectar duplicados **exactos** mediante hash SHA-256.
- Marcar referencias no disponibles al actualizar la biblioteca.
- Quitar registros de la biblioteca **sin borrar nunca los archivos originales**.

Los recursos se **referencian**, no se copian. La base de datos SQLite se guarda en la carpeta de datos de usuario de Qt. El programa no requiere cuenta ni servidor.

## Arranque en Windows

1. Instala **Python 3.10 o superior**.
2. Descarga este repositorio en ZIP desde GitHub y descomprímelo, o clónalo con Git.
3. Ejecuta `ejecutar-windows.bat`.
4. El programa te preguntará antes de instalar dependencias en el entorno virtual `.venv`.

Para crear un ejecutable en Windows, ejecuta después `crear-exe-windows.bat`. PyInstaller compilará `dist/PixelVault.exe` si se completa el proceso; **el EXE no viene incluido en el repositorio**.

## Arranque en Linux

Requiere Python 3.10+, soporte `venv` y bibliotecas gráficas Qt. Desde la raíz del repositorio:

```bash
bash ejecutar-linux.sh
```

Alternativa manual:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python launcher.py
```

## Pruebas

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

GitHub Actions ejecuta las pruebas de almacenamiento y compilación sintáctica sobre varias versiones de Python. **La ejecución real de la interfaz y los instaladores en Windows/Linux necesita validación en un equipo con escritorio**.

## Estructura

```text
src/pixel_vault/
    main.py       Entrada Qt
    ui.py         Interfaz, vistas y controles
    importer.py   Escaneo de archivos en segundo plano
    storage.py    SQLite, filtros, etiquetas y colecciones
    media.py      Clasificación, hash y dimensiones
tests/            Pruebas automatizadas
.github/workflows/tests.yml
launcher.py
ejecutar-windows.bat
ejecutar-linux.sh
crear-exe-windows.bat
```

## Pendiente

- Miniaturas persistentes y carga de miniaturas sin bloquear UI en bibliotecas grandes.
- Visor 3D, miniaturas de vídeos, mejores controles multimedia.
- Edición/renombrado y exportación de colecciones.
- Reconciliación de archivos movidos/renombrados.
- Importaciones incrementales más rápidas, progreso avanzado y manejo robusto de millones de archivos.
- Etiquetado por IA, similitud visual, sincronización.

**Advertencia:** no hay copias de seguridad automáticas de la base de datos. No almacenes en ella información que no quieras perder sin respaldos.

## Estado de validación

Implementación inicial publicada. Las pruebas CI se configuran en GitHub Actions; no se asegura que la interfaz funcione en todas las plataformas hasta probar una instalación real. Si encuentras un fallo, abre un Issue en este repositorio con el error y el sistema operativo.
