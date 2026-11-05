from django.urls import path

from . import views

urlpatterns = [
    path("salud/", views.salud, name="salud"),
    # Autenticación
    path("auth/registro/", views.registro),
    path("auth/login/", views.iniciar_sesion),
    path("auth/logout/", views.cerrar_sesion),
    path("auth/actual/", views.usuario_actual),
    path("auth/usuarios/", views.lista_usuarios),
    path("auth/usuarios/<int:usuario_id>/estado/", views.cambiar_estado_usuario),
    # Análisis individual
    path("segmentar/", views.segmentar_imagen, name="segmentar"),
    path("analisis/<int:analisis_id>/informe.pdf", views.informe_pdf),
    path("analisis/<int:analisis_id>/", views.detalle_analisis),
    # Lotes
    path("lotes/", views.crear_lote),
    path("lotes/<int:lote_id>/imagenes/", views.agregar_imagen_lote),
    path("lotes/<int:lote_id>/finalizar/", views.finalizar_lote),
    path("lotes/<int:lote_id>/descargar.zip", views.descargar_lote_zip),
    path("lotes/<int:lote_id>/exportar.csv", views.exportar_lote_csv),
    # Historial
    path("historial/", views.historial),
    # Videos
    path("videos/", views.subir_video),
    path("videos/<int:video_id>/estado/", views.estado_video),
]
