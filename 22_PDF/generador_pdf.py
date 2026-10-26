    c.drawString(rx + 19 * mm, T - 13 * mm, f"Nº {documento.get('numero', '')}")

    # Fecha
    fx = rx + 4 * mm
    fy = T - 31 * mm
    bw = 21 * mm
    bh = 10 * mm

    for i, lab in enumerate(["DÍA", "MES", "AÑO"]):
        x = fx + i * bw
        c.setStrokeColor(BLUE)
        c.setLineWidth(0.8)
        c.rect(x, fy, bw, bh, stroke=1, fill=0)
        c.setFillColor(LIGHT)
        c.rect(x, fy + bh - 4 * mm, bw, 4 * mm, stroke=0, fill=1)
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 6.7)
        c.drawCentredString(x + bw / 2, fy + bh - 2.7 * mm, lab)

    d, m, y = parts(documento)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    for i, value in enumerate([d, m, y]):
        c.drawCentredString(fx + i * bw + bw / 2, fy + 1.8 * mm, value)

    # Nombre y teléfono del cliente
    sy = T - 58 * mm
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 8.2)
    c.drawString(L, sy, "Señor(es):")
    c.setStrokeColor(BLUE)
    c.setLineWidth(0.6)
    c.line(L + 22 * mm, sy - 1.2 * mm, R - 43 * mm, sy - 1.2 * mm)
    c.drawString(R - 41 * mm, sy, "Telf.:")
    c.line(R - 29 * mm, sy - 1.2 * mm, R, sy - 1.2 * mm)

    # CORRECCIÓN: obtener el nombre del cliente relacionado en Supabase.
    cliente, telefono = obtener_datos_cliente(documento)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8.2)
    if cliente:
        c.drawString(L + 23 * mm, sy, cliente[:55])
    if telefono:
        c.drawString(R - 28 * mm, sy, telefono[:20])

    # Tabla de productos
    top = sy - 6 * mm
    bottom = 43 * mm
    c1 = L + 24 * mm
    c2 = R - 53 * mm
    c3 = R - 27 * mm
    hh = 9 * mm

    c.setFillColor(LIGHT)
    c.rect(L, top - hh, R - L, hh, stroke=0, fill=1)
    c.setStrokeColor(BLUE)
    c.setLineWidth(0.9)
    c.rect(L, bottom, R - L, top - bottom, stroke=1, fill=0)
    for x in [c1, c2, c3]:
        c.line(x, bottom, x, top)

    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString((L + c1) / 2, top - 6 * mm, "CANT.")
    c.drawCentredString((c1 + c2) / 2, top - 6 * mm, "DESCRIPCIÓN")
    c.drawCentredString((c2 + c3) / 2, top - 6 * mm, "P. UNIT.")
    c.drawCentredString((c3 + R) / 2, top - 6 * mm, "SUBTOTAL")

    rows = 19
    rh = (top - hh - bottom) / rows
    for i in range(1, rows):
        yy = top - hh - i * rh
        c.setStrokeColor(colors.HexColor("#AAB1C0"))
        c.setLineWidth(0.35)
        c.setDash(1, 2)
        c.line(L, yy, R, yy)

    c.setDash()
    yy = top - hh - rh + 2.8 * mm
    for item in detalles or []:
        if yy < bottom + 2 * mm:
            break
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8.2)
        c.drawCentredString((L + c1) / 2, yy, f"{val(item.get('cantidad')):g}")
        c.drawString(c1 + 2 * mm, yy, desc(item)[:65])
        c.drawRightString(c3 - 2 * mm, yy, f"{val(item.get('precio')):,.2f}")
        c.drawRightString(R - 2 * mm, yy, f"{val(item.get('total')):,.2f}")
        yy -= rh

    # Mensaje y total
    c.setFillColor(BLUE)
    c.setFont("Helvetica-BoldOblique", 9.5)
    c.drawString(L, 36.5 * mm, "Gracias por su Preferencia")
    total = val(documento.get("total", documento.get("total_cotizado", 0)))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(R - 55 * mm, 36.5 * mm, "TOTAL Bs.")
    c.setStrokeColor(BLUE)
    c.setLineWidth(0.8)
    c.roundRect(R - 37 * mm, 33.5 * mm, 34 * mm, 9 * mm, 1.2 * mm, stroke=1, fill=0)
    if total:
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(R - 5 * mm, 36.5 * mm, f"{total:,.2f}")

    # Firmas
    fy = 22 * mm
    c.setStrokeColor(colors.HexColor("#7D8492"))
    c.setLineWidth(0.45)
    c.line(L + 10 * mm, fy, L + 73 * mm, fy)
    c.line(R - 73 * mm, fy, R - 10 * mm, fy)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(L + 41.5 * mm, fy - 5 * mm, "ENTREGUÉ CONFORME")
    c.drawCentredString(R - 41.5 * mm, fy - 5 * mm, "RECIBÍ CONFORME")
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(colors.black)
    c.drawString(L + 10 * mm, fy - 9 * mm, "Nombre:")
    c.drawString(R - 73 * mm, fy - 9 * mm, "Nombre:")

    c.save()
    b.seek(0)
    return b
