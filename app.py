import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client, Client


# =========================================================
# CONFIGURACIÓN
# =========================================================

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception(
        "Faltan SUPABASE_URL y SUPABASE_KEY en el archivo .env"
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# INICIO
# =========================================================

@app.route("/")
def inicio():

    clientes = (
        supabase
        .table("clientes")
        .select("*")
        .execute()
        .data
    )

    productos = (
        supabase
        .table("productos")
        .select("*")
        .execute()
        .data
    )

    cotizaciones = (
        supabase
        .table("cotizaciones")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data
    )

    ultimas = []

    for c in cotizaciones[:5]:

        cliente_nombre = ""

        if c.get("cliente_id"):

            cliente = (
                supabase
                .table("clientes")
                .select("nombre")
                .eq("id", c["cliente_id"])
                .limit(1)
                .execute()
                .data
            )

            if cliente:
                cliente_nombre = cliente[0]["nombre"]

        c["cliente_nombre"] = cliente_nombre

        ultimas.append(c)

    return render_template(
        "index.html",
        cantidad_clientes=len(clientes),
        cantidad_productos=len(productos),
        cantidad_cotizaciones=len(cotizaciones),
        ultimas=ultimas
    )


# =========================================================
# CLIENTES
# =========================================================

@app.route("/clientes")
def clientes():

    lista = (
        supabase
        .table("clientes")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data
    )

    return render_template(
        "clientes.html",
        clientes=lista
    )


@app.route("/agregar-cliente", methods=["POST"])
def agregar_cliente():

    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    direccion = request.form.get("direccion", "").strip()
    email = request.form.get("email", "").strip()

    if nombre:

        supabase.table("clientes").insert({
            "nombre": nombre,
            "telefono": telefono,
            "direccion": direccion,
            "email": email
        }).execute()

    return redirect(url_for("clientes"))


@app.route("/editar-cliente/<int:id>", methods=["GET", "POST"])
def editar_cliente(id):

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        email = request.form.get("email", "").strip()

        supabase.table("clientes").update({
            "nombre": nombre,
            "telefono": telefono,
            "direccion": direccion,
            "email": email
        }).eq("id", id).execute()

        return redirect(url_for("clientes"))

    resultado = (
        supabase
        .table("clientes")
        .select("*")
        .eq("id", id)
        .limit(1)
        .execute()
        .data
    )

    cliente = resultado[0] if resultado else None

    return render_template(
        "editar_cliente.html",
        cliente=cliente
    )


@app.route("/eliminar-cliente/<int:id>")
def eliminar_cliente(id):

    supabase.table("clientes").delete().eq(
        "id", id
    ).execute()

    return redirect(url_for("clientes"))


# =========================================================
# PRODUCTOS
# =========================================================

@app.route("/productos")
def productos():

    lista = (
        supabase
        .table("productos")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data
    )

    return render_template(
        "productos.html",
        productos=lista
    )


@app.route("/agregar-producto", methods=["POST"])
def agregar_producto():

    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    precio = request.form.get("precio", "0")

    try:
        precio = float(precio)
    except:
        precio = 0

    if nombre and precio >= 0:

        supabase.table("productos").insert({
            "nombre": nombre,
            "descripcion": descripcion,
            "precio": precio
        }).execute()

    return redirect(url_for("productos"))


@app.route("/editar-producto/<int:id>", methods=["GET", "POST"])
def editar_producto(id):

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", "0")

        try:
            precio = float(precio)
        except:
            precio = 0

        supabase.table("productos").update({
            "nombre": nombre,
            "descripcion": descripcion,
            "precio": precio
        }).eq("id", id).execute()

        return redirect(url_for("productos"))

    resultado = (
        supabase
        .table("productos")
        .select("*")
        .eq("id", id)
        .limit(1)
        .execute()
        .data
    )

    producto = resultado[0] if resultado else None

    return render_template(
        "editar_producto.html",
        producto=producto
    )


@app.route("/eliminar-producto/<int:id>")
def eliminar_producto(id):

    supabase.table("productos").delete().eq(
        "id", id
    ).execute()

    return redirect(url_for("productos"))


# =========================================================
# NUEVA COTIZACIÓN
# =========================================================

@app.route("/nueva-cotizacion")
def nueva_cotizacion():

    clientes = (
        supabase
        .table("clientes")
        .select("*")
        .order("nombre")
        .execute()
        .data
    )

    productos = (
        supabase
        .table("productos")
        .select("*")
        .order("nombre")
        .execute()
        .data
    )

    return render_template(
        "nueva_cotizacion.html",
        clientes=clientes,
        productos=productos
    )


# =========================================================
# GUARDAR COTIZACIÓN
# =========================================================

@app.route("/guardar-cotizacion", methods=["POST"])
def guardar_cotizacion():

    cliente_id = request.form.get("cliente_id")
    descuento = request.form.get("descuento", "0")
    observaciones = request.form.get(
        "observaciones", ""
    ).strip()

    try:
        cliente_id = int(cliente_id)
    except:
        return redirect(url_for("nueva_cotizacion"))

    try:
        descuento = float(descuento)
    except:
        descuento = 0

    productos_ids = request.form.getlist("producto_id[]")
    cantidades = request.form.getlist("cantidad[]")
    precios = request.form.getlist("precio[]")

    detalles = []
    subtotal = 0

    for i in range(len(productos_ids)):

        try:

            producto_id = int(productos_ids[i])
            cantidad = float(cantidades[i])
            precio = float(precios[i])

            if cantidad <= 0:
                continue

            subtotal_producto = cantidad * precio

            producto = (
                supabase
                .table("productos")
                .select("nombre")
                .eq("id", producto_id)
                .limit(1)
                .execute()
                .data
            )

            nombre_producto = "Producto"

            if producto:
                nombre_producto = producto[0]["nombre"]

            detalles.append({
                "producto_id": producto_id,
                "producto_nombre": nombre_producto,
                "cantidad": cantidad,
                "precio": precio,
                "subtotal": subtotal_producto
            })

            subtotal += subtotal_producto

        except:
            continue

    if not detalles:
        return redirect(url_for("nueva_cotizacion"))

    if descuento < 0:
        descuento = 0

    if descuento > subtotal:
        descuento = subtotal

    total = subtotal - descuento

    fecha = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    # =====================================================
    # OBTENER SIGUIENTE NÚMERO
    # =====================================================

    cotizaciones = (
        supabase
        .table("cotizaciones")
        .select("id")
        .order("id", desc=True)
        .limit(1)
        .execute()
        .data
    )

    siguiente_id = 1

    if cotizaciones:
        siguiente_id = cotizaciones[0]["id"] + 1

    numero = f"COT-{siguiente_id:05d}"

    # =====================================================
    # GUARDAR COTIZACIÓN
    # =====================================================

    nueva = (
        supabase
        .table("cotizaciones")
        .insert({
            "numero": numero,
            "cliente_id": cliente_id,
            "fecha": fecha,
            "subtotal": subtotal,
            "descuento": descuento,
            "total": total,
            "observaciones": observaciones
        })
        .execute()
        .data
    )

    if not nueva:
        return redirect(url_for("nueva_cotizacion"))

    cotizacion_id = nueva[0]["id"]

    # =====================================================
    # GUARDAR DETALLES
    # =====================================================

    for detalle in detalles:

        supabase.table(
            "detalle_cotizacion"
        ).insert({

            "cotizacion_id": cotizacion_id,
            "producto_id": detalle["producto_id"],
            "producto_nombre": detalle["producto_nombre"],
            "cantidad": detalle["cantidad"],
            "precio": detalle["precio"],
            "subtotal": detalle["subtotal"]

        }).execute()

    return redirect(
        url_for(
            "ver_cotizacion",
            id=cotizacion_id
        )
    )


# =========================================================
# HISTORIAL
# =========================================================

@app.route("/historial")
def historial():

    cotizaciones = (
        supabase
        .table("cotizaciones")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data
    )

    for c in cotizaciones:

        cliente = (
            supabase
            .table("clientes")
            .select("nombre")
            .eq("id", c["cliente_id"])
            .limit(1)
            .execute()
            .data
        )

        c["cliente_nombre"] = ""

        if cliente:
            c["cliente_nombre"] = cliente[0]["nombre"]

    return render_template(
        "historial.html",
        cotizaciones=cotizaciones
    )


# =========================================================
# VER COTIZACIÓN
# =========================================================

@app.route("/cotizacion/<int:id>")
def ver_cotizacion(id):

    resultado = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq("id", id)
        .limit(1)
        .execute()
        .data
    )

    if not resultado:
        return redirect(url_for("historial"))

    cotizacion = resultado[0]

    cliente = None

    if cotizacion.get("cliente_id"):

        cliente_resultado = (
            supabase
            .table("clientes")
            .select("*")
            .eq("id", cotizacion["cliente_id"])
            .limit(1)
            .execute()
            .data
        )

        if cliente_resultado:
            cliente = cliente_resultado[0]

    cotizacion["cliente_nombre"] = (
        cliente["nombre"] if cliente else ""
    )

    cotizacion["cliente_telefono"] = (
        cliente["telefono"] if cliente else ""
    )

    cotizacion["cliente_direccion"] = (
        cliente["direccion"] if cliente else ""
    )

    cotizacion["cliente_email"] = (
        cliente["email"] if cliente else ""
    )

    detalles = (
        supabase
        .table("detalle_cotizacion")
        .select("*")
        .eq("cotizacion_id", id)
        .order("id")
        .execute()
        .data
    )

    return render_template(
        "ver_cotizacion.html",
        cotizacion=cotizacion,
        detalles=detalles
    )


# =========================================================
# ELIMINAR COTIZACIÓN
# =========================================================

@app.route("/eliminar-cotizacion/<int:id>")
def eliminar_cotizacion(id):

    supabase.table(
        "detalle_cotizacion"
    ).delete().eq(
        "cotizacion_id", id
    ).execute()

    supabase.table(
        "cotizaciones"
    ).delete().eq(
        "id", id
    ).execute()

    return redirect(url_for("historial"))


# =========================================================
# EJECUTAR
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )