"""
Endpoints de la API del asistente inteligente.

Autenticación (sesiones Django; contraseñas hasheadas por defecto):
  POST /api/auth/registro/     {username, email, password}
  POST /api/auth/login/        {usuario, contrasena}   (username o email)
  POST /api/auth/logout/
  GET  /api/auth/actual/
  GET  /api/auth/usuarios/            (solo administrador)
  POST /api/auth/usuarios/<id>/estado/ (solo administrador)

Análisis individual:
  POST /api/segmentar/         (imagen, umbral, transparencia)
  GET  /api/analisis/<id>/informe.pdf

Lotes (requieren sesión):
  POST /api/lotes/
  POST /api/lotes/<id>/imagenes/
  POST /api/lotes/<id>/finalizar/
  GET  /api/lotes/<id>/descargar.zip
  GET  /api/lotes/<id>/exportar.csv

Historial (requiere sesión; solo los propios):
  GET    /api/historial/?q=&tipo=&desde=&hasta=
  GET    /api/analisis/<id>/
  DELETE /api/analisis/<id>/

Videos (requieren sesión):
  POST /api/videos/
  GET  /api/videos/<id>/estado/

Nota: API local de prototipo; csrf_exempt porque el frontend se sirve
desde el mismo origen (Django sirve el build de React) o desde Vite dev.
"""
import csv
import json
import uuid
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

from . import videos as servicio_video
from .informe import generar_informe_pdf
from .ml import servicio
from .models import Analisis, Resultado

EXT_IMAGEN = {".jpg", ".jpeg", ".png"}
MAX_IMAGEN_MB = 10
MAX_VIDEO_MB = 200


# ------------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------------
def requiere_login(vista):
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"ok": False, "error": "Se requiere iniciar sesión"}, status=401
            )
        return vista(request, *args, **kwargs)

    return envoltura


def solo_admin(vista):
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse(
                {"ok": False, "error": "Solo el administrador"}, status=403
            )
        return vista(request, *args, **kwargs)

    return envoltura


def cuerpo_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


def validar_imagen(archivo):
    """Devuelve (imagen_pil, error). Valida formato, tamaño e integridad."""
    if archivo.size > MAX_IMAGEN_MB * 1024 * 1024:
        return None, f"Supera el máximo de {MAX_IMAGEN_MB} MB"
    ext = Path(archivo.name).suffix.lower()
    if ext not in EXT_IMAGEN:
        return None, f"Formato no permitido ({ext}); use JPG o PNG"
    try:
        imagen = Image.open(archivo).convert("RGB")
        imagen.load()
    except Exception:
        return None, "El archivo está dañado o no es una imagen válida"
    return imagen, None


def guardar_resultados(carpeta, imagen, mascara, overlay, calor):
    carpeta.mkdir(parents=True, exist_ok=True)
    imagen.save(carpeta / "original.png")
    mascara.save(carpeta / "mascara.png")
    overlay.save(carpeta / "overlay.png")
    calor.save(carpeta / "calor.png")


def urls_de(carpeta):
    base = f"{settings.MEDIA_URL}resultados/{carpeta.name}"
    return {
        "original": f"resultados/{carpeta.name}/original.png",
        "mascara": f"resultados/{carpeta.name}/mascara.png",
        "overlay": f"resultados/{carpeta.name}/overlay.png",
        "calor": f"resultados/{carpeta.name}/calor.png",
    }, {
        "original_url": f"{base}/original.png",
        "mascara_url": f"{base}/mascara.png",
        "overlay_url": f"{base}/overlay.png",
        "calor_url": f"{base}/calor.png",
    }


def procesar_imagen(archivo, analisis, umbral=0.5, transparencia=0.43):
    """Procesa una imagen y crea su Resultado asociado al análisis."""
    if analisis.pk is None:  # el padre debe existir antes del resultado
        analisis.save()
    resultado = Resultado(analisis=analisis, nombre_archivo=archivo.name)
    imagen, error = validar_imagen(archivo)
    if error:
        resultado.estado = "error"
        resultado.error = error
        resultado.save()
        return resultado

    carpeta = settings.MEDIA_ROOT / "resultados" / uuid.uuid4().hex[:12]
    try:
        mascara, overlay, calor, stats = servicio.segmentar(
            imagen, umbral=umbral, transparencia=transparencia
        )
    except Exception as exc:  # noqa: BLE001
        resultado.estado = "error"
        resultado.error = str(exc)
        resultado.save()
        return resultado

    guardar_resultados(carpeta, imagen, mascara, overlay, calor)
    rutas, _ = urls_de(carpeta)
    for campo, ruta in rutas.items():
        setattr(resultado, campo, ruta)
    resultado.area_segmentada = stats["porcentaje_polipo"]
    resultado.tiempo_inferencia_ms = stats["tiempo_inferencia_ms"]
    resultado.estado = (
        "procesada" if stats["porcentaje_polipo"] > 0 else "sin_regiones"
    )
    resultado.save()
    return resultado


