from .conexion import supabase


def siguiente_numero():
    respuesta = supabase.table("ventas").select(
        "numero"
    ).order(
        "id",
        desc=True
    ).limit(1).execute()

    if not respuesta.data:
        return "VTA-0001"

    ultimo = respuesta.data[0]["numero"]

    try:
        numero = int(ultimo.split("-")[1]) + 1
    except Exception:
        numero = 1

    return f"VTA-{numero:04d}"


def listar_ventas():
    respuesta = supabase.table("ventas").select(
        "*, clientes(nombre, telefono)"
    ).order(
        "id",
        desc=True
    ).execute()

    return respuesta.data or []


def obtener_venta(venta_id):
    venta = supabase.table("ventas").select(
        "*, clientes(nombre, telefono)"
    ).eq(
        "id",
        venta_id
    ).single().execute()

    detalles = supabase.table(
        "venta_productos"
    ).select("*").eq(
        "venta_id",
        venta_id
    ).order(
        "id"
    ).execute()

    return venta.data, detalles.data or []


def crear_venta(cliente_id, items, total):
    numero = siguiente_numero()

    cabecera = supabase.table("ventas").insert({
        "numero": numero,
        "cliente_id": cliente_id,
        "total": total
    }).execute()

    venta = cabecera.data[0]

    detalles = []

    for item in items:
        detalles.append({
            "venta_id": venta["id"],
            "producto_id": item.get("producto_id"),
            "nombre_producto": item["nombre_producto"],
            "cantidad": item["cantidad"],
            "tipo": item["tipo"],
            "medida": item.get("medida"),
            "precio": item["precio"],
            "total": item["total"]
        })

    if detalles:
        supabase.table(
            "venta_productos"
        ).insert(detalles).execute()

    return venta


def actualizar_venta(venta_id, cliente_id, items, total):
    supabase.table("ventas").update({
        "cliente_id": cliente_id,
        "total": total
    }).eq(
        "id",
        venta_id
    ).execute()

    supabase.table("venta_productos").delete().eq(
        "venta_id",
        venta_id
    ).execute()

    detalles = []

    for item in items:
        detalles.append({
            "venta_id": venta_id,
            "producto_id": item.get("producto_id"),
            "nombre_producto": item["nombre_producto"],
            "cantidad": item["cantidad"],
            "tipo": item["tipo"],
            "medida": item.get("medida"),
            "precio": item["precio"],
            "total": item["total"]
        })

    if detalles:
        supabase.table(
            "venta_productos"
        ).insert(detalles).execute()


def eliminar_venta(venta_id):
    return supabase.table("ventas").delete().eq(
        "id",
        venta_id
    ).execute()


def convertir_cotizacion(cotizacion_id):
    cotizacion = supabase.table("cotizaciones").select(
        "*"
    ).eq(
        "id",
        cotizacion_id
    ).single().execute().data

    detalles = supabase.table(
        "cotizacion_productos"
    ).select("*").eq(
        "cotizacion_id",
        cotizacion_id
    ).execute().data or []

    numero = siguiente_numero()

    venta = supabase.table("ventas").insert({
        "numero": numero,
        "cliente_id": cotizacion["cliente_id"],
        "total": cotizacion["total"]
    }).execute().data[0]

    nuevos = []

    for item in detalles:
        nuevos.append({
            "venta_id": venta["id"],
            "producto_id": item["producto_id"],
            "nombre_producto": item["nombre_producto"],
            "cantidad": item["cantidad"],
            "tipo": item["tipo"],
            "medida": item["medida"],
            "precio": item["precio"],
            "total": item["total"]
        })

    if nuevos:
        supabase.table(
            "venta_productos"
        ).insert(nuevos).execute()

    return venta
