import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave-local")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Faltan SUPABASE_URL y SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def numero_siguiente(prefijo, tabla):
    try:
        respuesta = supabase.table(tabla).select("numero").order("id", desc=True).limit(1).execute()

        if not respuesta.data:
            return f"{prefijo}-0001"

        ultimo = respuesta.data[0]["numero"]
        try:
            numero = int(ultimo.split("-")[-1]) + 1
        except Exception:
            numero = 1

        return f"{prefijo}-{numero:04d}"

    except Exception:
        return f"{prefijo}-0001"


def buscar_cliente(nombre, telefono):
    if not nombre:
        return None

    consulta = supabase.table("clientes").select("*").ilike("nombre", nombre).limit(1).execute()

    if consulta.data:
        return consulta.data[0]

    if telefono:
        consulta = (
            supabase.table("clientes")
            .select("*")
            .eq("telefono", telefono)
            .limit(1)
            .execute()
        )

        if consulta.data:
            return consulta.data[0]

    return None


def obtener_o_crear_cliente(nombre, telefono, direccion, email):
    existente = buscar_cliente(nombre, telefono)

    if existente:
        return existente["id"]

    nuevo = {
        "nombre": nombre,
        "telefono": telefono,
        "direccion": direccion,
        "email": email
    }

    respuesta = supabase.table("clientes").insert(nuevo).execute()

    if not respuesta.data:
        raise Exception("No se pudo guardar el cliente.")

    return respuesta.data[0]["id"]


def buscar_producto(nombre):
    if not nombre:
        return None

    respuesta = (
        supabase.table("productos")
        .select("*")
        .ilike("nombre", nombre)
        .limit(1)
        .execute()
    )

    if respuesta.data:
        return respuesta.data[0]

    return None


def obtener_o_crear_producto(nombre, descripcion, tipo_venta, precio):
    existente = buscar_producto(nombre)

    if existente:
        return existente

    nuevo = {
        "nombre": nombre,
        "descripcion": descripcion,
        "tipo_venta": tipo_venta,
        "precio": precio
    }

    respuesta = supabase.table("productos").insert(nuevo).execute()

    if not respuesta.data:
        raise Exception("No se pudo guardar el producto.")

    return respuesta.data[0]


@app.route("/")
def inicio():
    clientes = supabase.table("clientes").select("*").execute().data or []
    productos = supabase.table("productos").select("*").execute().data or []
    cotizaciones = supabase.table("cotizaciones").select("*").order("id", desc=True).execute().data or []
    ventas = supabase.table("ventas").select("*").order("id", desc=True).execute().data or []

    total_cotizado = sum(float(x.get("total") or 0) for x in cotizaciones)
    total_vendido = sum(float(x.get("total") or 0) for x in ventas)

    hoy = datetime.now().date().isoformat()

    ventas_hoy = [
        x for x in ventas
        if str(x.get("fecha", ""))[:10] == hoy
    ]

    total_hoy = sum(float(x.get("total") or 0) for x in ventas_hoy)

    stock_bajo = [
        p for p in productos
        if float(p.get("stock") or 0) <= float(p.get("stock_minimo") or 0)
    ]

    agotados = [
        p for p in productos
        if float(p.get("stock") or 0) <= 0
    ]

    return render_template(
        "index.html",
        clientes=clientes,
        productos=productos,
        cotizaciones=cotizaciones,
        ventas=ventas,
        total_cotizado=total_cotizado,
        total_vendido=total_vendido,
        ventas_hoy=ventas_hoy,
        total_hoy=total_hoy,
        stock_bajo=stock_bajo,
        agotados=agotados
    )


@app.route("/clientes")
def clientes():
    datos = supabase.table("clientes").select("*").order("id", desc=True).execute().data or []
    return render_template("clientes.html", clientes=datos)


