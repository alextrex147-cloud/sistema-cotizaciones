import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from dotenv import load_dotenv
from supabase import create_client


# ============================================================
# CONFIGURACIÓN
# ============================================================

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception(
        "Faltan SUPABASE_URL o SUPABASE_KEY en las variables de entorno."
    )

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def numero_siguiente(tabla, campo="numero"):
    try:
        respuesta = (
            supabase
            .table(tabla)
            .select(campo)
            .order(campo, desc=True)
            .limit(1)
            .execute()
        )

        if respuesta.data:
            ultimo = respuesta.data[0].get(campo)

            try:
                return int(ultimo) + 1
            except:
                return 1

        return 1

    except:
        return 1


def buscar_cliente(nombre):
    nombre = (nombre or "").strip()

    if not nombre:
        return None

    respuesta = (
        supabase
        .table("clientes")
        .select("*")
        .ilike("nombre", nombre)
        .limit(1)
        .execute()
    )

    if respuesta.data:
        return respuesta.data[0]

    return None


def obtener_o_crear_cliente(nombre, telefono="", direccion=""):
    nombre = (nombre or "").strip()

    if not nombre:
        raise Exception("Debes indicar el nombre del cliente.")

    cliente = buscar_cliente(nombre)

    if cliente:
        return cliente

    datos = {
        "nombre": nombre,
        "telefono": (telefono or "").strip(),
        "direccion": (direccion or "").strip()
    }

    respuesta = (
        supabase
        .table("clientes")
        .insert(datos)
        .execute()
    )

    if not respuesta.data:
        raise Exception("No se pudo crear el cliente.")

    return respuesta.data[0]


def buscar_producto(nombre):
    nombre = (nombre or "").strip()

    if not nombre:
        return None

    respuesta = (
        supabase
        .table("productos")
        .select("*")
        .ilike("nombre", nombre)
        .limit(1)
        .execute()
    )

    if respuesta.data:
        return respuesta.data[0]

    return None


def obtener_o_crear_producto(
    nombre,
    descripcion="",
    tipo_venta="unidad",
    precio=0,
    stock_minimo=0
):
    nombre = (nombre or "").strip()

    if not nombre:
        raise Exception("Debes escribir el nombre del producto.")

    producto = buscar_producto(nombre)

    if producto:
        return producto

    tipo_venta = (tipo_venta or "unidad").strip().lower()

    if tipo_venta not in ["metro", "kilo", "unidad"]:
        tipo_venta = "unidad"

    try:
        precio = float(precio or 0)
    except:
        precio = 0

    try:
        stock_minimo = float(stock_minimo or 0)
    except:
        stock_minimo = 0

    datos = {
        "nombre": nombre,
        "descripcion": (descripcion or "").strip(),
        "tipo_venta": tipo_venta,
        "precio": precio,
        "stock": 0,
        "stock_minimo": stock_minimo
    }

    respuesta = (
        supabase
        .table("productos")
        .insert(datos)
        .execute()
    )

    if not respuesta.data:
        raise Exception("No se pudo crear el producto.")

    return respuesta.data[0]


# ============================================================
# EXISTENCIAS
# ============================================================

def siguiente_numero_existencia(producto_id):
    respuesta = (
        supabase
        .table("existencias_inventario")
        .select("numero")
        .eq("producto_id", producto_id)
        .order("numero", desc=True)
        .limit(1)
        .execute()
    )

    if respuesta.data:
        return int(respuesta.data[0]["numero"]) + 1

    return 1


