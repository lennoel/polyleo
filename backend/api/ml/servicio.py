"""
Servicio de inferencia del modelo ViT de segmentación de pólipos.

- Carga el checkpoint UNA sola vez (singleton con bloqueo de hilo).
- Funciona 100% offline en CPU.
- Acepta tanto el formato de prueba (state_dict pelado) como el
  formato del entrenamiento corregido (dict con "model_state_dict",
  "img_size", "best_val_dice", "epoch", ...).
"""
import threading
import time

import numpy as np
import torch
from django.conf import settings
from PIL import Image
from torchvision import transforms

from .vit_seg import ViTSegmentation

_lock = threading.Lock()
_modelo = None
_info = {}

# Mismo preprocesamiento usado en el entrenamiento
_transform = transforms.Compose(
    [
        transforms.Resize((settings.MODELO_IMG_SIZE, settings.MODELO_IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        ),
    ]
)


def cargar_modelo():
    """Carga perezosa (lazy) y segura en hilos del modelo."""
    global _modelo, _info
    if _modelo is None:
        with _lock:
            if _modelo is None:
                modelo = ViTSegmentation(
                    img_size=settings.MODELO_IMG_SIZE,
                    patch_size=settings.MODELO_PATCH_SIZE,
                    embed_dim=settings.MODELO_EMBED_DIM,
                )
                checkpoint = torch.load(settings.MODELO_PATH, map_location="cpu")

                # Formato corregido (dict con metadatos) o state_dict directo
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    state = checkpoint["model_state_dict"]
                    _info = {
                        "formato": "checkpoint_con_metadata",
                        "epoca": checkpoint.get("epoch"),
                        "best_val_dice": checkpoint.get("best_val_dice"),
                    }
                else:
                    state = checkpoint
                    _info = {"formato": "state_dict (prueba)"}

                modelo.load_state_dict(state)
                modelo.eval()
                _modelo = modelo
                _info["archivo"] = str(settings.MODELO_PATH)
                _info["dispositivo"] = "cpu"
    return _modelo


def info_modelo():
    """Datos del modelo cargado (para el endpoint de salud)."""
    cargar_modelo()
    return dict(_info)


def _mapa_calor(probs):
    """Convierte probabilidades [0,1] en una imagen RGB tipo 'jet'.

    Azul = baja probabilidad, rojo = alta probabilidad.
    """
    p = np.clip(probs, 0.0, 1.0)
    r = np.clip(1.5 - np.abs(4.0 * p - 3.0), 0, 1)
    g = np.clip(1.5 - np.abs(4.0 * p - 2.0), 0, 1)
    b = np.clip(1.5 - np.abs(4.0 * p - 1.0), 0, 1)
    rgb = (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)
    return Image.fromarray(rgb, mode="RGB")


def segmentar(imagen_pil, umbral=0.5, transparencia=0.43):
    """Ejecuta la segmentación sobre una imagen PIL.

    umbral: 0.1-0.9, probabilidad mínima para marcar un píxel como pólipo.
    transparencia: 0.0-1.0, opacidad del tinte rojo en el overlay.

    Devuelve (mascara_pil, overlay_pil, calor_pil, estadisticas).
    """
    modelo = cargar_modelo()

    if imagen_pil.mode != "RGB":
        imagen_pil = imagen_pil.convert("RGB")

    umbral = min(max(float(umbral), 0.1), 0.9)
    transparencia = min(max(float(transparencia), 0.0), 1.0)

    inicio = time.perf_counter()

    tensor = _transform(imagen_pil).unsqueeze(0)  # [1, 3, 224, 224]
    with torch.no_grad():
        logits = modelo(tensor)
        probs = torch.sigmoid(logits)[0, 0].cpu().numpy()  # [224, 224]
        mascara_bin = (probs > umbral).astype(np.float32)

    tiempo_ms = (time.perf_counter() - inicio) * 1000.0

    # Máscara 224x224 -> tamaño original de la imagen
    mascara_np = (mascara_bin * 255).astype(np.uint8)
    mascara_pil = Image.fromarray(mascara_np, mode="L").resize(
        imagen_pil.size, Image.NEAREST
    )

    # Overlay: pólipo resaltado en rojo semitransparente sobre la original
    overlay = imagen_pil.copy().convert("RGBA")
    tinte = Image.new("RGBA", overlay.size, (255, 0, 0, int(255 * transparencia)))
    overlay.paste(tinte, (0, 0), mascara_pil)
    overlay = overlay.convert("RGB")

    # Mapa de calor de probabilidades (útil para depurar y para la tesis)
    calor_pil = _mapa_calor(probs).resize(imagen_pil.size, Image.BILINEAR)

    porcentaje = float((mascara_np > 0).sum()) / mascara_np.size * 100.0
    estadisticas = {
        "porcentaje_polipo": round(porcentaje, 2),
        "tiempo_inferencia_ms": round(tiempo_ms, 1),
        "prob_maxima": round(float(probs.max()), 4),
        "prob_media": round(float(probs.mean()), 4),
        "umbral": umbral,
    }
    return mascara_pil, overlay, calor_pil, estadisticas
