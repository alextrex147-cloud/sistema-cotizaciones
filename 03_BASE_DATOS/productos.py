from conexion import supabase


def listar_productos(busqueda=""):

    consulta = supabase.table(
        "productos"
    ).select("*").order(
        "nombre",
        desc=False
    )

    if busqueda:
        consulta = consulta.ilike(
            "nombre",
            f"%{busqueda}%"
        )

    respuesta = consulta.execute()

    return respuesta.data or []


def obtener_producto(producto_id):

    respuesta = supabase.table(
        "productos"
    ).select("*").eq(
        "id",
        producto_id
    ).single().execute()

    return respuesta.data


def crear_producto(
    nombre,
    precio,
    unidad
):

    respuesta = supabase.table(
        "productos"
    ).insert({
        "nombre": nombre,
        "precio": float(precio),
        "unidad": unidad
    }).execute()

    return respuesta.data[0]


def actualizar_producto(
    producto_id,
    nombre,
    precio,
    unidad
):

    respuesta = supabase.table(
        "productos"
    ).update({
        "nombre": nombre,
        "precio": float(precio),
        "unidad": unidad
    }).eq(
        "id",
        producto_id
    ).execute()

    return respuesta.data


def eliminar_producto(producto_id):

    return supabase.table(
        "productos"
    ).delete().eq(
        "id",
        producto_id
    ).execute()
