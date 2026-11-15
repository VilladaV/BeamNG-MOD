# BeamNG-Mods

Galería web minimalista estilo Pinterest para visualizar tu colección local de mods de **BeamNG.drive** dividida en **Autos** y **Mapas**.

🌐 **Sitio en vivo (Firebase Hosting)**: https://beamng-mods-villadav-2026.web.app

## Características principales

- **Encabezado caricaturesco animado**: Título **BeamNG-Mods** con tipografía tipo cómic (`Rubik Bubbles` / `Fredoka`), contornos marcados, sombras 3D y animaciones fluidas letra por letra, acompañado de un selector minimalista entre **Autos** y **Mapas** y buscador rápido compacto.
- **Sección de Autos (381 mods)**: Cuadrícula masonry estilo Pinterest con proporciones variadas y fotografías del vehículo equivalente en la vida real (con respaldo automático a la miniatura del juego si falla la carga externa).
- **Sección de Mapas (127 mods)**:
  - **Mapa Mundial Cartoon interactivo sincronizado en la nube**: Panel desplegable dibujado con estética cómic/cartoon (océano con olas animadas, nubes flotantes, brújula, continentes coloridos con relieve 3D, zoom y paneo) donde puedes ubicar, arrastrar o inspeccionar cualquiera de los 127 mapas a tu gusto con sincronización en tiempo real mediante **Cloud Firestore** (`worldMap/sharedPins`) entre móvil, PC y otros dispositivos (más caché local en `localStorage`). Incluye botones rápidos para auto-ubicar los 65 mapas reales o esparcir creativamente los originales.
  - **Lugares del mundo real (65 mapas)**: Tarjeta dividida **50% fotografía real / 50% miniatura del juego** extraída directamente del archivo `.zip`.
  - **Mapas originales / ficticios (62 mapas)**: Tarjeta **100% con la miniatura del juego** extraída del archivo `.zip`.
  - **Inspección interna de `.zip`**: El generador de catálogo (`scripts/build_mods_catalog.py`) lee `levels/*/info.json` y `mod_info/*/info.json` dentro de cada archivo comprimido para identificar nombres y ubicaciones reales incluso cuando el nombre del `.zip` es abstracto.

## Comandos

```bash
# Instalar dependencias
npm install

# Desarrollo local
npm run dev

# Verificar tipos y compilar producción
npm run build

# Linter (oxlint)
npm run lint

# Previsualizar build de producción
npm run preview
```

### Regenerar catálogo de mods locales

```bash
python scripts/build_mods_catalog.py
```

Lee `C:\Users\johan\AppData\Local\BeamNG\BeamNG.drive\current\mods` y `mods\repo`, actualiza `src/data/modsCatalog.json` y comprime las miniaturas locales en `public/thumbnails/`.

## Despliegue en Firebase

```bash
npm run build
npx -y firebase-tools@latest deploy --only firestore,hosting --project beamng-mods-villadav-2026
```

## Flujo Gitflow

- `main`: rama de producción etiquetada (`v1.0.0`, `v1.1.0`, `v1.2.0`, `v1.3.0`).
- `develop`: rama de integración continua.
- `feature/*`: ramas por módulo (`feature/project-scaffold`, `feature/mods-data-pipeline`, `feature/cartoon-animated-header`, `feature/cars-pinterest-gallery`, `feature/maps-split-gallery`, `feature/cartoon-world-map`, `feature/firebase-cloud-deploy`) integradas con `--no-ff`.
- `release/*`: ramas de estabilización y preparación (`release/v1.0.0`, `release/v1.1.0`, `release/v1.2.0`, `release/v1.3.0`).