def crear_existencias(
    producto_id,
    cantidad_existencias,
    cantidad_por_existencia,
    unidad,
    motivo="Entrada"
):
    try:
        cantidad_existencias = int(
            cantidad_existencias
        )
    except:
        cantidad_existencias = 0

    try:
        cantidad_por_existencia = float(
            cantidad_por_existencia
        )
    except:
        cantidad_por_existencia = 0

    unidad = (unidad or "").strip().lower()

    if not producto_id:
        raise Exception(
            "No se indicó el producto."
        )

    if cantidad_existencias <= 0:
        raise Exception(
            "La cantidad de existencias debe ser mayor a 0."
        )

    if cantidad_por_existencia <= 0:
        raise Exception(
            "La cantidad por existencia debe ser mayor a 0."
        )

    if unidad not in [
        "metros",
        "kilos",
        "unidad"
    ]:
        raise Exception(
            "La unidad debe ser METROS, KILOS o UNIDAD."
        )

    numero = siguiente_numero_existencia(
        producto_id
    )

    creadas = []

    for i in range(cantidad_existencias):

        datos = {
            "producto_id": producto_id,
            "numero": numero + i,
            "cantidad_inicial": cantidad_por_existencia,
            "cantidad_actual": cantidad_por_existencia,
            "unidad_contenido": unidad,
            "estado": "disponible"
        }

        respuesta = (
            supabase
            .table("existencias_inventario")
            .insert(datos)
            .execute()
        )

        if not respuesta.data:
            raise Exception(
                "No se pudo crear una existencia."
            )

        existencia = respuesta.data[0]

        creadas.append(existencia)

        (
            supabase
            .table("movimientos_existencias")
            .insert({
                "existencia_id": existencia["id"],
                "producto_id": producto_id,
                "tipo": "ENTRADA",
                "cantidad": cantidad_por_existencia,
                "descripcion": motivo
            })
            .execute()
        )

    actualizar_stock_general(
        producto_id
    )

    return creadas


def obtener_existencias_producto(producto_id):
    respuesta = (
        supabase
        .table("existencias_inventario")
        .select("*")
        .eq("producto_id", producto_id)
        .order("numero")
        .execute()
    )

    return respuesta.data or []


def actualizar_stock_general(producto_id):

    existencias = obtener_existencias_producto(
        producto_id
    )

    total = 0

    for existencia in existencias:

        try:
            cantidad = float(
                existencia.get(
                    "cantidad_actual",
                    0
                ) or 0
            )
        except:
            cantidad = 0

        total += cantidad

    (
        supabase
        .table("productos")
        .update({
            "stock": total
        })
        .eq("id", producto_id)
        .execute()
    )

    return total


def stock_disponible(producto_id):

    existencias = obtener_existencias_producto(
        producto_id
    )

    total = 0

    for existencia in existencias:

        if existencia.get("estado") == "agotada":
            continue

        try:
            cantidad = float(
                existencia.get(
                    "cantidad_actual",
                    0
                ) or 0
            )
        except:
            cantidad = 0

        total += cantidad

    return total


def descontar_existencia(
    producto_id,
    cantidad_necesaria,
    numero_venta=""
):
    try:
        cantidad_necesaria = float(
            cantidad_necesaria
        )
    except:
        cantidad_necesaria = 0

    if cantidad_necesaria <= 0:
        return

    existencias = (
        supabase
        .table("existencias_inventario")
        .select("*")
        .eq("producto_id", producto_id)
        .neq("estado", "agotada")
        .order("numero")
        .execute()
        .data or []
    )

    disponible = 0

    for existencia in existencias:

        try:
            disponible += float(
                existencia.get(
                    "cantidad_actual",
                    0
                ) or 0
            )
        except:
            pass

    if disponible < cantidad_necesaria:
        raise Exception(
            "No hay suficiente stock para realizar la venta."
        )

    restante = cantidad_necesaria

    for existencia in existencias:

        if restante <= 0:
            break

        try:
            actual = float(
                existencia.get(
                    "cantidad_actual",
                    0
                ) or 0
            )
        except:
            actual = 0

        if actual <= 0:
            continue

        descuento = min(
            actual,
            restante
        )

        nuevo = actual - descuento

        if nuevo <= 0:
            nuevo = 0
            estado = "agotada"
        else:
            estado = "disponible"

        (
            supabase
            .table("existencias_inventario")
            .update({
                "cantidad_actual": nuevo,
                "estado": estado
            })
            .eq("id", existencia["id"])
            .execute()
        )

        (
            supabase
            .table("movimientos_existencias")
            .insert({
                "existencia_id": existencia["id"],
                "producto_id": producto_id,
                "tipo": "SALIDA",
                "cantidad": descuento,
                "numero_venta": numero_venta,
                "descripcion": "Salida por venta"
            })
            .execute()
        )

        restante -= descuento

    actualizar_stock_general(
        producto_id
    )


