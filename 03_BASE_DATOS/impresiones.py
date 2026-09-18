from conexion import supabase


def crear_impresion(tipo_documento, documento_id, numero):
    respuesta = supabase.table("impresiones").insert({
        "tipo_documento": tipo_documento,
        "documento_id": documento_id,
        "numero": numero,
        "estado": "pendiente"
    }).execute()

    if respuesta.data:
        return respuesta.data[0]

    return None


def obtener_pendiente():
    respuesta = (
        supabase
        .table("impresiones")
        .select("*")
        .eq("estado", "pendiente")
        .order("id", desc=False)
        .limit(1)
        .execute()
    )

    if respuesta.data:
        return respuesta.data[0]

    return None


def marcar_impreso(impresion_id):
    return (
        supabase
        .table("impresiones")
        .update({
            "estado": "impreso",
            "impreso_at": "now()"
        })
        .eq("id", impresion_id)
        .execute()
    )


def marcar_error(impresion_id, error):
    return (
        supabase
        .table("impresiones")
        .update({
            "estado": "error",
            "error": str(error)
        })
        .eq("id", impresion_id)
        .execute()
    )


def listar_impresiones():
    respuesta = (
        supabase
        .table("impresiones")
        .select("*")
        .order("id", desc=True)
        .execute()
    )

    return respuesta.data or []
