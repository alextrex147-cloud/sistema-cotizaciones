from conexion import supabase


def siguiente_numero():

    respuesta = supabase.table(
        "cotizaciones"
    ).select(
        "numero"
    ).order(
        "id",
        desc=True
    ).limit(1).execute()

    if not respuesta.data:
        return "COT-0001"

    ultimo = respuesta.data[0]["numero"]

    try:
        numero = int(
            ultimo.split("-")[1]
        ) + 1
    except Exception:
        numero = 1

    return f"COT-{numero:04d}"


def listar_cotizaciones():

    respuesta = supabase.table(
        "cotizaciones"
    ).select(
        "*, clientes(nombre, telefono)"
    ).order(
        "id",
        desc=True
    ).execute()

    return respuesta.data or []


def obtener_cotizacion(
    cotizacion_id
):

    cotizacion = supabase.table(
        "cotizaciones"
    ).select(
        "*, clientes(nombre, telefono)"
    ).eq(
        "id",
        cotizacion_id
    ).single().execute()

    detalles = supabase.table(
        "cotizacion_productos"
    ).select("*").eq(
        "cotizacion_id",
        cotizacion_id
    ).order(
        "id"
    ).execute()

    return (
        cotizacion.data,
        detalles.data or []
    )


def crear_cotizacion(
    cliente_id,
    items,
    total
):

    numero = siguiente_numero()

    cabecera = supabase.table(
        "cotizaciones"
    ).insert({
        "numero": numero,
        "cliente_id": cliente_id,
        "total": total,
        "estado": "cotizacion"
    }).execute()

    cotizacion = cabecera.data[0]

    detalles = []

    for item in items:

        detalles.append({
            "cotizacion_id":
                cotizacion["id"],

            "producto_id":
                item.get("producto_id"),

            "nombre_producto":
                item["nombre_producto"],

            "cantidad":
                item["cantidad"],

            "tipo":
                item["tipo"],

            "medida":
                item.get("medida"),

            "precio":
                item["precio"],

            "total":
                item["total"]
        })

    if detalles:

        supabase.table(
            "cotizacion_productos"
        ).insert(
            detalles
        ).execute()

    return cotizacion


def actualizar_cotizacion(
    cotizacion_id,
    cliente_id,
    items,
    total
):

    supabase.table(
        "cotizaciones"
    ).update({
        "cliente_id": cliente_id,
        "total": total
    }).eq(
        "id",
        cotizacion_id
    ).execute()

    supabase.table(
        "cotizacion_productos"
    ).delete().eq(
        "cotizacion_id",
        cotizacion_id
    ).execute()

    detalles = []

    for item in items:

        detalles.append({
            "cotizacion_id":
                cotizacion_id,

            "producto_id":
                item.get("producto_id"),

            "nombre_producto":
                item["nombre_producto"],

            "cantidad":
                item["cantidad"],

            "tipo":
                item["tipo"],

            "medida":
                item.get("medida"),

            "precio":
                item["precio"],

            "total":
                item["total"]
        })

    if detalles:

        supabase.table(
            "cotizacion_productos"
        ).insert(
            detalles
        ).execute()


def eliminar_cotizacion(
    cotizacion_id
):

    return supabase.table(
        "cotizaciones"
    ).delete().eq(
        "id",
        cotizacion_id
    ).execute()