def res_json(r):
    base = settings.MEDIA_URL
    return {
        "id": r.id,
        "analisis_id": r.analisis_id,
        "nombre_archivo": r.nombre_archivo,
        "area_segmentada": r.area_segmentada,
        "tiempo_inferencia_ms": r.tiempo_inferencia_ms,
        "estado": r.estado,
        "error": r.error,
        "original_url": base + r.original if r.original else None,
        "mascara_url": base + r.mascara if r.mascara else None,
        "overlay_url": base + r.overlay if r.overlay else None,
        "calor_url": base + r.calor if r.calor else None,
        "informe_url": f"/api/analisis/{r.analisis_id}/informe.pdf?resultado={r.id}",
    }


def analisis_json(a, con_resultados=False):
    datos = {
        "id": a.id,
        "tipo": a.tipo,
        "fecha": a.fecha.isoformat(),
        "estado": a.estado,
        "progreso": a.progreso,
        "tiempo_procesamiento": a.tiempo_procesamiento,
        "detalle": a.detalle,
        "usuario": a.usuario.username if a.usuario else None,
    }
    if con_resultados:
        datos["resultados"] = [res_json(r) for r in a.resultados.all()]
    return datos


def obtener_analisis(request, analisis_id):
    """Análisis propio del usuario (o None si no existe / no es suyo)."""
    try:
        return Analisis.objects.get(pk=analisis_id, usuario=request.user)
    except (Analisis.DoesNotExist, ValueError):
        return None


# ------------------------------------------------------------------
# Autenticación
# ------------------------------------------------------------------
@csrf_exempt
def registro(request):
    if request.method != "POST":
        return JsonResponse({"error": "Usa método POST"}, status=405)
    datos = cuerpo_json(request)
    username = (datos.get("username") or "").strip()
    email = (datos.get("email") or "").strip()
    password = datos.get("password") or ""

    if not username or not email or not password:
        return JsonResponse({"ok": False, "error": "Completa todos los campos"}, status=400)
    if len(password) < 6:
        return JsonResponse(
            {"ok": False, "error": "La contraseña debe tener al menos 6 caracteres"},
            status=400,
        )
    if User.objects.filter(username=username).exists():
        return JsonResponse({"ok": False, "error": "El usuario ya existe"}, status=400)
    if User.objects.filter(email=email).exists():
        return JsonResponse({"ok": False, "error": "El correo ya está registrado"}, status=400)

    usuario = User.objects.create_user(
        username=username, email=email, password=password
    )
    login(request, usuario)
    return JsonResponse({"ok": True, "usuario": usuario_json(usuario)})


def usuario_json(u):
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "es_admin": u.is_staff,
        "fecha_registro": u.date_joined.isoformat(),
    }


@csrf_exempt
def iniciar_sesion(request):
    if request.method != "POST":
        return JsonResponse({"error": "Usa método POST"}, status=405)
    datos = cuerpo_json(request)
    nombre = (datos.get("usuario") or "").strip()
    contrasena = datos.get("contrasena") or ""

    usuario = None
    if "@" in nombre:  # permite iniciar sesión con correo
        try:
            nombre = User.objects.get(email=nombre).username
        except User.DoesNotExist:
            pass
    usuario = authenticate(request, username=nombre, password=contrasena)
    if usuario is None:
        return JsonResponse(
            {"ok": False, "error": "Usuario o contraseña incorrectos"}, status=401
        )
    if not usuario.is_active:
        return JsonResponse({"ok": False, "error": "Cuenta deshabilitada"}, status=403)
    login(request, usuario)
    return JsonResponse({"ok": True, "usuario": usuario_json(usuario)})


@csrf_exempt
def cerrar_sesion(request):
    logout(request)
    return JsonResponse({"ok": True})


def usuario_actual(request):
    if request.user.is_authenticated:
        return JsonResponse({"ok": True, "usuario": usuario_json(request.user)})
    return JsonResponse({"ok": True, "usuario": None})


@requiere_login
@solo_admin
def lista_usuarios(request):
    datos = [
        {**usuario_json(u), "activo": u.is_active}
        for u in User.objects.order_by("id")
    ]
    return JsonResponse({"ok": True, "usuarios": datos})


