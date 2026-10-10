import sys
import os
import json
from datetime import datetime
from pathlib import Path

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

# =========================================================
# 1. CARPETAS DEL SISTEMA
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BASE_DIR / "03_BASE_DATOS"))
sys.path.insert(0, str(BASE_DIR / "22_PDF"))

# =========================================================
# 2. IMPORTAR BASE DE DATOS
# =========================================================

from clientes import (
    listar_clientes,
    crear_o_actualizar_cliente,
    actualizar_cliente,
    eliminar_cliente
)

from productos import (
    listar_productos,
    crear_producto,
    actualizar_producto,
    eliminar_producto
)

from cotizaciones import (
    listar_cotizaciones,
    obtener_cotizacion,
    crear_cotizacion,
    actualizar_cotizacion,
    eliminar_cotizacion
)

from ventas import (
    listar_ventas,
    obtener_venta,
    crear_venta,
    actualizar_venta,
    eliminar_venta,
    convertir_cotizacion
)

from generador_pdf import generar_pdf

try:
    from impresiones import crear_impresion, listar_impresiones
except ImportError:
    def crear_impresion(*args, **kwargs):
        return None

    def listar_impresiones():
        return []

# =========================================================
# 3. CONFIGURACIÓN FLASK
# =========================================================

app = Flask(
    __name__,
    template_folder="09_TEMPLATES",
    static_folder="17_STATIC"
)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "clave-local-cambiar-en-render"
)

# =========================================================
# 4. FUNCIONES AUXILIARES
# =========================================================

def numero(valor, defecto=0):
    try:
        return float(valor or defecto)
    except (ValueError, TypeError):
        return float(defecto)


def calcular_item(item):
    cantidad = numero(item.get("cantidad"))
    precio = numero(item.get("precio"))
    tipo = str(item.get("tipo", "normal")).lower()

    if tipo in ("metros", "metro", "kilos", "kilo"):
        medida = numero(item.get("medida"))
        total = cantidad * medida * precio
    else:
        total = cantidad * precio

    item["cantidad"] = cantidad
    item["precio"] = precio
    item["total"] = round(total, 2)

    return item


def leer_items():
    items_json = request.form.get("items_json", "[]")

    try:
        items = json.loads(items_json)
    except (json.JSONDecodeError, TypeError):
        items = []

    if not isinstance(items, list):
        return []

    resultado = []

    for item in items:
        if not isinstance(item, dict):
            continue

        producto = str(item.get("producto", "")).strip()

        if not producto:
            continue

        item["producto"] = producto
        resultado.append(calcular_item(item))

    return resultado


def calcular_total(items):
    return round(
        sum(numero(item.get("total")) for item in items),
        2
    )


def obtener_cliente_del_formulario():
    nombre = request.form.get("cliente", "").strip()
    telefono = request.form.get("telefono", "").strip()

    if not nombre:
        return None

    return crear_o_actualizar_cliente(nombre, telefono)


def documento_en_fechas(documento, desde="", hasta=""):
    fecha = str(
        documento.get("created_at")
        or documento.get("fecha")
        or documento.get("fecha_creacion")
        or ""
    )[:10]

    if desde and (not fecha or fecha < desde):
        return False

    if hasta and (not fecha or fecha > hasta):
        return False

    return True


# =========================================================
# 5. PÁGINA PRINCIPAL
# =========================================================

@app.route("/")
def inicio():
    cotizaciones = listar_cotizaciones() or []
    ventas = listar_ventas() or []
    productos = listar_productos() or []
    clientes = listar_clientes() or []

    registros = []

    for documento in cotizaciones:
        documento = dict(documento)
        documento["tipo_documento"] = "Cotización"
        registros.append(documento)

    for documento in ventas:
        documento = dict(documento)
        documento["tipo_documento"] = "Venta"
        registros.append(documento)

    registros.sort(
        key=lambda x: str(
            x.get("created_at") or x.get("fecha") or ""
        ),
        reverse=True
    )

    return render_template(
        "inicio.html",
        cotizaciones=cotizaciones,
        ventas=ventas,
        productos=productos,
        clientes=clientes,
        registros=registros[:10]
    )


# =========================================================
# 6. CONTEO POR RESPONSABLE
# =========================================================

