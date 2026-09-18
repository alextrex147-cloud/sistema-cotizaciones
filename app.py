from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_file,
    flash
)

from 03_BASE_DATOS.clientes import (
    listar_clientes,
    obtener_cliente,
    crear_o_actualizar_cliente,
    actualizar_cliente,
    eliminar_cliente
)

from 03_BASE_DATOS.productos import (
    listar_productos,
    obtener_producto,
    crear_producto,
    actualizar_producto,
    eliminar_producto
)

from 03_BASE_DATOS.cotizaciones import (
    listar_cotizaciones,
    obtener_cotizacion,
    crear_cotizacion,
    actualizar_cotizacion,
    eliminar_cotizacion
)

from 03_BASE_DATOS.ventas import (
    listar_ventas,
    obtener_venta,
    crear_venta,
    actualizar_venta,
    eliminar_venta,
    convertir_cotizacion
)

from 22_PDF.generador_pdf import generar_pdf


app = Flask(__name__)

app.secret_key = "CAMBIAR_ESTA_CLAVE_EN_RENDER"


def numero(valor, defecto=0):
    try:
        return float(valor)
    except Exception:
        return defecto


def calcular_item(item):
    cantidad = numero(item.get("cantidad"))
    precio = numero(item.get("precio"))
    medida = numero(item.get("medida"), 1)

    tipo = item.get("tipo", "normal")

    if tipo in ["metros", "kilos"]:
        total = cantidad * medida * precio
    else:
        total = cantidad * precio

    item["cantidad"] = cantidad
    item["precio"] = precio
    item["medida"] = medida if tipo != "normal" else None
    item["tipo"] = tipo
    item["total"] = round(total, 2)

    return item


def leer_items():
    items = request.get_json(silent=True)

    if not items:
        items = request.form.get("items")

        if not items:
            return []

        import json

        try:
            items = json.loads(items)
        except Exception:
            return []

    resultado = []

    for item in items:
        if not item.get("nombre_producto"):
            continue

        resultado.append(
            calcular_item(item)
        )

    return resultado


@app.route("/")
def inicio():
    cotizaciones = listar_cotizaciones()
    ventas = listar_ventas()
    productos = listar_productos()
    clientes = listar_clientes()

    registros = []

    for c in cotizaciones[:5]:
        cliente = c.get("clientes") or {}

        registros.append({
            "tipo": "Cotización",
            "numero": c["numero"],
            "cliente": cliente.get("nombre", "Sin cliente"),
            "total": c["total"],
            "fecha": str(c.get("created_at", ""))[:10]
        })

    for v in ventas[:5]:
        cliente = v.get("clientes") or {}

        registros.append({
            "tipo": "Venta",
            "numero": v["numero"],
            "cliente": cliente.get("nombre", "Sin cliente"),
            "total": v["total"],
            "fecha": str(v.get("created_at", ""))[:10]
        })

    registros = sorted(
        registros,
        key=lambda x: x["fecha"],
        reverse=True
    )[:10]

    return render_template(
        "inicio.html",
        cantidad_cotizaciones=len(cotizaciones),
        cantidad_ventas=len(ventas),
        cantidad_productos=len(productos),
        cantidad_clientes=len(clientes),
        registros=registros
    )


# =========================================================
# PRODUCTOS
# =========================================================

@app.route("/productos")
def productos():
    busqueda = request.args.get(
        "buscar",
        ""
    )

    lista = listar_productos(busqueda)

    return render_template(
        "productos.html",
        productos=lista,
        buscar=busqueda
    )


@app.route("/productos/crear", methods=["POST"])
def producto_crear():
    nombre = request.form.get("nombre", "").strip()
    precio = numero(
        request.form.get("precio")
    )
    unidad = request.form.get(
        "unidad",
        "unidad"
    )

    if nombre:
        crear_producto(
            nombre,
            precio,
            unidad
        )

    return redirect(url_for("productos"))


@app.route("/productos/editar/<int:producto_id>", methods=["POST"])
def producto_editar(producto_id):
    nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    precio = numero(
        request.form.get("precio")
    )

    unidad = request.form.get(
        "unidad",
        "unidad"
    )

    actualizar_producto(
        producto_id,
        nombre,
        precio,
        unidad
    )

    return redirect(url_for("productos"))


@app.route("/productos/eliminar/<int:producto_id>")
def producto_eliminar(producto_id):
    eliminar_producto(producto_id)

    return redirect(url_for("productos"))


