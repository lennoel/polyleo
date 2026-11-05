"""Generación del informe PDF de un análisis individual (reportlab)."""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def generar_informe_pdf(resultado):
    """Devuelve bytes del PDF con los datos y las imágenes del análisis."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4
    y = alto - 2 * cm

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(2 * cm, y, "Informe de análisis de segmentación")
    y -= 0.8 * cm
    pdf.setFont("Helvetica", 9)
    pdf.drawString(2 * cm, y, "Asistente Inteligente - Deteccion y Segmentacion de Polipos (ViT)")
    y -= 0.8 * cm

    pdf.setFont("Helvetica", 11)
    lineas = [
        f"Archivo: {resultado.nombre_archivo}",
        f"Analisis N.: {resultado.analisis_id}",
        f"Fecha: {resultado.analisis.fecha.strftime('%d/%m/%Y %H:%M')}",
        f"Area segmentada: {resultado.area_segmentada:.2f} %",
        f"Tiempo de inferencia: {resultado.tiempo_inferencia_ms:.1f} ms",
        f"Estado: {resultado.get_estado_display()}",
    ]
    for linea in lineas:
        pdf.drawString(2 * cm, y, linea)
        y -= 0.55 * cm

    # Imágenes: original, máscara, overlay (si existen)
    from django.conf import settings
    import os
    imagenes = [
        ("Original", resultado.original),
        ("Mascara predicha", resultado.mascara),
        ("Segmentacion superpuesta", resultado.overlay),
    ]
    lado = 5.4 * cm
    for titulo, rel in imagenes:
        if not rel:
            continue
        ruta = os.path.join(str(settings.MEDIA_ROOT), rel.replace("resultados/", "resultados/", 1))
        # las rutas guardadas son relativas tipo 'resultados/<id>/archivo.png'
        ruta = settings.MEDIA_ROOT / rel
        if not os.path.isfile(ruta):
            continue
        if y - lado - 1 * cm < 2 * cm:
            pdf.showPage()
            y = alto - 2 * cm
        pdf.setFont("Helvetica-Bold", 10)
        y -= 0.6 * cm
        pdf.drawString(2 * cm, y, titulo)
        y -= 0.2 * cm
        img = ImageReader(str(ruta))
        iw, ih = img.getSize()
        escala = min(lado / iw, lado / ih)
        w, h = iw * escala, ih * escala
        pdf.drawImage(img, 2 * cm, y - h, width=w, height=h)
        y = y - h - 0.4 * cm

    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawString(
        2 * cm, 1.5 * cm,
        "Resultado generado por un modelo de IA. Es una prediccion visual, "
        "no un diagnostico medico.",
    )
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