@app.route("/agregar-cliente", methods=["POST"])
def agregar_cliente():
    datos = {
        "nombre": request.form.get("nombre", "").strip(),
        "telefono": request.form.get("telefono", "").strip(),
        "direccion": request.form.get("direccion", "").strip(),
        "email": request.form.get("email", "").strip()
    }

    if datos["nombre"]:
        supabase.table("clientes").insert(datos).execute()

    return redirect(url_for("clientes"))


@app.route("/eliminar-cliente/<int:id>", methods=["POST"])
def eliminar_cliente(id):
    supabase.table("clientes").delete().eq("id", id).execute()
    return redirect(url_for("clientes"))


@app.route("/productos")
def productos():
    datos = supabase.table("productos").select("*").order("id", desc=True).execute().data or []
    return render_template("productos.html", productos=datos)


@app.route("/agregar-producto", methods=["POST"])
def agregar_producto():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    tipo_venta = request.form.get("tipo_venta", "unidad")
    precio = float(request.form.get("precio") or 0)
    stock = float(request.form.get("stock") or 0)
    stock_minimo = float(request.form.get("stock_minimo") or 0)
    largo = request.form.get("largo_inventario")

    datos = {
        "nombre": nombre,
        "descripcion": descripcion,
        "tipo_venta": tipo_venta,
        "precio": precio,
        "stock": stock,
        "stock_minimo": stock_minimo,
        "largo_inventario": float(largo) if largo else None
    }

    if nombre:
        respuesta = supabase.table("productos").insert(datos).execute()

        if respuesta.data and stock > 0:
            supabase.table("movimientos_inventario").insert({
                "producto_id": respuesta.data[0]["id"],
                "tipo": "ENTRADA",
                "cantidad": stock,
                "largo": float(largo) if largo else None,
                "motivo": "Stock inicial"
            }).execute()

    return redirect(url_for("productos"))


@app.route("/eliminar-producto/<int:id>", methods=["POST"])
def eliminar_producto(id):
    supabase.table("productos").delete().eq("id", id).execute()
    return redirect(url_for("productos"))


@app.route("/inventario")
def inventario():
    productos = supabase.table("productos").select("*").order("nombre").execute().data or []
    movimientos = (
        supabase.table("movimientos_inventario")
        .select("*")
        .order("id", desc=True)
        .limit(100)
        .execute()
        .data or []
    )

    return render_template(
        "inventario.html",
        productos=productos,
        movimientos=movimientos
    )


@app.route("/entrada-inventario", methods=["POST"])
def entrada_inventario():
    producto_id = int(request.form["producto_id"])
    cantidad = float(request.form.get("cantidad") or 0)
    largo = request.form.get("largo")
    motivo = request.form.get("motivo", "Entrada")

    producto = (
        supabase.table("productos")
        .select("*")
        .eq("id", producto_id)
        .single()
        .execute()
        .data
    )

    nuevo_stock = float(producto["stock"] or 0) + cantidad

    supabase.table("productos").update({
        "stock": nuevo_stock
    }).eq("id", producto_id).execute()

    supabase.table("movimientos_inventario").insert({
        "producto_id": producto_id,
        "tipo": "ENTRADA",
        "cantidad": cantidad,
        "largo": float(largo) if largo else None,
        "motivo": motivo
    }).execute()

    return redirect(url_for("inventario"))


@app.route("/nueva-cotizacion")
def nueva_cotizacion():
    clientes = supabase.table("clientes").select("*").order("nombre").execute().data or []
    productos = supabase.table("productos").select("*").order("nombre").execute().data or []

    numero = numero_siguiente("COT", "cotizaciones")

    return render_template(
        "nueva-cotizacion.html",
        clientes=clientes,
        productos=productos,
        numero=numero
    )