# ============================================================
# INICIO
# ============================================================

@app.route("/")
def inicio():

    try:
        productos = (
            supabase
            .table("productos")
            .select("*")
            .execute()
            .data or []
        )
    except:
        productos = []

    try:
        clientes = (
            supabase
            .table("clientes")
            .select("*")
            .execute()
            .data or []
        )
    except:
        clientes = []

    try:
        cotizaciones = (
            supabase
            .table("cotizaciones")
            .select("*")
            .execute()
            .data or []
        )
    except:
        cotizaciones = []

    return render_template(
        "index.html",
        productos=productos,
        clientes=clientes,
        cotizaciones=cotizaciones
    )


# ============================================================
# CLIENTES
# ============================================================

@app.route("/clientes")
def clientes():

    lista = (
        supabase
        .table("clientes")
        .select("*")
        .order("nombre")
        .execute()
        .data or []
    )

    return render_template(
        "clientes.html",
        clientes=lista
    )


@app.route(
    "/agregar-cliente",
    methods=["POST"]
)
def agregar_cliente():

    try:

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        direccion = request.form.get(
            "direccion",
            ""
        ).strip()

        obtener_o_crear_cliente(
            nombre,
            telefono,
            direccion
        )

        return redirect(
            url_for("clientes")
        )

    except Exception as e:

        return (
            f"Error al guardar cliente: {e}",
            500
        )


@app.route(
    "/eliminar-cliente/<int:id>",
    methods=["POST"]
)
def eliminar_cliente(id):

    try:

        (
            supabase
            .table("clientes")
            .delete()
            .eq("id", id)
            .execute()
        )

        return redirect(
            url_for("clientes")
        )

    except Exception as e:

        return (
            f"Error al eliminar cliente: {e}",
            500
        )


# ============================================================
# PRODUCTOS
# ============================================================

@app.route("/productos")
def productos():

    lista = (
        supabase
        .table("productos")
        .select("*")
        .order("nombre")
        .execute()
        .data or []
    )

    return render_template(
        "productos.html",
        productos=lista
    )


@app.route(
    "/agregar-producto",
    methods=["POST"]
)
def agregar_producto():

    try:

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        tipo_venta = request.form.get(
            "tipo_venta",
            "unidad"
        ).strip().lower()

        precio = request.form.get(
            "precio",
            "0"
        )

        stock_minimo = request.form.get(
            "stock_minimo",
            "0"
        )

        cantidad_existencias = request.form.get(
            "cantidad_existencias",
            "0"
        )

        cantidad_por_existencia = request.form.get(
            "cantidad_por_existencia",
            "0"
        )

        unidad = request.form.get(
            "unidad",
            "unidad"
        ).strip().lower()

        producto_existente = buscar_producto(
            nombre
        )

        if producto_existente:

            (
                supabase
                .table("productos")
                .update({
                    "descripcion": descripcion,
                    "tipo_venta": tipo_venta,
                    "precio": float(precio or 0),
                    "stock_minimo": float(
                        stock_minimo or 0
                    )
                })
                .eq(
                    "id",
                    producto_existente["id"]
                )
                .execute()
            )

            producto = producto_existente

        else:

            producto = obtener_o_crear_producto(
                nombre,
                descripcion,
                tipo_venta,
                precio,
                stock_minimo
            )

        try:
            ce = int(
                cantidad_existencias or 0
            )
        except:
            ce = 0

        try:
            cpe = float(
                cantidad_por_existencia or 0
            )
        except:
            cpe = 0

        if ce > 0 and cpe > 0:

            crear_existencias(
                producto["id"],
                ce,
                cpe,
                unidad,
                "Entrada inicial"
            )

        return redirect(
            url_for("productos")
        )

    except Exception as e:

        return (
            f"Error al guardar producto: {e}",
            500
        )