@app.route("/conteo-responsables")
def conteo_responsables():
    responsable = request.args.get("responsable", "").strip()
    desde = request.args.get("desde", "").strip()
    hasta = request.args.get("hasta", "").strip()

    responsables_validos = [
        "José Luis Quenta",
        "Ayudante",
        "Felipa"
    ]

    if responsable not in responsables_validos:
        return render_template(
            "conteo_responsables.html",
            responsable="",
            desde=desde,
            hasta=hasta,
            consultado=False,
            total_cotizaciones=0,
            total_ventas=0
        )

    cotizaciones = listar_cotizaciones() or []
    ventas = listar_ventas() or []

    total_cotizaciones = sum(
        1 for documento in cotizaciones
        if documento.get("responsable") == responsable
        and documento_en_fechas(documento, desde, hasta)
    )

    total_ventas = sum(
        1 for documento in ventas
        if documento.get("responsable") == responsable
        and documento_en_fechas(documento, desde, hasta)
    )

    return render_template(
        "conteo_responsables.html",
        responsable=responsable,
        desde=desde,
        hasta=hasta,
        consultado=True,
        total_cotizaciones=total_cotizaciones,
        total_ventas=total_ventas
    )


# =========================================================
# 7. PRODUCTOS
# =========================================================

@app.route("/productos")
def productos():
    return render_template(
        "productos.html",
        productos=listar_productos() or []
    )


@app.route("/productos/guardar", methods=["POST"])
def guardar_producto():
    nombre = request.form.get("nombre", "").strip()
    precio = numero(request.form.get("precio"))
    unidad = request.form.get("unidad", "unidad").strip()

    if not nombre:
        flash("Escribe el nombre del producto.", "error")
        return redirect(url_for("productos"))

    crear_producto(nombre, precio, unidad)

    flash("Producto guardado.", "success")
    return redirect(url_for("productos"))


@app.route("/productos/editar/<int:producto_id>", methods=["GET", "POST"])
def editar_producto(producto_id):
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        precio = numero(request.form.get("precio"))
        unidad = request.form.get("unidad", "unidad").strip()

        actualizar_producto(
            producto_id,
            nombre,
            precio,
            unidad
        )

        flash("Producto actualizado.", "success")
        return redirect(url_for("productos"))

    return render_template(
        "editar_producto.html",
        producto_id=producto_id
    )


@app.route("/productos/eliminar/<int:producto_id>", methods=["POST"])
def borrar_producto(producto_id):
    eliminar_producto(producto_id)
    flash("Producto eliminado.", "success")
    return redirect(url_for("productos"))


@app.route("/api/productos")
def api_productos():
    return jsonify(listar_productos() or [])


# =========================================================
# 8. CLIENTES
# =========================================================

@app.route("/clientes")
def clientes():
    return render_template(
        "clientes.html",
        clientes=listar_clientes() or []
    )


@app.route("/clientes/editar/<int:cliente_id>", methods=["GET", "POST"])
def editar_cliente(cliente_id):
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()

        actualizar_cliente(
            cliente_id,
            nombre,
            telefono
        )

        flash("Cliente actualizado.", "success")
        return redirect(url_for("clientes"))

    return render_template(
        "editar_cliente.html",
        cliente_id=cliente_id
    )


@app.route("/clientes/eliminar/<int:cliente_id>", methods=["POST"])
def borrar_cliente(cliente_id):
    eliminar_cliente(cliente_id)
    flash("Cliente eliminado.", "success")
    return redirect(url_for("clientes"))


@app.route("/api/clientes")
def api_clientes():
    return jsonify(listar_clientes() or [])


# =========================================================
# 9. LISTA DE COTIZACIONES
# =========================================================

@app.route("/cotizaciones")
def lista_cotizaciones():
    return render_template(
        "historial.html",
        cotizaciones=listar_cotizaciones() or [],
        ventas=listar_ventas() or []
    )


# =========================================================
# 10. NUEVA COTIZACIÓN
# =========================================================

@app.route("/cotizaciones/nueva")
def nueva_cotizacion():
    return render_template(
        "nueva_cotizacion.html",
        modo="nueva",
        cotizacion=None,
        clientes=listar_clientes() or [],
        productos=listar_productos() or []
    )


