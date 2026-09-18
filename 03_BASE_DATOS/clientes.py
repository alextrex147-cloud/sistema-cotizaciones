from conexion import supabase


def listar_clientes(busqueda=""):

    consulta = supabase.table(
        "clientes"
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


def obtener_cliente(cliente_id):

    respuesta = supabase.table(
        "clientes"
    ).select("*").eq(
        "id",
        cliente_id
    ).single().execute()

    return respuesta.data


def buscar_por_nombre(nombre):

    respuesta = supabase.table(
        "clientes"
    ).select("*").ilike(
        "nombre",
        nombre
    ).limit(1).execute()

    if respuesta.data:
        return respuesta.data[0]

    return None


def crear_o_actualizar_cliente(
    nombre,
    telefono
):

    existente = buscar_por_nombre(
        nombre
    )

    if existente:

        respuesta = supabase.table(
            "clientes"
        ).update({
            "telefono": telefono
        }).eq(
            "id",
            existente["id"]
        ).execute()

        if respuesta.data:
            return respuesta.data[0]

        return existente

    respuesta = supabase.table(
        "clientes"
    ).insert({
        "nombre": nombre,
        "telefono": telefono
    }).execute()

    return respuesta.data[0]


def actualizar_cliente(
    cliente_id,
    nombre,
    telefono
):

    respuesta = supabase.table(
        "clientes"
    ).update({
        "nombre": nombre,
        "telefono": telefono
    }).eq(
        "id",
        cliente_id
    ).execute()

    return respuesta.data


def eliminar_cliente(cliente_id):

    return supabase.table(
        "clientes"
    ).delete().eq(
        "id",
        cliente_id
    ).execute()