@app.route(
    "/eliminar-producto/<int:id>",
    methods=["POST"]
)
def eliminar_producto(id):

    try:

        # Eliminamos movimientos
        (
            supabase
            .table("movimientos_existencias")
            .delete()
            .eq("producto_id", id)
            .execute()
        )

        # Eliminamos existencias
        (
            supabase
            .table("existencias_inventario")
            .delete()
            .eq("producto_id", id)
            .execute()
        )

        # Finalmente eliminamos producto
        (
            supabase
            .table("productos")
            .delete()
            .eq("id", id)
            .execute()
        )

        return redirect(
            url_for("productos")
        )

    except Exception as e:

        return (
            f"Error al eliminar producto: {e}",
            500
        )


# ============================================================
# INVENTARIO
# ============================================================

@app.route("/inventario")
def inventario():

    existencias = (
        supabase
        .table("existencias_inventario")
        .select("*")
        .order("producto_id")
        .order("numero")
        .execute()
        .data or []
    )

    movimientos = (
        supabase
        .table("movimientos_existencias")
        .select("*")
        .order("id", desc=True)
        .limit(100)
        .execute()
        .data or []
    )

    productos = (
        supabase
        .table("productos")
        .select("*")
        .order("nombre")
        .execute()
        .data or []
    )

    mapa_existencias = {
        e["id"]: e["numero"]
        for e in existencias
    }

    mapa_productos = {
        p["id"]: p["nombre"]
        for p in productos
    }

    for existencia in existencias:

        existencia["producto_nombre"] = (
            mapa_productos.get(
                existencia.get("producto_id"),
                "Producto desconocido"
            )
        )

    for movimiento in movimientos:

        movimiento["existencia_numero"] = (
            mapa_existencias.get(
                movimiento.get("existencia_id")
            )
        )

        movimiento["producto_nombre"] = (
            mapa_productos.get(
                movimiento.get("producto_id"),
                "Producto desconocido"
            )
        )

    return render_template(
        "inventario.html",
        existencias=existencias,
        movimientos=movimientos,
        productos=productos
    )


@app.route(
    "/entrada-inventario",
    methods=["POST"]
)
def entrada_inventario():

    try:

        producto_nombre = request.form.get(
            "producto_nombre",
            ""
        ).strip()

        if not producto_nombre:

            raise Exception(
                "Debes escribir el nombre del producto."
            )

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        tipo_venta = request.form.get(
            "tipo_venta",
            "unidad"
        ).strip().lower()

        precio = request.form.get(
            "precio",
            "0"
        )

        stock_minimo = request.form.get(
            "stock_minimo",
            "0"
        )

        producto = buscar_producto(
            producto_nombre
        )

        if not producto:

            producto = obtener_o_crear_producto(
                producto_nombre,
                descripcion,
                tipo_venta,
                precio,
                stock_minimo
            )

        cantidad_existencias = int(
            request.form.get(
                "cantidad_existencias"
            ) or 0
        )

        cantidad_por_existencia = float(
            request.form.get(
                "cantidad_por_existencia"
            ) or 0
        )

        unidad = request.form.get(
            "unidad",
            ""
        ).strip().lower()

        crear_existencias(
            producto["id"],
            cantidad_existencias,
            cantidad_por_existencia,
            unidad,
            "Entrada de inventario"
        )

        return redirect(
            url_for("inventario")
        )

    except Exception as e:

        return (
            f"Error al registrar entrada: {e}",
            500
        )


@app.route(
    "/eliminar-existencia/<int:id>",
    methods=["POST"]
)
def eliminar_existencia(id):

    try:

        existencia = (
            supabase
            .table("existencias_inventario")
            .select("*")
            .eq("id", id)
            .limit(1)
            .execute()
        )

        if not existencia.data:

            raise Exception(
                "La existencia no existe."
            )

        existencia = existencia.data[0]

        producto_id = existencia[
            "producto_id"
        ]

        # Primero eliminamos sus movimientos
        (
            supabase
            .table("movimientos_existencias")
            .delete()
            .eq(
                "existencia_id",
                id
            )
            .execute()
        )

        # Después eliminamos la existencia
        (
            supabase
            .table("existencias_inventario")
            .delete()
            .eq(
                "id",
                id
            )
            .execute()
        )

        # Actualizamos el stock general
        actualizar_stock_general(
            producto_id
        )

        return redirect(
            url_for("inventario")
        )

    except Exception as e:

        return (
            f"Error al eliminar existencia: {e}",
            500
        )