@csrf_exempt
@requiere_login
@solo_admin
def cambiar_estado_usuario(request, usuario_id):
    try:
        usuario = User.objects.get(pk=usuario_id)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "No existe"}, status=404)
    if usuario == request.user:
        return JsonResponse(
            {"ok": False, "error": "No puedes cambiar tu propia cuenta"}, status=400
        )
    usuario.is_active = not usuario.is_active
    usuario.save()
    return JsonResponse({"ok": True, "activo": usuario.is_active})


# ------------------------------------------------------------------
# Salud del sistema
# ------------------------------------------------------------------
def salud(request):
    try:
        info = servicio.info_modelo()
        return JsonResponse({"ok": True, "modelo": info})
    except FileNotFoundError:
        return JsonResponse(
            {"ok": False, "error": f"No se encontró el modelo en {settings.MODELO_PATH}"},
            status=500,
        )
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({"ok": False, "error": str(exc)}, status=500)


# ------------------------------------------------------------------
# Análisis individual
# ------------------------------------------------------------------
@csrf_exempt
def segmentar_imagen(request):
    if request.method != "POST":
        return JsonResponse({"error": "Usa método POST"}, status=405)

    archivo = request.FILES.get("imagen")
    if archivo is None:
        return JsonResponse({"error": "Falta el campo 'imagen'"}, status=400)

    umbral = float(request.POST.get("umbral", 0.5))
    transparencia = float(request.POST.get("transparencia", 0.43))

    analisis = Analisis(
        usuario=request.user if request.user.is_authenticated else None,
        tipo="imagen",
        estado="completado",
    )
    resultado = procesar_imagen(archivo, analisis, umbral, transparencia)
    analisis.tiempo_procesamiento = resultado.tiempo_inferencia_ms
    analisis.save()

    respuesta = {"ok": resultado.estado != "error", "analisis_id": analisis.id}
    respuesta.update(res_json(resultado))
    if resultado.estado == "error":
        return JsonResponse(respuesta, status=400)
    return JsonResponse(respuesta)


def informe_pdf(request, analisis_id):
    """Descarga el informe PDF de un análisis."""
    resultado_id = request.GET.get("resultado")
    try:
        resultado = Resultado.objects.get(
            pk=resultado_id, analisis_id=analisis_id
        )
    except (Resultado.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"error": "No encontrado"}, status=404)
    if resultado.analisis.usuario and (
        not request.user.is_authenticated
        or resultado.analisis.usuario != request.user
    ):
        return JsonResponse({"error": "Sin permiso"}, status=403)
    contenido = generar_informe_pdf(resultado)
    respuesta = HttpResponse(contenido, content_type="application/pdf")
    nombre = Path(resultado.nombre_archivo).stem
    respuesta["Content-Disposition"] = f'attachment; filename="informe_{nombre}.pdf"'
    return respuesta


# ------------------------------------------------------------------
# Lotes
# ------------------------------------------------------------------
@csrf_exempt
@requiere_login
def crear_lote(request):
    if request.method != "POST":
        return JsonResponse({"error": "Usa método POST"}, status=405)
    analisis = Analisis.objects.create(
        usuario=request.user, tipo="lote", estado="procesando", progreso=0
    )
    return JsonResponse({"ok": True, "id": analisis.id})


@csrf_exempt
@requiere_login
def agregar_imagen_lote(request, lote_id):
    if request.method != "POST":
        return JsonResponse({"error": "Usa método POST"}, status=405)
    analisis = obtener_analisis(request, lote_id)
    if analisis is None or analisis.tipo != "lote":
        return JsonResponse({"error": "Lote no encontrado"}, status=404)
    if analisis.resultados.count() >= 50:
        return JsonResponse({"error": "Máximo 50 imágenes por lote"}, status=400)

    archivo = request.FILES.get("imagen")
    if archivo is None:
        return JsonResponse({"error": "Falta el campo 'imagen'"}, status=400)
    umbral = float(request.POST.get("umbral", 0.5))
    transparencia = float(request.POST.get("transparencia", 0.43))
    resultado = procesar_imagen(archivo, analisis, umbral, transparencia)
    return JsonResponse({"ok": resultado.estado != "error", **res_json(resultado)})


@csrf_exempt
@requiere_login
def finalizar_lote(request, lote_id):
    analisis = obtener_analisis(request, lote_id)
    if analisis is None:
        return JsonResponse({"error": "Lote no encontrado"}, status=404)
    resultados = analisis.resultados.all()
    total = resultados.count()
    con_regiones = sum(1 for r in resultados if r.area_segmentada > 0)
    errores = sum(1 for r in resultados if r.estado == "error")
    analisis.estado = "completado"
    analisis.progreso = 100
    analisis.tiempo_procesamiento = sum(r.tiempo_inferencia_ms for r in resultados)
    analisis.detalle = {
        "total": total,
        "con_regiones": con_regiones,
        "sin_regiones": total - con_regiones - errores,
        "errores": errores,
    }
    analisis.save()
    return JsonResponse({"ok": True, **analisis_json(analisis, con_resultados=True)})