@app.route("/api/productos")
def api_productos():
    lista = listar_productos()

    return jsonify(lista)


# =========================================================
# CLIENTES
# =========================================================

@app.route("/clientes")
def clientes():
    busqueda = request.args.get(
        "buscar",
        ""
    )

    lista = listar_clientes(busqueda)

    return render_template(
        "clientes.html",
        clientes=lista,
        buscar=busqueda
    )


@app.route("/clientes/editar/<int:cliente_id>", methods=["POST"])
def cliente_editar(cliente_id):
    nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    telefono = request.form.get(
        "telefono",
        ""
    ).strip()

    actualizar_cliente(
        cliente_id,
        nombre,
        telefono
    )

    return redirect(url_for("clientes"))


@app.route("/clientes/eliminar/<int:cliente_id>")
def cliente_eliminar(cliente_id):
    eliminar_cliente(cliente_id)

    return redirect(url_for("clientes"))


@app.route("/api/clientes")
def api_clientes():
    return jsonify(listar_clientes())


# =========================================================
# COTIZACIONES
# =========================================================

@app.route("/cotizaciones")
def cotizaciones():
    lista = listar_cotizaciones()

    return render_template(
        "cotizaciones.html",
        cotizaciones=lista
    )


@app.route("/cotizaciones/nueva")
def nueva_cotizacion():
    productos = listar_productos()
    clientes = listar_clientes()

    return render_template(
        "crear_cotizacion.html",
        productos=productos,
        clientes=clientes,
        modo="nueva",
        documento=None,
        detalles=[]
    )


@app.route("/cotizaciones/guardar", methods=["POST"])
def guardar_cotizacion():
    import json

    nombre = request.form.get(
        "cliente_nombre",
        ""
    ).strip()

    telefono = request.form.get(
        "cliente_telefono",
        ""
    ).strip()

    items = json.loads(
        request.form.get(
            "items_json",
            "[]"
        )
    )

    items = [
        calcular_item(x)
        for x in items
        if x.get("nombre_producto")
    ]

    if not nombre:
        flash(
            "Debes ingresar el nombre del cliente."
        )

        return redirect(
            url_for("nueva_cotizacion")
        )

    if not items:
        flash(
            "Debes agregar al menos un producto."
        )

        return redirect(
            url_for("nueva_cotizacion")
        )

    cliente = crear_o_actualizar_cliente(
        nombre,
        telefono
    )

    total = round(
        sum(
            x["total"]
            for x in items
        ),
        2
    )

    cotizacion = crear_cotizacion(
        cliente["id"],
        items,
        total
    )

    return redirect(
        url_for(
            "ver_cotizacion",
            cotizacion_id=cotizacion["id"]
        )
    )


@app.route("/cotizaciones/<int:cotizacion_id>")
def ver_cotizacion(cotizacion_id):
    documento, detalles = obtener_cotizacion(
        cotizacion_id
    )

    return render_template(
        "crear_cotizacion.html",
        productos=listar_productos(),
        clientes=listar_clientes(),
        modo="ver",
        documento=documento,
        detalles=detalles
    )


@app.route(
    "/cotizaciones/editar/<int:cotizacion_id>"
)
def editar_cotizacion(cotizacion_id):
    documento, detalles = obtener_cotizacion(
        cotizacion_id
    )

    return render_template(
        "crear_cotizacion.html",
        productos=listar_productos(),
        clientes=listar_clientes(),
        modo="editar",
        documento=documento,
        detalles=detalles
    )


@app.route(
    "/cotizaciones/actualizar/<int:cotizacion_id>",
    methods=["POST"]
)
def actualizar_cotizacion_ruta(cotizacion_id):
    import json

    nombre = request.form.get(
        "cliente_nombre",
        ""
    ).strip()

    telefono = request.form.get(
        "cliente_telefono",
        ""
    ).strip()

    items = json.loads(
        request.form.get(
            "items_json",
            "[]"
        )
    )

    items = [
        calcular_item(x)
        for x in items
        if x.get("nombre_producto")
    ]

    cliente = crear_o_actualizar_cliente(
        nombre,
        telefono
    )

    total = round(
        sum(x["total"] for x in items),
        2
    )

    actualizar_cotizacion(
        cotizacion_id,
        cliente["id"],
        items,
        total
    )

    return redirect(
        url_for(
            "ver_cotizacion",
            cotizacion_id=cotizacion_id
        )
    )