# =========================================================
# 11. GUARDAR COTIZACIÓN
# =========================================================

@app.route("/cotizaciones/guardar", methods=["POST"])
def guardar_cotizacion():
    cliente = obtener_cliente_del_formulario()

    if not cliente:
        flash("Debes escribir el nombre del cliente.", "error")
        return redirect(url_for("nueva_cotizacion"))

    items = leer_items()

    if not items:
        flash("Agrega al menos un producto.", "error")
        return redirect(url_for("nueva_cotizacion"))

    total = calcular_total(items)

    crear_cotizacion(
        cliente["id"],
        items,
        total
    )

    flash("Cotización guardada.", "success")
    return redirect(url_for("lista_cotizaciones"))


# =========================================================
# 12. VER COTIZACIÓN
# =========================================================

@app.route("/cotizaciones/<int:cotizacion_id>")
def ver_cotizacion(cotizacion_id):
    cotizacion = obtener_cotizacion(cotizacion_id)

    if not cotizacion:
        flash("No se encontró la cotización.", "error")
        return redirect(url_for("lista_cotizaciones"))

    return render_template(
        "nueva_cotizacion.html",
        modo="ver",
        cotizacion=cotizacion,
        clientes=listar_clientes() or [],
        productos=listar_productos() or []
    )


# =========================================================
# 13. EDITAR COTIZACIÓN
# =========================================================

@app.route("/cotizaciones/editar/<int:cotizacion_id>")
def formulario_editar_cotizacion(cotizacion_id):
    cotizacion = obtener_cotizacion(cotizacion_id)

    if not cotizacion:
        flash("No se encontró la cotización.", "error")
        return redirect(url_for("lista_cotizaciones"))

    return render_template(
        "nueva_cotizacion.html",
        modo="editar",
        cotizacion=cotizacion,
        clientes=listar_clientes() or [],
        productos=listar_productos() or []
    )


@app.route("/cotizaciones/actualizar/<int:cotizacion_id>", methods=["POST"])
def guardar_edicion_cotizacion(cotizacion_id):
    cliente = obtener_cliente_del_formulario()

    if not cliente:
        flash("Debes escribir el nombre del cliente.", "error")
        return redirect(
            url_for(
                "formulario_editar_cotizacion",
                cotizacion_id=cotizacion_id
            )
        )

    items = leer_items()

    if not items:
        flash("Agrega al menos un producto.", "error")
        return redirect(
            url_for(
                "formulario_editar_cotizacion",
                cotizacion_id=cotizacion_id
            )
        )

    actualizar_cotizacion(
        cotizacion_id,
        cliente["id"],
        items,
        calcular_total(items)
    )

    flash("Cotización actualizada.", "success")
    return redirect(url_for("ver_cotizacion", cotizacion_id=cotizacion_id))


# =========================================================
# 14. ELIMINAR COTIZACIÓN
# =========================================================

@app.route("/cotizaciones/eliminar/<int:cotizacion_id>", methods=["POST"])
def borrar_cotizacion(cotizacion_id):
    eliminar_cotizacion(cotizacion_id)
    flash("Cotización eliminada.", "success")
    return redirect(url_for("lista_cotizaciones"))


# =========================================================
# 15. CONVERTIR COTIZACIÓN EN VENTA
# =========================================================

@app.route("/cotizaciones/<int:cotizacion_id>/convertir", methods=["POST"])
def pasar_a_venta(cotizacion_id):
    convertir_cotizacion(cotizacion_id)
    flash("Se procesó la conversión a venta.", "success")
    return redirect(url_for("lista_ventas"))


# =========================================================
# 16. LISTA DE VENTAS
# =========================================================

@app.route("/ventas")
def lista_ventas():
    return render_template(
        "historial.html",
        cotizaciones=listar_cotizaciones() or [],
        ventas=listar_ventas() or []
    )


# =========================================================
# 17. NUEVA VENTA
# =========================================================

@app.route("/ventas/nueva")
def nueva_venta():
    return render_template(
        "nueva_cotizacion.html",
        modo="venta_nueva",
        cotizacion=None,
        venta=None,
        clientes=listar_clientes() or [],
        productos=listar_productos() or []
    )


# =========================================================
# 18. GUARDAR VENTA
# =========================================================