@app.route(
    "/eliminar-movimiento/<int:id>",
    methods=["POST"]
)
def eliminar_movimiento(id):

    try:

        (
            supabase
            .table("movimientos_existencias")
            .delete()
            .eq("id", id)
            .execute()
        )

        return redirect(
            url_for("inventario")
        )

    except Exception as e:

        return (
            f"Error al eliminar movimiento: {e}",
            500
        )


@app.route(
    "/limpiar-movimientos",
    methods=["POST"]
)
def limpiar_movimientos():

    try:

        (
            supabase
            .table("movimientos_existencias")
            .delete()
            .neq("id", 0)
            .execute()
        )

        return redirect(
            url_for("inventario")
        )

    except Exception as e:

        return (
            f"Error al limpiar movimientos: {e}",
            500
        )


# ============================================================
# COTIZACIONES
# ============================================================

@app.route("/nueva-cotizacion")
def nueva_cotizacion():

    clientes = (
        supabase
        .table("clientes")
        .select("*")
        .order("nombre")
        .execute()
        .data or []
    )

    productos = (
        supabase
        .table("productos")
        .select("*")
        .order("nombre")
        .execute()
        .data or []
    )

    numero = numero_siguiente(
        "cotizaciones",
        "numero"
    )

    return render_template(
        "nueva_cotizacion.html",
        clientes=clientes,
        productos=productos,
        numero=numero
    )


@app.route(
    "/guardar-cotizacion",
    methods=["POST"]
)
def guardar_cotizacion():

    try:

        cliente_nombre = request.form.get(
            "cliente",
            ""
        ).strip()

        cliente_telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        cliente_direccion = request.form.get(
            "direccion",
            ""
        ).strip()

        tipo_documento = request.form.get(
            "tipo_documento",
            "COTIZACION"
        ).strip().upper()

        numero = request.form.get(
            "numero",
            ""
        ).strip()

        observaciones = request.form.get(
            "observaciones",
            ""
        ).strip()

        cliente = obtener_o_crear_cliente(
            cliente_nombre,
            cliente_telefono,
            cliente_direccion
        )

        productos_ids = request.form.getlist(
            "producto_id"
        )

        cantidades = request.form.getlist(
            "cantidad"
        )

        precios = request.form.getlist(
            "precio"
        )

        longitudes = request.form.getlist(
            "longitud"
        )

        detalles = []

        total = 0

        for i in range(
            len(productos_ids)
        ):

            producto_id = productos_ids[i]

            if not producto_id:
                continue

            producto = (
                supabase
                .table("productos")
                .select("*")
                .eq(
                    "id",
                    int(producto_id)
                )
                .limit(1)
                .execute()
            )

            if not producto.data:
                continue

            producto = producto.data[0]

            try:
                cantidad = float(
                    cantidades[i]
                )
            except:
                cantidad = 0

            try:
                precio = float(
                    precios[i]
                )
            except:
                precio = float(
                    producto.get(
                        "precio",
                        0
                    ) or 0
                )

            try:
                longitud = float(
                    longitudes[i]
                )
            except:
                longitud = 1

            tipo = (
                producto.get(
                    "tipo_venta",
                    "unidad"
                ) or "unidad"
            ).lower()

            if tipo == "metro":
                subtotal = (
                    cantidad
                    * longitud
                    * precio
                )

            else:
                subtotal = (
                    cantidad
                    * precio
                )

            total += subtotal

            detalles.append({
                "producto_id": producto["id"],
                "producto": producto["nombre"],
                "cantidad": cantidad,
                "longitud": longitud,
                "precio": precio,
                "subtotal": subtotal
            })

        estado = "cotizacion"

        if tipo_documento == "VENTA":
            estado = "venta"

        datos = {
            "numero": numero,
            "cliente_id": cliente["id"],
            "tipo": tipo_documento,
            "estado": estado,
            "total": total,
            "observaciones": observaciones,
            "detalle": detalles,
            "fecha": datetime.now().isoformat()
        }

        respuesta = (
            supabase
            .table("cotizaciones")
            .insert(datos)
            .execute()
        )

        if not respuesta.data:
            raise Exception(
                "No se pudo guardar la cotización."
            )

        cotizacion = respuesta.data[0]

        # Si es venta, descontamos stock
        if tipo_documento == "VENTA":

            for detalle in detalles:

                producto_id = detalle[
                    "producto_id"
                ]

                producto = (
                    supabase
                    .table("productos")
                    .select("*")
                    .eq(
                        "id",
                        producto_id
                    )
                    .limit(1)
                    .execute()
                )

                if not producto.data:
                    continue

                producto = producto.data[0]

                tipo = (
                    producto.get(
                        "tipo_venta",
                        "unidad"
                    ) or "unidad"
                ).lower()

                cantidad_stock = (
                    detalle["cantidad"]
                )

                if tipo == "metro":

                    cantidad_stock = (
                        detalle["cantidad"]
                        * detalle["longitud"]
                    )

                descontar_existencia(
                    producto_id,
                    cantidad_stock,
                    numero
                )

        return redirect(
            url_for(
                "cotizacion",
                id=cotizacion["id"]
            )
        )

    except Exception as e:

        return (
            f"Error al guardar cotización: {e}",
            500
        )