@app.route("/guardar-cotizacion", methods=["POST"])
def guardar_cotizacion():
    try:
        nombre_cliente = request.form.get("cliente_nombre", "").strip()
        telefono = request.form.get("cliente_telefono", "").strip()
        direccion = request.form.get("cliente_direccion", "").strip()
        email = request.form.get("cliente_email", "").strip()

        cliente_id = obtener_o_crear_cliente(
            nombre_cliente,
            telefono,
            direccion,
            email
        )

        nombres = request.form.getlist("producto_nombre[]")
        descripciones = request.form.getlist("producto_descripcion[]")
        tipos = request.form.getlist("producto_tipo[]")
        cantidades = request.form.getlist("cantidad[]")
        largos = request.form.getlist("largo[]")
        precios = request.form.getlist("precio[]")

        detalles = []
        subtotal_total = 0

        for i in range(len(nombres)):
            nombre = nombres[i].strip()

            if not nombre:
                continue

            tipo = tipos[i] if i < len(tipos) else "unidad"
            cantidad = float(cantidades[i] or 0)
            largo = float(largos[i]) if i < len(largos) and largos[i] else None
            precio = float(precios[i] or 0)

            if tipo == "metro":
                subtotal = cantidad * (largo or 0) * precio
            else:
                subtotal = cantidad * precio

            producto = obtener_o_crear_producto(
                nombre,
                descripciones[i] if i < len(descripciones) else "",
                tipo,
                precio
            )

            detalles.append({
                "producto_id": producto["id"],
                "producto_nombre": nombre,
                "cantidad": cantidad,
                "largo": largo,
                "precio": precio,
                "subtotal": subtotal
            })

            subtotal_total += subtotal

        descuento = float(request.form.get("descuento") or 0)
        total = subtotal_total - descuento

        numero = request.form.get("numero") or numero_siguiente("COT", "cotizaciones")

        cotizacion = supabase.table("cotizaciones").insert({
            "numero": numero,
            "cliente_id": cliente_id,
            "subtotal": subtotal_total,
            "descuento": descuento,
            "total": total,
            "estado": "cotizacion",
            "observaciones": request.form.get("observaciones", "")
        }).execute()

        if not cotizacion.data:
            raise Exception("No se pudo guardar la cotización.")

        cotizacion_id = cotizacion.data[0]["id"]

        for detalle in detalles:
            detalle["cotizacion_id"] = cotizacion_id
            supabase.table("detalle_cotizacion").insert(detalle).execute()

        return redirect(url_for("ver_cotizacion", id=cotizacion_id))

    except Exception as e:
        return f"Error al guardar la cotización: {e}", 500


@app.route("/historial")
def historial():
    cotizaciones = (
        supabase.table("cotizaciones")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data or []
    )

    return render_template(
        "historial.html",
        cotizaciones=cotizaciones
    )


@app.route("/cotizacion/<int:id>")
def ver_cotizacion(id):
    cotizacion = (
        supabase.table("cotizaciones")
        .select("*")
        .eq("id", id)
        .single()
        .execute()
        .data
    )

    detalles = (
        supabase.table("detalle_cotizacion")
        .select("*")
        .eq("cotizacion_id", id)
        .execute()
        .data or []
    )

    cliente = None

    if cotizacion.get("cliente_id"):
        cliente = (
            supabase.table("clientes")
            .select("*")
            .eq("id", cotizacion["cliente_id"])
            .single()
            .execute()
            .data
        )

    return render_template(
        "cotizacion.html",
        cotizacion=cotizacion,
        detalles=detalles,
        cliente=cliente
    )


@app.route("/eliminar-cotizacion/<int:id>", methods=["POST"])
def eliminar_cotizacion(id):
    supabase.table("detalle_cotizacion").delete().eq("cotizacion_id", id).execute()
    supabase.table("cotizaciones").delete().eq("id", id).execute()

    return redirect(url_for("historial"))


