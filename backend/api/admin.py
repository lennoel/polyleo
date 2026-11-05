from django.contrib import admin

from .models import Analisis, Resultado


@admin.register(Analisis)
class AnalisisAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "tipo", "fecha", "estado", "progreso")
    list_filter = ("tipo", "estado", "fecha")


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = ("id", "analisis", "nombre_archivo", "area_segmentada", "estado")
    list_filter = ("estado",)
