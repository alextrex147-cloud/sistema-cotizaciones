import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client


# ============================================================
# CONFIGURACIÓN
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise Exception("Falta SUPABASE_URL")

if not SUPABASE_KEY:
    raise Exception("Falta SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

app = Flask(__name__)


# ============================================================
# FUNCIONES AUXILIARES
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
            return int(respuesta.data[0][campo]) + 1

    except:
        pass

    return 1


# ============================================================
# CLIENTES
# ============================================================

def buscar_cliente(nombre):

    nombre = (nombre or "").strip()

    if not nombre:
        return None

    try:

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

    except:
        pass

    return None


def obtener_o_crear_cliente(nombre):

    nombre = (nombre or "").strip()

    if not nombre:
        return None

    cliente = buscar_cliente(nombre)

    if cliente:
        return cliente

    datos = {
        "nombre": nombre
    }

    try:

        respuesta = (
            supabase
            .table("clientes")
            .insert(datos)
            .execute()
        )

        if respuesta.data:
            return respuesta.data[0]

    except Exception as e:
        raise Exception(
            f"No se pudo guardar el cliente: {e}"
        )

    return None


# ============================================================
# PRODUCTOS
# ============================================================

def buscar_producto(nombre):

    nombre = (nombre or "").strip()

    if not nombre:
        return None

    try:

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

    except:
        pass

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
        raise Exception(
            "Debes escribir el nombre del producto."
        )

    producto = buscar_producto(nombre)

    if producto:
        return producto

    try:
        precio = float(precio or 0)
    except:
        precio = 0

    try:
        stock_minimo = float(stock_minimo or 0)
    except:
        stock_minimo = 0

    tipo_venta = (
        tipo_venta or "unidad"
    ).strip().lower()

    if tipo_venta not in [
        "unidad",
        "metro",
        "kilo"
    ]:
        tipo_venta = "unidad"

    datos = {
        "nombre": nombre,
        "descripcion": descripcion or "",
        "tipo_venta": tipo_venta,
        "precio": precio,
        "stock": 0,
        "stock_minimo": stock_minimo
    }

    try:

        respuesta = (
            supabase
            .table("productos")
            .insert(datos)
            .execute()
        )

        if respuesta.data:
            return respuesta.data[0]

    except Exception as e:
        raise Exception(
            f"No se pudo guardar el producto: {e}"
        )

    return None


# ============================================================
# EXISTENCIAS
# ============================================================

def siguiente_numero_existencia(producto_id):

    try:

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

            return (
                int(
                    respuesta.data[0]["numero"]
                ) + 1
            )

    except:
        pass

    return 1


def actualizar_stock_general(producto_id):

    try:

        respuesta = (
            supabase
            .table("existencias_inventario")
            .select("cantidad_actual")
            .eq("producto_id", producto_id)
            .eq("estado", "disponible")
            .execute()
        )

        total = 0

        for existencia in (
            respuesta.data or []
        ):

            try:

                total += float(
                    existencia.get(
                        "cantidad_actual",
                        0
                    ) or 0
                )

            except:
                pass

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

    except Exception as e:

        print(
            "Error actualizando stock:",
            e
        )

        return 0


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

    unidad = (
        unidad or ""
    ).strip().lower()

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

    for i in range(
        cantidad_existencias
    ):

        datos = {

            "producto_id": producto_id,

            "numero":
                numero + i,

            "cantidad_inicial":
                cantidad_por_existencia,

            "cantidad_actual":
                cantidad_por_existencia,

            "unidad_contenido":
                unidad,

            "estado":
                "disponible"
        }

        respuesta = (
            supabase
            .table(
                "existencias_inventario"
            )
            .insert(datos)
            .execute()
        )

        if not respuesta.data:

            raise Exception(
                "No se pudo crear una existencia."
            )

        existencia = (
            respuesta.data[0]
        )

        creadas.append(
            existencia
        )

        (
            supabase
            .table(
                "movimientos_existencias"
            )
            .insert({

                "existencia_id":
                    existencia["id"],

                "producto_id":
                    producto_id,

                "tipo":
                    "ENTRADA",

                "cantidad":
                    cantidad_por_existencia,

                "descripcion":
                    motivo
            })
            .execute()
        )

    actualizar_stock_general(
        producto_id
    )

    return creadas


def obtener_existencias_producto(
    producto_id
):

    try:

        respuesta = (
            supabase
            .table(
                "existencias_inventario"
            )
            .select("*")
            .eq(
                "producto_id",
                producto_id
            )
            .order(
                "numero"
            )
            .execute()
        )

        return respuesta.data or []

    except:

        return []


def stock_disponible(producto_id):

    existencias = (
        obtener_existencias_producto(
            producto_id
        )
    )

    total = 0

    for existencia in existencias:

        estado = (
            existencia.get(
                "estado",
                ""
            ) or ""
        ).lower()

        if estado != "disponible":
            continue

        try:

            total += float(
                existencia.get(
                    "cantidad_actual",
                    0
                ) or 0
            )

        except:
            pass

    return total


def descontar_existencia(
    producto_id,
    cantidad,
    numero_venta=None,
    descripcion="Venta"
):

    try:

        cantidad = float(
            cantidad
        )

    except:

        raise Exception(
            "Cantidad inválida."
        )

    if cantidad <= 0:

        return

    existencias = (
        obtener_existencias_producto(
            producto_id
        )
    )

    restante = cantidad

    for existencia in existencias:

        if restante <= 0:
            break

        estado = (
            existencia.get(
                "estado",
                ""
            ) or ""
        ).lower()

        if estado != "disponible":
            continue

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

        usar = min(
            actual,
            restante
        )

        nuevo = actual - usar

        if nuevo <= 0:

            nuevo = 0

            nuevo_estado = "agotada"

        else:

            nuevo_estado = "disponible"

        (
            supabase
            .table(
                "existencias_inventario"
            )
            .update({

                "cantidad_actual":
                    nuevo,

                "estado":
                    nuevo_estado

            })
            .eq(
                "id",
                existencia["id"]
            )
            .execute()
        )

        (
            supabase
            .table(
                "movimientos_existencias"
            )
            .insert({

                "existencia_id":
                    existencia["id"],

                "producto_id":
                    producto_id,

                "tipo":
                    "SALIDA",

                "cantidad":
                    usar,

                "numero_venta":
                    numero_venta,

                "descripcion":
                    descripcion
            })
            .execute()
        )

        restante -= usar

    if restante > 0:

        raise Exception(
            "No hay suficiente stock disponible."
        )

    actualizar_stock_general(
        producto_id
    )


# ============================================================
# INICIO / DASHBOARD
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

    # ========================================================
    # TOTALES DEL PANEL PRINCIPAL
    # ========================================================

    total_cotizado = 0
    total_ventas = 0
    ventas_hoy = 0

    fecha_hoy = datetime.now().date()

    for c in cotizaciones:

        try:

            total = float(
                c.get(
                    "total",
                    0
                ) or 0
            )

        except:

            total = 0

        estado = (
            c.get(
                "estado",
                ""
            ) or ""
        ).lower()

        # COTIZACIONES
        if estado == "cotizacion":

            total_cotizado += total

        # VENTAS
        if estado == "venta":

            total_ventas += total

            fecha = c.get(
                "fecha"
            )

            if fecha:

                try:

                    fecha_texto = str(
                        fecha
                    )[:10]

                    if fecha_texto == str(
                        fecha_hoy
                    ):

                        ventas_hoy += total

                except:

                    pass

    return render_template(
        "index.html",

        productos=productos,

        clientes=clientes,

        cotizaciones=cotizaciones,

        total_cotizado=
            total_cotizado,

        total_ventas=
            total_ventas,

        ventas_hoy=
            ventas_hoy
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

        if not nombre:

            raise Exception(
                "Debes escribir el nombre."
            )

        datos = {

            "nombre":
                nombre,

            "telefono":
                request.form.get(
                    "telefono",
                    ""
                ).strip(),

            "direccion":
                request.form.get(
                    "direccion",
                    ""
                ).strip(),

            "email":
                request.form.get(
                    "email",
                    ""
                ).strip()
        }

        (
            supabase
            .table("clientes")
            .insert(datos)
            .execute()
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

        producto = (
            obtener_o_crear_producto(

                nombre,

                descripcion,

                tipo_venta,

                precio,

                stock_minimo
            )
        )

        # ====================================================
        # INVENTARIO INICIAL OPCIONAL
        # ====================================================

        cantidad_existencias = request.form.get(
            "cantidad_existencias",
            ""
        ).strip()

        cantidad_por_existencia = request.form.get(
            "cantidad_por_existencia",
            ""
        ).strip()

        unidad = request.form.get(
            "unidad",
            ""
        ).strip().lower()

        if (
            cantidad_existencias
            and
            cantidad_por_existencia
            and
            unidad
        ):

            crear_existencias(

                producto["id"],

                int(
                    cantidad_existencias
                ),

                float(
                    cantidad_por_existencia
                ),

                unidad,

                "Inventario inicial"
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

        (
            supabase
            .table(
                "movimientos_existencias"
            )
            .delete()
            .eq(
                "producto_id",
                id
            )
            .execute()
        )

        (
            supabase
            .table(
                "existencias_inventario"
            )
            .delete()
            .eq(
                "producto_id",
                id
            )
            .execute()
        )

        (
            supabase
            .table("productos")
            .delete()
            .eq(
                "id",
                id
            )
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
        .table(
            "existencias_inventario"
        )
        .select("*")
        .order("producto_id")
        .order("numero")
        .execute()
        .data or []
    )

    movimientos = (
        supabase
        .table(
            "movimientos_existencias"
        )
        .select("*")
        .order(
            "id",
            desc=True
        )
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

        e["id"]:
            e["numero"]

        for e in existencias
    }

    mapa_productos = {

        p["id"]:
            p["nombre"]

        for p in productos
    }

    for existencia in existencias:

        existencia[
            "producto_nombre"
        ] = mapa_productos.get(

            existencia.get(
                "producto_id"
            ),

            "Producto desconocido"
        )

    for movimiento in movimientos:

        movimiento[
            "existencia_numero"
        ] = mapa_existencias.get(

            movimiento.get(
                "existencia_id"
            )
        )

        movimiento[
            "producto_nombre"
        ] = mapa_productos.get(

            movimiento.get(
                "producto_id"
            ),

            "Producto desconocido"
        )

    return render_template(

        "inventario.html",

        existencias=existencias,

        movimientos=movimientos,

        productos=productos
    )


# ============================================================
# ENTRADA DE INVENTARIO
# ============================================================

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

            producto = (
                obtener_o_crear_producto(

                    producto_nombre,

                    descripcion,

                    tipo_venta,

                    precio,

                    stock_minimo
                )
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


# ============================================================
# ELIMINAR EXISTENCIA
# ============================================================

@app.route(
    "/eliminar-existencia/<int:id>",
    methods=["POST"]
)
def eliminar_existencia(id):

    try:

        existencia = (
            supabase
            .table(
                "existencias_inventario"
            )
            .select("*")
            .eq(
                "id",
                id
            )
            .limit(1)
            .execute()
        )

        if not existencia.data:

            raise Exception(
                "La existencia no existe."
            )

        existencia = (
            existencia.data[0]
        )

        producto_id = (
            existencia[
                "producto_id"
            ]
        )

        (
            supabase
            .table(
                "movimientos_existencias"
            )
            .delete()
            .eq(
                "existencia_id",
                id
            )
            .execute()
        )

        (
            supabase
            .table(
                "existencias_inventario"
            )
            .delete()
            .eq(
                "id",
                id
            )
            .execute()
        )

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


# ============================================================
# ELIMINAR UN MOVIMIENTO
# ============================================================

@app.route(
    "/eliminar-movimiento/<int:id>",
    methods=["POST"]
)
def eliminar_movimiento(id):

    try:

        (
            supabase
            .table(
                "movimientos_existencias"
            )
            .delete()
            .eq(
                "id",
                id
            )
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


# ============================================================
# LIMPIAR TODOS LOS MOVIMIENTOS
# ============================================================

@app.route(
    "/limpiar-movimientos",
    methods=["POST"]
)
def limpiar_movimientos():

    try:

        (
            supabase
            .table(
                "movimientos_existencias"
            )
            .delete()
            .neq(
                "id",
                0
            )
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
# NUEVA COTIZACIÓN
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

    return render_template(

        "nueva_cotizacion.html",

        clientes=clientes,

        productos=productos
    )


# ============================================================
# GUARDAR COTIZACIÓN
# ============================================================

@app.route(
    "/guardar-cotizacion",
    methods=["POST"]
)
def guardar_cotizacion():

    try:

        cliente_nombre = request.form.get(
            "cliente_nombre",
            ""
        ).strip()

        if not cliente_nombre:

            raise Exception(
                "Debes escribir el cliente."
            )

        cliente = (
            obtener_o_crear_cliente(
                cliente_nombre
            )
        )

        tipo = request.form.get(
            "tipo",
            "cotizacion"
        ).strip().lower()

        if tipo not in [
            "cotizacion",
            "venta"
        ]:

            tipo = "cotizacion"

        observaciones = request.form.get(
            "observaciones",
            ""
        ).strip()

        detalle = request.form.get(
            "detalle",
            ""
        ).strip()

        total = request.form.get(
            "total",
            "0"
        )

        try:

            total = float(total)

        except:

            total = 0

        numero = numero_siguiente(
            "cotizaciones",
            "numero"
        )

        datos = {

            "numero":
                numero,

            "cliente_id":
                cliente["id"],

            "tipo":
                tipo,

            "estado":
                "cotizacion"
                if tipo == "cotizacion"
                else "venta",

            "total":
                total,

            "observaciones":
                observaciones,

            "detalle":
                detalle
        }

        # ====================================================
        # SOLO COTIZACIÓN
        # ====================================================

        if tipo == "cotizacion":

            (
                supabase
                .table(
                    "cotizaciones"
                )
                .insert(datos)
                .execute()
            )

            return redirect(
                url_for("historial")
            )

        # ====================================================
        # VENTA DIRECTA
        # ====================================================

        # Si el formulario envía producto_id y cantidad,
        # se puede descontar automáticamente.

        producto_id = request.form.get(
            "producto_id"
        )

        cantidad = request.form.get(
            "cantidad"
        )

        if producto_id and cantidad:

            try:

                cantidad = float(
                    cantidad
                )

            except:

                cantidad = 0

            disponible = stock_disponible(
                int(producto_id)
            )

            if disponible < cantidad:

                raise Exception(
                    "No hay suficiente stock para realizar la venta."
                )

        respuesta = (
            supabase
            .table(
                "cotizaciones"
            )
            .insert(datos)
            .execute()
        )

        if respuesta.data:

            venta = (
                respuesta.data[0]
            )

            if producto_id and cantidad:

                descontar_existencia(

                    int(producto_id),

                    float(cantidad),

                    str(
                        venta.get(
                            "numero"
                        )
                    ),

                    "Venta directa"
                )

        return redirect(
            url_for("historial")
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
        .order(
            "id",
            desc=True
        )
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

        c["id"]:
            c["nombre"]

        for c in clientes
    }

    for cotizacion in cotizaciones:

        cotizacion[
            "cliente_nombre"
        ] = mapa_clientes.get(

            cotizacion.get(
                "cliente_id"
            ),

            "Sin cliente"
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
def ver_cotizacion(id):

    respuesta = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq(
            "id",
            id
        )
        .limit(1)
        .execute()
    )

    if not respuesta.data:

        return (
            "Cotización no encontrada",
            404
        )

    cotizacion = (
        respuesta.data[0]
    )

    cliente = None

    if cotizacion.get(
        "cliente_id"
    ):

        respuesta_cliente = (
            supabase
            .table("clientes")
            .select("*")
            .eq(
                "id",
                cotizacion[
                    "cliente_id"
                ]
            )
            .limit(1)
            .execute()
        )

        if respuesta_cliente.data:

            cliente = (
                respuesta_cliente.data[0]
            )

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
            .eq(
                "id",
                id
            )
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
            .eq(
                "id",
                id
            )
            .limit(1)
            .execute()
        )

        if not respuesta.data:

            raise Exception(
                "La cotización no existe."
            )

        cotizacion = (
            respuesta.data[0]
        )

        estado = (
            cotizacion.get(
                "estado",
                ""
            ) or ""
        ).lower()

        if estado == "venta":

            raise Exception(
                "Esta cotización ya fue convertida en venta."
            )

        # ====================================================
        # DETALLE
        # ====================================================

        detalle = cotizacion.get(
            "detalle",
            ""
        )

        # ====================================================
        # ACTUALIZAR ESTADO
        # ====================================================

        (
            supabase
            .table("cotizaciones")
            .update({

                "estado":
                    "venta",

                "tipo":
                    "venta"

            })
            .eq(
                "id",
                id
            )
            .execute()
        )

        return redirect(
            url_for("historial")
        )

    except Exception as e:

        return (
            f"Error al pasar a venta: {e}",
            500
        )


# ============================================================
# VENTAS
# ============================================================

@app.route("/ventas")
def ventas():

    ventas_lista = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq(
            "estado",
            "venta"
        )
        .order(
            "id",
            desc=True
        )
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

        c["id"]:
            c["nombre"]

        for c in clientes
    }

    for venta in ventas_lista:

        venta[
            "cliente_nombre"
        ] = mapa_clientes.get(

            venta.get(
                "cliente_id"
            ),

            "Sin cliente"
        )

    return render_template(

        "ventas.html",

        ventas=ventas_lista
    )


# ============================================================
# CAJA
# ============================================================

@app.route("/caja")
def caja():

    ventas_lista = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq(
            "estado",
            "venta"
        )
        .order(
            "id",
            desc=True
        )
        .execute()
        .data or []
    )

    total = 0

    for venta in ventas_lista:

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

        ventas=ventas_lista,

        total=total
    )


# ============================================================
# REPORTES
# ============================================================

@app.route("/reportes")
def reportes():

    cotizaciones = (
        supabase
        .table("cotizaciones")
        .select("*")
        .execute()
        .data or []
    )

    total_cotizaciones = 0
    total_ventas = 0

    cantidad_cotizaciones = 0
    cantidad_ventas = 0

    for c in cotizaciones:

        try:

            total = float(
                c.get(
                    "total",
                    0
                ) or 0
            )

        except:

            total = 0

        estado = (
            c.get(
                "estado",
                ""
            ) or ""
        ).lower()

        if estado == "cotizacion":

            total_cotizaciones += total

            cantidad_cotizaciones += 1

        elif estado == "venta":

            total_ventas += total

            cantidad_ventas += 1

    return render_template(

        "reportes.html",

        total_cotizaciones=
            total_cotizaciones,

        total_ventas=
            total_ventas,

        cantidad_cotizaciones=
            cantidad_cotizaciones,

        cantidad_ventas=
            cantidad_ventas
    )


# ============================================================
# EJECUTAR
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