# ============================================================
# HISTORIAL
# ============================================================

@app.route("/historial")
def historial():

    cotizaciones = (
        supabase
        .table("cotizaciones")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data or []
    )

    clientes = (
        supabase
        .table("clientes")
        .select("*")
        .execute()
        .data or []
    )

    mapa_clientes = {
        c["id"]: c["nombre"]
        for c in clientes
    }

    for c in cotizaciones:

        c["cliente_nombre"] = (
            mapa_clientes.get(
                c.get("cliente_id"),
                "Sin cliente"
            )
        )

    return render_template(
        "historial.html",
        cotizaciones=cotizaciones
    )


# ============================================================
# VER COTIZACIÓN
# ============================================================

@app.route(
    "/cotizacion/<int:id>"
)
def cotizacion(id):

    respuesta = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq("id", id)
        .limit(1)
        .execute()
    )

    if not respuesta.data:

        return (
            "Cotización no encontrada",
            404
        )

    cotizacion = respuesta.data[0]

    cliente = None

    if cotizacion.get("cliente_id"):

        respuesta_cliente = (
            supabase
            .table("clientes")
            .select("*")
            .eq(
                "id",
                cotizacion["cliente_id"]
            )
            .limit(1)
            .execute()
        )

        if respuesta_cliente.data:
            cliente = respuesta_cliente.data[0]

    return render_template(
        "cotizacion.html",
        cotizacion=cotizacion,
        cliente=cliente
    )


# ============================================================
# ELIMINAR COTIZACIÓN
# ============================================================

@app.route(
    "/eliminar-cotizacion/<int:id>",
    methods=["POST"]
)
def eliminar_cotizacion(id):

    try:

        (
            supabase
            .table("cotizaciones")
            .delete()
            .eq("id", id)
            .execute()
        )

        return redirect(
            url_for("historial")
        )

    except Exception as e:

        return (
            f"Error al eliminar cotización: {e}",
            500
        )


# ============================================================
# PASAR COTIZACIÓN A VENTA
# ============================================================

