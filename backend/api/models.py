"""
Modelos de datos del asistente.

USUARIO se resuelve con django.contrib.auth.User (contraseñas hasheadas
por Django). ANALISIS y RESULTADO siguen la propuesta del documento
de especificaciones del proyecto.
"""
from django.contrib.auth.models import User
from django.db import models


class Analisis(models.Model):
    TIPOS = (("imagen", "Imagen"), ("lote", "Lote"), ("video", "Video"))
    ESTADOS = (
        ("procesando", "Procesando"),
        ("completado", "Completado"),
        ("error", "Error"),
    )

    usuario = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE,
        related_name="analisis",
    )
    tipo = models.CharField(max_length=10, choices=TIPOS, default="imagen")
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default="completado")
    tiempo_procesamiento = models.FloatField(default=0.0)  # milisegundos
    progreso = models.FloatField(default=100.0)  # 0-100 (videos)
    detalle = models.JSONField(default=dict, blank=True)  # resumen lote / info video

    def __str__(self):
        return f"Analisis #{self.pk} ({self.tipo})"


class Resultado(models.Model):
    ESTADOS = (
        ("procesada", "Procesada"),
        ("sin_regiones", "Sin regiones segmentadas"),
        ("error", "Error"),
    )

    analisis = models.ForeignKey(
        Analisis, related_name="resultados", on_delete=models.CASCADE
    )
    nombre_archivo = models.CharField(max_length=255)
    area_segmentada = models.FloatField(default=0.0)  # porcentaje
    tiempo_inferencia_ms = models.FloatField(default=0.0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="procesada")
    error = models.TextField(blank=True, default="")

    # Rutas relativas a MEDIA_URL (vacías si hubo error)
    original = models.CharField(max_length=500, blank=True, default="")
    mascara = models.CharField(max_length=500, blank=True, default="")
    overlay = models.CharField(max_length=500, blank=True, default="")
    calor = models.CharField(max_length=500, blank=True, default="")

    def __str__(self):
        return f"{self.nombre_archivo} ({self.area_segmentada:.2f}%)"