@app.route(
    "/cotizaciones/eliminar/<int:cotizacion_id>"
)
def eliminar_cotizacion_ruta(cotizacion_id):
    eliminar_cotizacion(
        cotizacion_id
    )

    return redirect(
        url_for("cotizaciones")
    )


@app.route(
    "/cotizaciones/<int:cotizacion_id>/convertir"
)
def convertir_cotizacion_ruta(cotizacion_id):
    venta = convertir_cotizacion(
        cotizacion_id
    )

    return redirect(
        url_for(
            "ver_venta",
            venta_id=venta["id"]
        )
    )


# =========================================================
# VENTAS
# =========================================================

@app.route("/ventas")
def ventas():
    lista = listar_ventas()

    return render_template(
        "ventas.html",
        ventas=lista
    )


@app.route("/ventas/nueva")
def nueva_venta():
    productos = listar_productos()
    clientes = listar_clientes()

    return render_template(
        "crear_cotizacion.html",
        productos=productos,
        clientes=clientes,
        modo="venta_nueva",
        documento=None,
        detalles=[]
    )


@app.route("/ventas/guardar", methods=["POST"])
def guardar_venta():
    import json

    nombre = request.form.get(
        "cliente_nombre",
        ""
    ).strip()

    telefono = request.form.get(
        "cliente_telefono",
        ""
    ).strip()

    items = json.loads(
        request.form.get(
            "items_json",
            "[]"
        )
    )

    items = [
        calcular_item(x)
        for x in items
        if x.get("nombre_producto")
    ]

    cliente = crear_o_actualizar_cliente(
        nombre,
        telefono
    )

    total = round(
        sum(x["total"] for x in items),
        2
    )

    venta = crear_venta(
        cliente["id"],
        items,
        total
    )

    return redirect(
        url_for(
            "ver_venta",
            venta_id=venta["id"]
        )
    )


@app.route("/ventas/<int:venta_id>")
def ver_venta(venta_id):
    documento, detalles = obtener_venta(
        venta_id
    )

    return render_template(
        "crear_cotizacion.html",
        productos=listar_productos(),
        clientes=listar_clientes(),
        modo="venta_ver",
        documento=documento,
        detalles=detalles
    )


@app.route("/ventas/editar/<int:venta_id>")
def editar_venta(venta_id):
    documento, detalles = obtener_venta(
        venta_id
    )

    return render_template(
        "crear_cotizacion.html",
        productos=listar_productos(),
        clientes=listar_clientes(),
        modo="venta_editar",
        documento=documento,
        detalles=detalles
    )


@app.route(
    "/ventas/actualizar/<int:venta_id>",
    methods=["POST"]
)
def actualizar_venta_ruta(venta_id):
    import json

    nombre = request.form.get(
        "cliente_nombre",
        ""
    ).strip()

    telefono = request.form.get(
        "cliente_telefono",
        ""
    ).strip()

    items = json.loads(
        request.form.get(
            "items_json",
            "[]"
        )
    )

    items = [
        calcular_item(x)
        for x in items
        if x.get("nombre_producto")
    ]

    cliente = crear_o_actualizar_cliente(
        nombre,
        telefono
    )

    total = round(
        sum(x["total"] for x in items),
        2
    )

    actualizar_venta(
        venta_id,
        cliente["id"],
        items,
        total
    )

    return redirect(
        url_for(
            "ver_venta",
            venta_id=venta_id
        )
    )


@app.route("/ventas/eliminar/<int:venta_id>")
def eliminar_venta_ruta(venta_id):
    eliminar_venta(
        venta_id
    )

    return redirect(
        url_for("ventas")
    )


# =========================================================
# PDF
# =========================================================

@app.route(
    "/cotizaciones/<int:cotizacion_id>/pdf"
)
def pdf_cotizacion(cotizacion_id):
    documento, detalles = obtener_cotizacion(
        cotizacion_id
    )

    archivo = generar_pdf(
        "cotizacion",
        documento,
        detalles
    )

    return send_file(
        archivo,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{documento['numero']}.pdf"
    )


@app.route(
    "/ventas/<int:venta_id>/pdf"
)
def pdf_venta(venta_id):
    documento, detalles = obtener_venta(
        venta_id
    )

    archivo = generar_pdf(
        "venta",
        documento,
        detalles
    )

    return send_file(
        archivo,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{documento['numero']}.pdf"
    )


# =========================================================
# EJECUTAR
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