@app.route(
    "/pasar-a-venta/<int:id>",
    methods=["POST"]
)
def pasar_a_venta(id):

    try:

        respuesta = (
            supabase
            .table("cotizaciones")
            .select("*")
            .eq("id", id)
            .limit(1)
            .execute()
        )

        if not respuesta.data:

            raise Exception(
                "La cotización no existe."
            )

        cotizacion = respuesta.data[0]

        estado_actual = (
            cotizacion.get(
                "estado",
                ""
            ) or ""
        ).lower()

        if estado_actual == "venta":

            raise Exception(
                "Esta cotización ya fue convertida en venta."
            )

        detalles = (
            cotizacion.get(
                "detalle",
                []
            ) or []
        )

        if isinstance(detalles, str):
            detalles = []

        # ----------------------------------------------------
        # Primero comprobamos todo el stock
        # ----------------------------------------------------

        for detalle in detalles:

            producto_id = detalle.get(
                "producto_id"
            )

            if not producto_id:
                continue

            producto = (
                supabase
                .table("productos")
                .select("*")
                .eq(
                    "id",
                    producto_id
                )
                .limit(1)
                .execute()
            )

            if not producto.data:
                continue

            producto = producto.data[0]

            tipo = (
                producto.get(
                    "tipo_venta",
                    "unidad"
                ) or "unidad"
            ).lower()

            cantidad = float(
                detalle.get(
                    "cantidad",
                    0
                ) or 0
            )

            longitud = float(
                detalle.get(
                    "longitud",
                    1
                ) or 1
            )

            cantidad_stock = cantidad

            if tipo == "metro":

                cantidad_stock = (
                    cantidad
                    * longitud
                )

            disponible = stock_disponible(
                producto_id
            )

            if disponible < cantidad_stock:

                raise Exception(
                    "Stock insuficiente para "
                    + producto["nombre"]
                )

        # ----------------------------------------------------
        # Descontamos
        # ----------------------------------------------------

        for detalle in detalles:

            producto_id = detalle.get(
                "producto_id"
            )

            if not producto_id:
                continue

            producto = (
                supabase
                .table("productos")
                .select("*")
                .eq(
                    "id",
                    producto_id
                )
                .limit(1)
                .execute()
            )

            if not producto.data:
                continue

            producto = producto.data[0]

            tipo = (
                producto.get(
                    "tipo_venta",
                    "unidad"
                ) or "unidad"
            ).lower()

            cantidad = float(
                detalle.get(
                    "cantidad",
                    0
                ) or 0
            )

            longitud = float(
                detalle.get(
                    "longitud",
                    1
                ) or 1
            )

            cantidad_stock = cantidad

            if tipo == "metro":

                cantidad_stock = (
                    cantidad
                    * longitud
                )

            descontar_existencia(
                producto_id,
                cantidad_stock,
                cotizacion.get(
                    "numero",
                    ""
                )
            )

        (
            supabase
            .table("cotizaciones")
            .update({
                "estado": "venta",
                "tipo": "VENTA"
            })
            .eq(
                "id",
                id
            )
            .execute()
        )

        return redirect(
            url_for(
                "cotizacion",
                id=id
            )
        )

    except Exception as e:

        return (
            f"Error al convertir a venta: {e}",
            500
        )


# ============================================================
# VENTAS
# ============================================================

@app.route("/ventas")
def ventas():

    ventas = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq("estado", "venta")
        .order("id", desc=True)
        .execute()
        .data or []
    )

    return render_template(
        "ventas.html",
        ventas=ventas
    )


# ============================================================
# CAJA
# ============================================================

@app.route("/caja")
def caja():

    ventas = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq("estado", "venta")
        .order("id", desc=True)
        .execute()
        .data or []
    )

    total = 0

    for venta in ventas:

        try:
            total += float(
                venta.get(
                    "total",
                    0
                ) or 0
            )
        except:
            pass

    return render_template(
        "caja.html",
        ventas=ventas,
        total=total
    )


# ============================================================
# REPORTES
# ============================================================

@app.route("/reportes")
def reportes():

    productos = (
        supabase
        .table("productos")
        .select("*")
        .order("nombre")
        .execute()
        .data or []
    )

    ventas = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq("estado", "venta")
        .order("id", desc=True)
        .execute()
        .data or []
    )

    cotizaciones = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq("estado", "cotizacion")
        .order("id", desc=True)
        .execute()
        .data or []
    )

    total_ventas = 0

    for venta in ventas:

        try:
            total_ventas += float(
                venta.get(
                    "total",
                    0
                ) or 0
            )
        except:
            pass

    stock_bajo = []

    for producto in productos:

        try:
            stock = float(
                producto.get(
                    "stock",
                    0
                ) or 0
            )

            minimo = float(
                producto.get(
                    "stock_minimo",
                    0
                ) or 0
            )

            if stock <= minimo:
                stock_bajo.append(
                    producto
                )

        except:
            pass

    return render_template(
        "reportes.html",
        productos=productos,
        ventas=ventas,
        cotizaciones=cotizaciones,
        total_ventas=total_ventas,
        stock_bajo=stock_bajo
    )


# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                5000
            )
        ),
        debug=True
    )