@app.route("/pasar-a-venta/<int:id>", methods=["POST"])
def pasar_a_venta(id):
    try:
        cotizacion = (
            supabase.table("cotizaciones")
            .select("*")
            .eq("id", id)
            .single()
            .execute()
            .data
        )

        detalles = (
            supabase.table("detalle_cotizacion")
            .select("*")
            .eq("cotizacion_id", id)
            .execute()
            .data or []
        )

        numero = numero_siguiente("VTA", "ventas")

        forma_pago = request.form.get("forma_pago", "Efectivo")

        venta = supabase.table("ventas").insert({
            "numero": numero,
            "cotizacion_id": id,
            "cliente_id": cotizacion["cliente_id"],
            "subtotal": cotizacion["subtotal"],
            "descuento": cotizacion["descuento"],
            "total": cotizacion["total"],
            "forma_pago": forma_pago,
            "observaciones": cotizacion.get("observaciones", "")
        }).execute()

        if not venta.data:
            raise Exception("No se pudo crear la venta.")

        venta_id = venta.data[0]["id"]

        for detalle in detalles:
            supabase.table("detalle_venta").insert({
                "venta_id": venta_id,
                "producto_id": detalle["producto_id"],
                "producto_nombre": detalle["producto_nombre"],
                "cantidad": detalle["cantidad"],
                "largo": detalle["largo"],
                "precio": detalle["precio"],
                "subtotal": detalle["subtotal"]
            }).execute()

            producto = (
                supabase.table("productos")
                .select("*")
                .eq("id", detalle["producto_id"])
                .single()
                .execute()
                .data
            )

            stock_actual = float(producto["stock"] or 0)

            if producto["tipo_venta"] == "metro":
                salida = float(detalle["cantidad"]) * float(detalle["largo"] or 0)
            else:
                salida = float(detalle["cantidad"])

            nuevo_stock = stock_actual - salida

            if nuevo_stock < 0:
                nuevo_stock = 0

            supabase.table("productos").update({
                "stock": nuevo_stock
            }).eq("id", detalle["producto_id"]).execute()

            supabase.table("movimientos_inventario").insert({
                "producto_id": detalle["producto_id"],
                "tipo": "SALIDA",
                "cantidad": salida,
                "largo": detalle["largo"],
                "motivo": f"Venta {numero}"
            }).execute()

        supabase.table("movimientos_caja").insert({
            "venta_id": venta_id,
            "tipo": "INGRESO",
            "monto": cotizacion["total"],
            "forma_pago": forma_pago,
            "descripcion": f"Venta {numero}"
        }).execute()

        supabase.table("cotizaciones").update({
            "estado": "vendida"
        }).eq("id", id).execute()

        return redirect(url_for("ventas"))

    except Exception as e:
        return f"Error al convertir a venta: {e}", 500


@app.route("/ventas")
def ventas():
    datos = (
        supabase.table("ventas")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data or []
    )

    total = sum(float(x.get("total") or 0) for x in datos)

    return render_template(
        "ventas.html",
        ventas=datos,
        total=total
    )


@app.route("/caja")
def caja():
    movimientos = (
        supabase.table("movimientos_caja")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data or []
    )

    total = sum(
        float(x.get("monto") or 0)
        for x in movimientos
        if x.get("tipo") == "INGRESO"
    )

    return render_template(
        "caja.html",
        movimientos=movimientos,
        total=total
    )


@app.route("/reportes")
def reportes():
    ventas = supabase.table("ventas").select("*").execute().data or []
    cotizaciones = supabase.table("cotizaciones").select("*").execute().data or []
    productos = supabase.table("productos").select("*").execute().data or []

    total_ventas = sum(float(x.get("total") or 0) for x in ventas)
    total_cotizaciones = sum(float(x.get("total") or 0) for x in cotizaciones)

    return render_template(
        "reportes.html",
        ventas=ventas,
        cotizaciones=cotizaciones,
        productos=productos,
        total_ventas=total_ventas,
        total_cotizaciones=total_cotizaciones
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True
    )