@app.route("/ventas/guardar", methods=["POST"])
def guardar_venta():
    cliente = obtener_cliente_del_formulario()

    if not cliente:
        flash("Debes escribir el nombre del cliente.", "error")
        return redirect(url_for("nueva_venta"))

    items = leer_items()

    if not items:
        flash("Agrega al menos un producto.", "error")
        return redirect(url_for("nueva_venta"))

    total = calcular_total(items)

    crear_venta(
        cliente["id"],
        items,
        total
    )

    flash("Venta guardada.", "success")
    return redirect(url_for("lista_ventas"))


# =========================================================
# 19. VER VENTA
# =========================================================

@app.route("/ventas/<int:venta_id>")
def ver_venta(venta_id):
    venta = obtener_venta(venta_id)

    if not venta:
        flash("No se encontró la venta.", "error")
        return redirect(url_for("lista_ventas"))

    return render_template(
        "nueva_cotizacion.html",
        modo="venta_ver",
        venta=venta,
        cotizacion=venta,
        clientes=listar_clientes() or [],
        productos=listar_productos() or []
    )


# =========================================================
# 20. EDITAR VENTA
# =========================================================

@app.route("/ventas/editar/<int:venta_id>")
def formulario_editar_venta(venta_id):
    venta = obtener_venta(venta_id)

    if not venta:
        flash("No se encontró la venta.", "error")
        return redirect(url_for("lista_ventas"))

    return render_template(
        "nueva_cotizacion.html",
        modo="venta_editar",
        venta=venta,
        cotizacion=venta,
        clientes=listar_clientes() or [],
        productos=listar_productos() or []
    )


@app.route("/ventas/actualizar/<int:venta_id>", methods=["POST"])
def guardar_edicion_venta(venta_id):
    cliente = obtener_cliente_del_formulario()

    if not cliente:
        flash("Debes escribir el nombre del cliente.", "error")
        return redirect(
            url_for(
                "formulario_editar_venta",
                venta_id=venta_id
            )
        )

    items = leer_items()

    if not items:
        flash("Agrega al menos un producto.", "error")
        return redirect(
            url_for(
                "formulario_editar_venta",
                venta_id=venta_id
            )
        )

    actualizar_venta(
        venta_id,
        cliente["id"],
        items,
        calcular_total(items)
    )

    flash("Venta actualizada.", "success")
    return redirect(url_for("ver_venta", venta_id=venta_id))


# =========================================================
# 21. ELIMINAR VENTA
# =========================================================

@app.route("/ventas/eliminar/<int:venta_id>", methods=["POST"])
def borrar_venta(venta_id):
    eliminar_venta(venta_id)
    flash("Venta eliminada.", "success")
    return redirect(url_for("lista_ventas"))


# =========================================================
# 22. GENERAR PDF
# =========================================================

@app.route("/cotizaciones/<int:cotizacion_id>/pdf")
def pdf_cotizacion(cotizacion_id):
    documento = obtener_cotizacion(cotizacion_id)

    if not documento:
        flash("No se encontró la cotización.", "error")
        return redirect(url_for("lista_cotizaciones"))

    pdf = generar_pdf(
        "Cotización",
        documento,
        documento.get("detalles", documento.get("items", []))
    )

    if hasattr(pdf, "seek"):
        pdf.seek(0)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"cotizacion_{cotizacion_id}.pdf"
    )


@app.route("/ventas/<int:venta_id>/pdf")
def pdf_venta(venta_id):
    documento = obtener_venta(venta_id)

    if not documento:
        flash("No se encontró la venta.", "error")
        return redirect(url_for("lista_ventas"))

    pdf = generar_pdf(
        "Venta",
        documento,
        documento.get("detalles", documento.get("items", []))
    )

    if hasattr(pdf, "seek"):
        pdf.seek(0)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"venta_{venta_id}.pdf"
    )


# =========================================================
# 23. IMPRESIONES
# =========================================================

@app.route("/impresiones")
def lista_impresiones():
    return render_template(
        "historial.html",
        cotizaciones=listar_cotizaciones() or [],
        ventas=listar_ventas() or [],
        impresiones=listar_impresiones() or []
    )


# =========================================================
# 24. INICIAR SERVIDOR
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
