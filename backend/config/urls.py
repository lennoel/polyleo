from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def spa(request, ruta=""):
    """Sirve el index.html del frontend React (aplicación de una sola página)."""
    index = settings.STATICFILES_DIRS[0] / "index.html"
    if index.is_file():
        return HttpResponse(index.read_text(encoding="utf-8"))
    return HttpResponse(
        "Frontend no compilado. Ejecuta 'npm run build' en frontend/ "
        "o usa el servidor Vite en el puerto 5173.",
        status=503,
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Archivos estáticos del build de React (assets)
    urlpatterns += static(
        "/assets/", document_root=settings.STATICFILES_DIRS[0] / "assets"
    )

# Cualquier otra ruta -> SPA (React Router se encarga en el cliente)
urlpatterns.append(path("<path:ruta>", spa))
urlpatterns.append(path("", spa))
