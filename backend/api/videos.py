"""
Procesamiento de videos de colonoscopia (en segundo plano).

- Extrae fotogramas con OpenCV.
- Analiza N fotogramas por segundo con el modelo ViT (configurable).
- Los fotogramas no analizados se copian sin modificar.
- Genera un video MP4 con las regiones resaltadas y una línea de
  tiempo de intervalos con regiones segmentadas.
- El progreso se guarda en el registro Analisis (campo progreso).
"""
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from django.conf import settings
from PIL import Image

from .ml import servicio

FPS_ANALISIS = 2          # fotogramas analizados por segundo de video
MAX_DURACION_SEG = 120    # límite del prototipo (segundos)


def procesar_video_en_segundo_plano(analisis_id, ruta_video):
    hilo = threading.Thread(
        target=_procesar, args=(analisis_id, ruta_video), daemon=True
    )
    hilo.start()


def _procesar(analisis_id, ruta_video):
    from .models import Analisis  # import tardío (evita ciclos)

    analisis = Analisis.objects.get(pk=analisis_id)
    inicio_total = time.perf_counter()
    try:
        cap = cv2.VideoCapture(str(ruta_video))
        if not cap.isOpened():
            raise RuntimeError("No se pudo abrir el video")

        fps_original = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duracion = total_frames / fps_original if fps_original else 0
        if duracion > MAX_DURACION_SEG:
            raise RuntimeError(
                f"El video excede el límite del prototipo ({MAX_DURACION_SEG} s)"
            )

        paso = max(int(round(fps_original / FPS_ANALISIS)), 1)
        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        carpeta = Path(ruta_video).parent
        ruta_salida = carpeta / "video_segmentado.mp4"
        writer = cv2.VideoWriter(
            str(ruta_salida),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps_original,
            (ancho, alto),
        )

        detecciones = []  # (segundo, area_segmentada)
        analizados = 0
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            segundo = idx / fps_original

            if idx % paso == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                imagen = Image.fromarray(rgb)
                mascara, overlay, _, stats = servicio.segmentar(imagen)
                area = stats["porcentaje_polipo"]
                detecciones.append((round(segundo, 2), area))
                analizados += 1
                if area > 0:
                    frame = cv2.cvtColor(np.array(overlay), cv2.COLOR_RGB2BGR)
                analisis.progreso = round(idx / max(total_frames, 1) * 100, 1)
                analisis.save(update_fields=["progreso"])

            writer.write(frame)
            idx += 1

        cap.release()
        writer.release()

        # Intervalos continuos con regiones segmentadas
        intervalos = _intervalos(detecciones, paso / fps_original)

        analisis.estado = "completado"
        analisis.progreso = 100.0
        analisis.tiempo_procesamiento = (time.perf_counter() - inicio_total) * 1000
        analisis.detalle = {
            "duracion_seg": round(duracion, 2),
            "fps_original": round(fps_original, 2),
            "fps_analisis": FPS_ANALISIS,
            "total_frames": total_frames,
            "frames_analizados": analizados,
            "intervalos": intervalos,
            "video_url": f"{settings.MEDIA_URL}resultados/{carpeta.name}/video_segmentado.mp4",
            "original_url": f"{settings.MEDIA_URL}resultados/{carpeta.name}/{Path(ruta_video).name}",
        }
        analisis.save()
    except Exception as exc:  # noqa: BLE001
        analisis.estado = "error"
        analisis.detalle = {"error": str(exc)}
        analisis.save()


def _intervalos(detecciones, paso_seg):
    """Agrupa detecciones consecutivas con área > 0 en intervalos."""
    intervalos = []
    inicio = None
    ultimo = None
    for segundo, area in detecciones:
        if area > 0:
            if inicio is None:
                inicio = segundo
            ultimo = segundo
        else:
            if inicio is not None:
                intervalos.append([inicio, round(ultimo + paso_seg, 2)])
                inicio = None
    if inicio is not None:
        intervalos.append([inicio, round(ultimo + paso_seg, 2)])
    return intervalos
