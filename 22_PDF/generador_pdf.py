from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def generar_pdf(tipo, documento, detalles):
    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    ancho, alto = A4

    pdf.setTitle(
        f"{tipo} {documento['numero']}"
    )

    pdf.setFont("Helvetica-Bold", 20)

    titulo = "COTIZACIÓN" if tipo == "cotizacion" else "VENTA"

    pdf.drawString(
        20 * mm,
        alto - 25 * mm,
        titulo
    )

    pdf.setFont("Helvetica", 10)

    pdf.drawString(
        20 * mm,
        alto - 35 * mm,
        f"Número: {documento['numero']}"
    )

    fecha = str(
        documento.get("created_at", "")
    )[:10]

    pdf.drawString(
        20 * mm,
        alto - 42 * mm,
        f"Fecha: {fecha}"
    )

    cliente = documento.get("clientes") or {}

    pdf.drawString(
        20 * mm,
        alto - 55 * mm,
        f"Cliente: {cliente.get('nombre', 'Sin cliente')}"
    )

    pdf.drawString(
        20 * mm,
        alto - 62 * mm,
        f"Teléfono: {cliente.get('telefono', '')}"
    )

    y = alto - 80 * mm

    pdf.setFont("Helvetica-Bold", 9)

    pdf.drawString(20 * mm, y, "PRODUCTO")
    pdf.drawString(85 * mm, y, "CANT.")
    pdf.drawString(110 * mm, y, "TIPO")
    pdf.drawString(135 * mm, y, "PRECIO")
    pdf.drawString(165 * mm, y, "TOTAL")

    y -= 7 * mm

    pdf.setFont("Helvetica", 8)

    for item in detalles:
        nombre = item["nombre_producto"]

        if len(nombre) > 30:
            nombre = nombre[:30]

        pdf.drawString(
            20 * mm,
            y,
            nombre
        )

        pdf.drawRightString(
            100 * mm,
            y,
            f"{float(item['cantidad']):.2f}"
        )

        pdf.drawString(
            110 * mm,
            y,
            item["tipo"]
        )

        pdf.drawRightString(
            155 * mm,
            y,
            f"{float(item['precio']):.2f}"
        )

        pdf.drawRightString(
            190 * mm,
            y,
            f"{float(item['total']):.2f}"
        )

        y -= 7 * mm

        if y < 30 * mm:
            pdf.showPage()
            y = alto - 25 * mm

    pdf.setFont("Helvetica-Bold", 13)

    pdf.drawRightString(
        190 * mm,
        y - 5 * mm,
        f"TOTAL: {float(documento['total']):.2f} Bs"
    )

    pdf.setFont("Helvetica", 8)

    pdf.drawString(
        20 * mm,
        15 * mm,
        "Documento generado por el sistema."
    )

    pdf.save()

    buffer.seek(0)

    return buffer