@requiere_login
def descargar_lote_zip(request, lote_id):
    analisis = obtener_analisis(request, lote_id)
    if analisis is None:
        return JsonResponse({"error": "Lote no encontrado"}, status=404)
    ruta_zip = settings.MEDIA_ROOT / "resultados" / f"lote_{lote_id}.zip"
    with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in analisis.resultados.all():
            if r.estado == "error":
                continue
            for campo in ("mascara", "overlay"):
                rel = getattr(r, campo)
                if rel:
                    ruta = settings.MEDIA_ROOT / rel
                    if ruta.is_file():
                        zf.write(
                            ruta,
                            f"{Path(r.nombre_archivo).stem}_{campo}.png",
                        )
    return FileResponse(
        open(ruta_zip, "rb"),
        as_attachment=True,
        filename=f"lote_{lote_id}_resultados.zip",
    )


@requiere_login
def exportar_lote_csv(request, lote_id):
    analisis = obtener_analisis(request, lote_id)
    if analisis is None:
        return JsonResponse({"error": "Lote no encontrado"}, status=404)
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = (
        f'attachment; filename="lote_{lote_id}_resultados.csv"'
    )
    escritor = csv.writer(respuesta)
    escritor.writerow(["Imagen", "Área segmentada (%)", "Tiempo (ms)", "Estado"])
    for r in analisis.resultados.all():
        escritor.writerow(
            [r.nombre_archivo, r.area_segmentada, r.tiempo_inferencia_ms, r.estado]
        )
    return respuesta


# ------------------------------------------------------------------
# Historial
# ------------------------------------------------------------------
@requiere_login
def historial(request):
    analisis = Analisis.objects.filter(usuario=request.user).order_by("-fecha")
    texto = request.GET.get("q", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    desde = request.GET.get("desde", "").strip()
    hasta = request.GET.get("hasta", "").strip()
    if tipo:
        analisis = analisis.filter(tipo=tipo)
    if desde:
        analisis = analisis.filter(fecha__date__gte=desde)
    if hasta:
        analisis = analisis.filter(fecha__date__lte=hasta)
    if texto:
        analisis = analisis.filter(resultados__nombre_archivo__icontains=texto)
    datos = [analisis_json(a) for a in analisis.distinct()[:200]]
    return JsonResponse({"ok": True, "analisis": datos})


@requiere_login
def detalle_analisis(request, analisis_id):
    analisis = obtener_analisis(request, analisis_id)
    if analisis is None:
        return JsonResponse({"error": "No encontrado"}, status=404)
    return JsonResponse({"ok": True, **analisis_json(analisis, con_resultados=True)})


@csrf_exempt
@requiere_login
def eliminar_analisis(request, analisis_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Usa método DELETE"}, status=405)
    analisis = obtener_analisis(request, analisis_id)
    if analisis is None:
        return JsonResponse({"error": "No encontrado"}, status=404)
    analisis.delete()
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------
# Videos
# ------------------------------------------------------------------
@csrf_exempt
@requiere_login
def subir_video(request):
    if request.method != "POST":
        return JsonResponse({"error": "Usa método POST"}, status=405)
    archivo = request.FILES.get("video")
    if archivo is None:
        return JsonResponse({"error": "Falta el campo 'video'"}, status=400)
    if Path(archivo.name).suffix.lower() != ".mp4":
        return JsonResponse({"error": "Solo se admite formato MP4"}, status=400)
    if archivo.size > MAX_VIDEO_MB * 1024 * 1024:
        return JsonResponse({"error": f"Supera el máximo de {MAX_VIDEO_MB} MB"}, status=400)

    carpeta = settings.MEDIA_ROOT / "resultados" / uuid.uuid4().hex[:12]
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "video_original.mp4"
    with open(ruta, "wb") as salida:
        for bloque in archivo.chunks():
            salida.write(bloque)

    analisis = Analisis.objects.create(
        usuario=request.user, tipo="video", estado="procesando", progreso=0
    )
    Resultado.objects.create(
        analisis=analisis,
        nombre_archivo=archivo.name,
        original=f"resultados/{carpeta.name}/video_original.mp4",
    )
    servicio_video.procesar_video_en_segundo_plano(analisis.id, ruta)
    return JsonResponse({"ok": True, "id": analisis.id})


@requiere_login
def estado_video(request, video_id):
    analisis = obtener_analisis(request, video_id)
    if analisis is None or analisis.tipo != "video":
        return JsonResponse({"error": "No encontrado"}, status=404)
    return JsonResponse({"ok": True, **analisis_json(analisis)})
