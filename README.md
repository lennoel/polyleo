# Asistente Inteligente de Segmentación de Pólipos — Sistema Web Local

Producto de la tesis: *"Asistente Inteligente para la Detección y Segmentación
de Pólipos en Colonoscopias mediante Visión Transformers"* (UMSA — Informática).

## Arquitectura (100 % local / offline)

```
Navegador (React + TypeScript, build servido por Django)
                        ↓  mismo origen
        Django (API REST + autenticación por sesiones)   http://localhost:8000
                        ↓
        PyTorch + ViT (modelo3.pth, CPU)  +  SQLite (db.sqlite3)
```

## Funcionalidades

| Módulo | Ruta | Descripción |
|---|---|---|
| Inicio | `/` | Presentación y navegación |
| Imagen individual | `/individual` | Analizar una imagen: umbral ajustable (0.1–0.9), transparencia de la máscara, vista previa, máscara/overlay/mapa de probabilidad, descarga de imágenes e **informe PDF** |
| Análisis por lotes | `/lotes` | Hasta 50 imágenes: progreso por archivo, estados individuales (errores no cancelan el lote), resumen, **ZIP** y **CSV** |
| Análisis de video | `/video` | MP4 (máx. 200 MB / 2 min): procesa 2 fps en segundo plano, progreso en vivo, video segmentado, **línea de tiempo de intervalos**, descarga |
| Historial | `/historial` | Análisis del usuario logueado: buscar por nombre/tipo, ver resultados, eliminar |
| Perfil | `/perfil` | Datos de la cuenta; el administrador además habilita/deshabilita usuarios |
| Acceso | `/acceso` | Registro e inicio de sesión (usuario o correo) |

El análisis individual funciona también sin sesión (sin guardar historial).
Lotes, video e historial requieren iniciar sesión.

## Uso

1. Doble clic en **`iniciar_backend.bat`** (levanta Django en el puerto 8000).
2. Abrir **http://localhost:8000** en el navegador.

Eso es todo: el backend sirve la API **y** el frontend compilado
(`frontend/dist`). No hace falta internet ni otro servidor.

### Cuentas iniciales (creadas para pruebas)

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin1234` | Administrador |
| `leonel` | `tesis2026` | Usuario registrado |

**Cambia estas contraseñas antes de presentar el sistema.**

### Modo desarrollo del frontend (opcional)

Si editas el frontend y quieres recarga en caliente:

```bat
iniciar_frontend.bat   REM Vite en http://localhost:5173
```

Para que los cambios queden en la versión servida por Django:

```bat
cd frontend
npm.cmd run build
```

## Modelo de IA

- Por defecto usa `../modelo3.pth` (Val Dice **0.9534**, época 27).
- Acepta tanto el checkpoint con metadatos (`model_state_dict`, `epoch`,
  `best_val_dice`) como un `state_dict` pelado.
- Para usar otro checkpoint sin tocar código:

```bat
set MODELO_POLIPOS_PATH=C:\ruta\otro_modelo.pth
iniciar_backend.bat
```

## API (resumen)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/salud/` | Estado del backend y del modelo |
| POST | `/api/auth/registro/` · `/api/auth/login/` · `/api/auth/logout/` | Autenticación |
| GET | `/api/auth/actual/` | Usuario actual |
| POST | `/api/segmentar/` | Imagen individual (`imagen`, `umbral`, `transparencia`) |
| POST | `/api/lotes/` → `/api/lotes/<id>/imagenes/` → `/api/lotes/<id>/finalizar/` | Flujo de lotes |
| GET | `/api/lotes/<id>/descargar.zip` · `/api/lotes/<id>/exportar.csv` | Exportaciones |
| GET | `/api/historial/?q=&tipo=&desde=&hasta=` | Historial del usuario |
| GET/DELETE | `/api/analisis/<id>/` | Detalle / eliminar |
| GET | `/api/analisis/<id>/informe.pdf?resultado=<rid>` | Informe PDF |
| POST | `/api/videos/` · GET `/api/videos/<id>/estado/` | Video y progreso |

## Datos almacenados

- `backend/db.sqlite3`: usuarios (hash de contraseñas de Django),
  `ANALISIS` y `RESULTADO` (cada análisis pertenece a su usuario).
- `backend/media/resultados/<id>/`: imágenes, máscaras, overlays,
  mapas de calor y videos generados.

## Roadmap (producto → documentar → iterar)

- [x] Fase 1: imágenes (seleccionar → analizar → máscara/overlay)
- [x] Fase 2: video + historial + usuarios + lotes + descargas
- [ ] Reentrenamiento con dataset ampliado y data augmentation
- [ ] Recuperación de contraseña por correo (fuera del alcance del prototipo local)
