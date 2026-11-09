# ◒ PIXEL VAULT — v0.2.0

**Digital Asset Manager & Creative Library.** Un archivo creativo local con estética editorial: ciruela profundo, marfil, coral y melocotón, en lugar de la interfaz de consola azul tradicional.

## Instalar en Windows (recomendado)

Abre **Actions → Windows Installer → última ejecución correcta**, descarga el artifact **PIXEL-VAULT-Installer-Windows-v0.2.0**, descomprime el ZIP de GitHub y ejecuta `PIXEL-VAULT-Setup-0.2.0.exe`.

El instalador ofrece:
- icono propio y aplicación en menú Inicio;
- acceso directo en el escritorio (activado por defecto);
- opción de abrir PIXEL VAULT al acabar;
- desinstalador desde Windows.

**No necesitas instalar Python para usar la versión instalada.** El instalador no lleva firma de código: Windows puede mostrar una advertencia SmartScreen. No hay actualizaciones automáticas todavía.

También existe un artifact portable independiente, para quien prefiera no instalar.

## Qué hay nuevo

- **Galería** con miniaturas de imágenes reales y tarjetas dibujadas para código, documentos, audio, vídeo, 3D y otros formatos; no quedan archivos como texto sobre espacios vacíos.
- **Vista lista** con columnas de nombre, tipo, categoría, tamaño, fecha y ruta, como un explorador.
- Diseño editorial claro, sin imitar a DEVDOCK: marfil, berenjena, coral, melocotón y lavanda.
- Menú contextual con acciones rápidas, multiselección, favoritos y etiquetas en lote.
- Búsqueda por nombre/etiquetas/descripción, filtros por categoría y extensión, ordenación y paginación.
- Colecciones, favoritos, detección de hashes SHA-256, referencias desaparecidas y estadísticas.
- Miniaturas de imágenes cacheadas en los datos locales de usuario.
- **Integración real con DEVDOCK**: consulta sus proyectos en una base SQLite de solo lectura, filtra los archivos ya indexados por proyecto y permite importar un proyecto a petición del usuario. No modifica los datos de DEVDOCK.

Las tarjetas de vídeo y 3D tienen representaciones visuales por formato; la generación de fotogramas o la visualización 3D interactiva siguen pendientes.

## DEVDOCK: conexión segura

PIXEL VAULT intenta localizar `devdock.sqlite` en el directorio de datos de usuario de Electron (Windows: `%APPDATA%/devdock/devdock.sqlite`; Linux: `~/.config/devdock/devdock.sqlite`). Si no lo encuentra, usa **Conectar DEVDOCK** y selecciona la base de datos. Puede ser necesario abrir primero DEVDOCK para que exista.

Al seleccionar un proyecto, verás sus recursos ya indexados; con **Importar proyecto** indexarás su carpeta con confirmación expresa. Esta integración lee el esquema actual de DEVDOCK (`projects` con `root_path`). No escribe sobre la otra aplicación, no ejecuta comandos de DEVDOCK y no borra archivos.

## Desarrollo local

Requiere Python 3.10+. En Windows ejecuta `ejecutar-windows.bat`. En Linux usa:

```bash
bash ejecutar-linux.sh
```

El primer arranque pide permiso antes de crear un entorno virtual e instalar dependencias.

Para ejecutar las pruebas:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Si quieres compilar manualmente un ejecutable, usa `crear-exe-windows.bat`. El instalador se genera de forma reproducible con GitHub Actions, PyInstaller e Inno Setup, usando `scripts/create_icon.py`.

## Privacidad y precauciones

- **No mueve ni elimina los archivos originales.** «Quitar de biblioteca» solo elimina registros SQLite.
- Hashes y miniaturas se calculan localmente; no se sube tu biblioteca a la nube.
- La base de datos se guarda en el directorio de datos local de PIXEL VAULT. **Haz copia de seguridad** si tus etiquetas y colecciones son importantes.
- Importar directorios enormes todavía puede llevar tiempo y la generación inicial de miniaturas puede ralentizar el desplazamiento. Las mejoras de indexación y renderizado asincrónicos siguen pendientes.

## Próximas mejoras

Miniaturas reales para vídeo, mejor tratamiento de archivos Unreal/Blender, arrastrar y soltar, asociaciones de proyecto persistentes, selección avanzada, exportación de colecciones, búsqueda visual y previsualización 3D. No se consideran implementadas todavía.

## Estado

Fuente publicada en `main`, pruebas de SQLite e integración disponibles en GitHub Actions. El funcionamiento visual del instalador debe comprobarse en un equipo Windows antes de considerar la versión estable.
