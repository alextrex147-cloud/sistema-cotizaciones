import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = Flask(**name**)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave-local")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
raise Exception("Faltan SUPABASE_URL y SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================

# NUMERACIÓN

# =========================================================

def numero_siguiente(prefijo, tabla):
try:
respuesta = (
supabase
.table(tabla)
.select("numero")
.order("id", desc=True)
.limit(1)
.execute()
)

```
    if not respuesta.data:
        return f"{prefijo}-0001"

    ultimo = respuesta.data[0]["numero"]

    try:
        numero = int(str(ultimo).split("-")[-1]) + 1
    except Exception:
        numero = 1

    return f"{prefijo}-{numero:04d}"

except Exception:
    return f"{prefijo}-0001"
```

# =========================================================

# CLIENTES

# =========================================================

def buscar_cliente(nombre, telefono):
if not nombre:
return None

```
consulta = (
    supabase
    .table("clientes")
    .select("*")
    .ilike("nombre", nombre)
    .limit(1)
    .execute()
)

if consulta.data:
    return consulta.data[0]

if telefono:
    consulta = (
        supabase
        .table("clientes")
        .select("*")
        .eq("telefono", telefono)
        .limit(1)
        .execute()
    )

    if consulta.data:
        return consulta.data[0]

return None
```

def obtener_o_crear_cliente(nombre, telefono, direccion, email):

```
existente = buscar_cliente(nombre, telefono)

if existente:
    return existente["id"]

nuevo = {
    "nombre": nombre,
    "telefono": telefono,
    "direccion": direccion,
    "email": email
}

respuesta = (
    supabase
    .table("clientes")
    .insert(nuevo)
    .execute()
)

if not respuesta.data:
    raise Exception("No se pudo guardar el cliente.")

return respuesta.data[0]["id"]
```

# =========================================================

# PRODUCTOS

# =========================================================

def buscar_producto(nombre):

```
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
```

def obtener_o_crear_producto(
nombre,
descripcion,
tipo_venta,
precio
):

```
existente = buscar_producto(nombre)

if existente:
    return existente

nuevo = {
    "nombre": nombre,
    "descripcion": descripcion,
    "tipo_venta": tipo_venta,
    "precio": precio,
    "stock": 0,
    "stock_minimo": 0
}

respuesta = (
    supabase
    .table("productos")
    .insert(nuevo)
    .execute()
)

if not respuesta.data:
    raise Exception("No se pudo guardar el producto.")

return respuesta.data[0]
```

# =========================================================

# EXISTENCIAS

# =========================================================

def siguiente_numero_existencia(producto_id):

```
respuesta = (
    supabase
    .table("existencias_inventario")
    .select("numero")
    .eq("producto_id", producto_id)
    .order("numero", desc=True)
    .limit(1)
    .execute()
)

if not respuesta.data:
    return 1

return int(respuesta.data[0]["numero"]) + 1
```

def crear_existencias(
producto_id,
presentacion,
cantidad_contenedores,
cantidad_por_contenedor,
unidad,
motivo="Entrada"
):

```
cantidad_contenedores = int(cantidad_contenedores)
cantidad_por_contenedor = float(cantidad_por_contenedor)

if cantidad_contenedores <= 0:
    raise Exception(
        "La cantidad de presentaciones debe ser mayor a 0."
    )

if cantidad_por_contenedor <= 0:
    raise Exception(
        "El contenido debe ser mayor a 0."
    )

if unidad not in [
    "metros",
    "kilos",
    "unidad"
]:
    raise Exception(
        "La unidad debe ser METROS, KILOS o UNIDAD."
    )

if not producto_id:
    raise Exception(
        "No se indicó el producto."
    )

numero = siguiente_numero_existencia(producto_id)

creadas = []

for i in range(cantidad_contenedores):

    datos = {
        "producto_id": producto_id,
        "tipo_presentacion": presentacion,
        "numero": numero + i,
        "cantidad_inicial": cantidad_por_contenedor,
        "cantidad_actual": cantidad_por_contenedor,
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

    supabase.table(
        "movimientos_existencias"
    ).insert({
        "existencia_id": existencia["id"],
        "producto_id": producto_id,
        "tipo": "ENTRADA",
        "cantidad": cantidad_por_contenedor,
        "descripcion": motivo
    }).execute()

actualizar_stock_general(producto_id)

return creadas
```

def obtener_existencias_producto(producto_id):

```
respuesta = (
    supabase
    .table("existencias_inventario")
    .select("*")
    .eq("producto_id", producto_id)
    .order("numero")
    .execute()
)

return respuesta.data or []
```

def actualizar_stock_general(producto_id):

```
existencias = obtener_existencias_producto(
    producto_id
)

total = 0

for existencia in existencias:

    total += float(
        existencia.get("cantidad_actual") or 0
    )

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
```

# =========================================================

# COMPROBAR STOCK

# =========================================================

def stock_disponible(
producto_id,
cantidad_necesaria,
unidad
):

```
existencias = (
    supabase
    .table("existencias_inventario")
    .select("*")
    .eq("producto_id", producto_id)
    .eq("unidad_contenido", unidad)
    .eq("estado", "disponible")
    .order("numero")
    .execute()
    .data or []
)

disponible = 0

for existencia in existencias:

    disponible += float(
        existencia.get("cantidad_actual") or 0
    )

return disponible >= float(cantidad_necesaria)
```

# =========================================================

# DESCONTAR FIFO

# =========================================================

def descontar_existencia(
producto_id,
cantidad_necesaria,
numero_venta,
unidad
):

```
cantidad_necesaria = float(
    cantidad_necesaria
)

if cantidad_necesaria <= 0:
    return

existencias = (
    supabase
    .table("existencias_inventario")
    .select("*")
    .eq("producto_id", producto_id)
    .eq("unidad_contenido", unidad)
    .eq("estado", "disponible")
    .order("numero")
    .execute()
    .data or []
)

restante = cantidad_necesaria

for existencia in existencias:

    if restante <= 0:
        break

    actual = float(
        existencia.get("cantidad_actual") or 0
    )

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
            "descripcion": f"Venta {numero_venta}"
        })
        .execute()
    )

    restante -= descuento

if restante > 0:

    raise Exception(
        f"No existe suficiente inventario de {unidad}."
    )

actualizar_stock_general(producto_id)
```

# =========================================================

# INICIO

# =========================================================

@app.route("/")
def inicio():

```
clientes = (
    supabase
    .table("clientes")
    .select("*")
    .execute()
    .data or []
)

productos = (
    supabase
    .table("productos")
    .select("*")
    .execute()
    .data or []
)

cotizaciones = (
    supabase
    .table("cotizaciones")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data or []
)

ventas = (
    supabase
    .table("ventas")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data or []
)

total_cotizado = sum(
    float(x.get("total") or 0)
    for x in cotizaciones
)

total_vendido = sum(
    float(x.get("total") or 0)
    for x in ventas
)

hoy = datetime.now().date().isoformat()

ventas_hoy = [
    x for x in ventas
    if str(x.get("fecha", ""))[:10] == hoy
]

total_hoy = sum(
    float(x.get("total") or 0)
    for x in ventas_hoy
)

stock_bajo = [
    p for p in productos
    if float(p.get("stock") or 0)
    <= float(p.get("stock_minimo") or 0)
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
```

# =========================================================

# CLIENTES

# =========================================================

@app.route("/clientes")
def clientes():

```
datos = (
    supabase
    .table("clientes")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data or []
)

return render_template(
    "clientes.html",
    clientes=datos
)
```

@app.route("/agregar-cliente", methods=["POST"])
def agregar_cliente():

```
datos = {
    "nombre": request.form.get(
        "nombre",
        ""
    ).strip(),

    "telefono": request.form.get(
        "telefono",
        ""
    ).strip(),

    "direccion": request.form.get(
        "direccion",
        ""
    ).strip(),

    "email": request.form.get(
        "email",
        ""
    ).strip()
}

if datos["nombre"]:

    supabase.table(
        "clientes"
    ).insert(datos).execute()

return redirect(
    url_for("clientes")
)
```

@app.route(
"/eliminar-cliente/[int:id](int:id)",
methods=["POST"]
)
def eliminar_cliente(id):

```
supabase.table(
    "clientes"
).delete().eq(
    "id",
    id
).execute()

return redirect(
    url_for("clientes")
)
```

# =========================================================

# PRODUCTOS

# =========================================================

@app.route("/productos")
def productos():

```
datos = (
    supabase
    .table("productos")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data or []
)

return render_template(
    "productos.html",
    productos=datos
)
```

@app.route(
"/agregar-producto",
methods=["POST"]
)
def agregar_producto():

```
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
    )

    precio = float(
        request.form.get("precio") or 0
    )

    stock_minimo = float(
        request.form.get(
            "stock_minimo"
        ) or 0
    )

    presentacion = request.form.get(
        "presentacion",
        ""
    ).strip()

    cantidad_contenedores = int(
        request.form.get(
            "cantidad_contenedores"
        ) or 0
    )

    cantidad_por_contenedor = float(
        request.form.get(
            "cantidad_por_contenedor"
        ) or 0
    )

    unidad = request.form.get(
        "unidad",
        ""
    )

    if not nombre:
        raise Exception(
            "Debes escribir el nombre del producto."
        )

    if not presentacion:
        raise Exception(
            "Debes escribir la presentación."
        )

    if unidad not in [
        "metros",
        "kilos",
        "unidad"
    ]:
        raise Exception(
            "La unidad debe ser METROS, KILOS o UNIDAD."
        )

    datos = {
        "nombre": nombre,
        "descripcion": descripcion,
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
        raise Exception(
            "No se pudo guardar el producto."
        )

    producto_id = respuesta.data[0]["id"]

    crear_existencias(
        producto_id,
        presentacion,
        cantidad_contenedores,
        cantidad_por_contenedor,
        unidad,
        "Stock inicial"
    )

    return redirect(
        url_for("productos")
    )

except Exception as e:

    return (
        f"Error al guardar producto: {e}",
        500
    )
```

@app.route(
"/eliminar-producto/[int:id](int:id)",
methods=["POST"]
)
def eliminar_producto(id):

```
try:

    existencias = (
        supabase
        .table("existencias_inventario")
        .select("id")
        .eq("producto_id", id)
        .execute()
        .data or []
    )

    for existencia in existencias:

        (
            supabase
            .table("movimientos_existencias")
            .delete()
            .eq(
                "existencia_id",
                existencia["id"]
            )
            .execute()
        )

    (
        supabase
        .table("existencias_inventario")
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
```

# =========================================================

# INVENTARIO

# =========================================================

@app.route("/inventario")
def inventario():

```
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

    existencia["producto_nombre"] = mapa_productos.get(
        existencia.get("producto_id"),
        "Producto desconocido"
    )

for movimiento in movimientos:

    movimiento["existencia_numero"] = mapa_existencias.get(
        movimiento.get("existencia_id")
    )

    movimiento["producto_nombre"] = mapa_productos.get(
        movimiento.get("producto_id"),
        "Producto desconocido"
    )

return render_template(
    "inventario.html",
    existencias=existencias,
    movimientos=movimientos,
    productos=productos
)
```

# =========================================================

# ENTRADA INVENTARIO

# =========================================================

@app.route(
"/entrada-inventario",
methods=["POST"]
)
def entrada_inventario():

```
try:

    producto_id = request.form.get(
        "producto_id"
    )

    if not producto_id:

        raise Exception(
            "No se indicó el producto de esta existencia."
        )

    producto_id = int(producto_id)

    presentacion = request.form.get(
        "presentacion",
        ""
    ).strip()

    cantidad_contenedores = int(
        request.form.get(
            "cantidad_contenedores"
        ) or 0
    )

    cantidad_por_contenedor = float(
        request.form.get(
            "cantidad_por_contenedor"
        ) or 0
    )

    unidad = request.form.get(
        "unidad",
        ""
    ).strip()

    if not presentacion:

        raise Exception(
            "Debes indicar la presentación."
        )

    crear_existencias(
        producto_id,
        presentacion,
        cantidad_contenedores,
        cantidad_por_contenedor,
        unidad,
        "Entrada"
    )

    return redirect(
        url_for("inventario")
    )

except Exception as e:

    return (
        f"Error al registrar entrada: {e}",
        500
    )
```

# =========================================================

# ELIMINAR EXISTENCIA

# =========================================================

@app.route(
"/eliminar-existencia/[int:id](int:id)",
methods=["POST"]
)
def eliminar_existencia(id):

```
try:

    existencia = (
        supabase
        .table("existencias_inventario")
        .select("*")
        .eq("id", id)
        .limit(1)
        .execute()
        .data or []
    )

    if not existencia:

        raise Exception(
            "La existencia no existe."
        )

    existencia = existencia[0]

    producto_id = existencia.get(
        "producto_id"
    )

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

    if producto_id:

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
```

# =========================================================

# ELIMINAR UN MOVIMIENTO

# =========================================================

@app.route(
"/eliminar-movimiento/[int:id](int:id)",
methods=["POST"]
)
def eliminar_movimiento(id):

```
try:

    (
        supabase
        .table("movimientos_existencias")
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
```

# =========================================================

# LIMPIAR TODOS LOS MOVIMIENTOS

# =========================================================

@app.route(
"/limpiar-movimientos",
methods=["POST"]
)
def limpiar_movimientos():

```
try:

    movimientos = (
        supabase
        .table("movimientos_existencias")
        .select("id")
        .execute()
        .data or []
    )

    for movimiento in movimientos:

        (
            supabase
            .table("movimientos_existencias")
            .delete()
            .eq(
                "id",
                movimiento["id"]
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
```

# =========================================================

# NUEVA COTIZACIÓN

# =========================================================

@app.route("/nueva-cotizacion")
def nueva_cotizacion():

```
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
    "COT",
    "cotizaciones"
)

return render_template(
    "nueva-cotizacion.html",
    clientes=clientes,
    productos=productos,
    numero=numero
)
```

# =========================================================

# GUARDAR COTIZACIÓN

# =========================================================

@app.route(
"/guardar-cotizacion",
methods=["POST"]
)
def guardar_cotizacion():

```
try:

    nombre_cliente = request.form.get(
        "cliente_nombre",
        ""
    ).strip()

    telefono = request.form.get(
        "cliente_telefono",
        ""
    ).strip()

    direccion = request.form.get(
        "cliente_direccion",
        ""
    ).strip()

    email = request.form.get(
        "cliente_email",
        ""
    ).strip()

    cliente_id = obtener_o_crear_cliente(
        nombre_cliente,
        telefono,
        direccion,
        email
    )

    nombres = request.form.getlist(
        "producto_nombre[]"
    )

    descripciones = request.form.getlist(
        "producto_descripcion[]"
    )

    tipos = request.form.getlist(
        "producto_tipo[]"
    )

    cantidades = request.form.getlist(
        "cantidad[]"
    )

    largos = request.form.getlist(
        "largo[]"
    )

    precios = request.form.getlist(
        "precio[]"
    )

    detalles = []

    subtotal_total = 0

    for i in range(len(nombres)):

        nombre = nombres[i].strip()

        if not nombre:
            continue

        tipo = (
            tipos[i]
            if i < len(tipos)
            else "unidad"
        )

        cantidad = float(
            cantidades[i] or 0
        )

        largo = (
            float(largos[i])
            if i < len(largos)
            and largos[i]
            else None
        )

        precio = float(
            precios[i] or 0
        )

        if tipo == "metro":

            subtotal = (
                cantidad
                * (largo or 0)
                * precio
            )

        else:

            subtotal = (
                cantidad
                * precio
            )

        producto = obtener_o_crear_producto(
            nombre,
            descripciones[i]
            if i < len(descripciones)
            else "",
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

    descuento = float(
        request.form.get(
            "descuento"
        ) or 0
    )

    total = max(
        subtotal_total - descuento,
        0
    )

    numero = (
        request.form.get("numero")
        or numero_siguiente(
            "COT",
            "cotizaciones"
        )
    )

    cotizacion = (
        supabase
        .table("cotizaciones")
        .insert({
            "numero": numero,
            "cliente_id": cliente_id,
            "subtotal": subtotal_total,
            "descuento": descuento,
            "total": total,
            "estado": "cotizacion",
            "observaciones": request.form.get(
                "observaciones",
                ""
            )
        })
        .execute()
    )

    if not cotizacion.data:

        raise Exception(
            "No se pudo guardar la cotización."
        )

    cotizacion_id = cotizacion.data[0]["id"]

    for detalle in detalles:

        detalle["cotizacion_id"] = cotizacion_id

        (
            supabase
            .table("detalle_cotizacion")
            .insert(detalle)
            .execute()
        )

    return redirect(
        url_for(
            "ver_cotizacion",
            id=cotizacion_id
        )
    )

except Exception as e:

    return (
        f"Error al guardar la cotización: {e}",
        500
    )
```

# =========================================================

# HISTORIAL

# =========================================================

@app.route("/historial")
def historial():

```
cotizaciones = (
    supabase
    .table("cotizaciones")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data or []
)

return render_template(
    "historial.html",
    cotizaciones=cotizaciones
)
```

# =========================================================

# VER COTIZACIÓN

# =========================================================

@app.route("/cotizacion/[int:id](int:id)")
def ver_cotizacion(id):

```
cotizacion = (
    supabase
    .table("cotizaciones")
    .select("*")
    .eq("id", id)
    .single()
    .execute()
    .data
)

detalles = (
    supabase
    .table("detalle_cotizacion")
    .select("*")
    .eq("cotizacion_id", id)
    .execute()
    .data or []
)

cliente = None

if cotizacion.get("cliente_id"):

    cliente = (
        supabase
        .table("clientes")
        .select("*")
        .eq(
            "id",
            cotizacion["cliente_id"]
        )
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
```

# =========================================================

# ELIMINAR COTIZACIÓN

# =========================================================

@app.route(
"/eliminar-cotizacion/[int:id](int:id)",
methods=["POST"]
)
def eliminar_cotizacion(id):

```
ventas_relacionadas = (
    supabase
    .table("ventas")
    .select("id")
    .eq("cotizacion_id", id)
    .execute()
    .data or []
)

if ventas_relacionadas:

    return (
        "No se puede eliminar esta cotización porque ya está relacionada con una venta.",
        400
    )

(
    supabase
    .table("detalle_cotizacion")
    .delete()
    .eq(
        "cotizacion_id",
        id
    )
    .execute()
)

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
```

# =========================================================

# PASAR COTIZACIÓN A VENTA

# =========================================================

@app.route(
"/pasar-a-venta/[int:id](int:id)",
methods=["POST"]
)
def pasar_a_venta(id):

```
try:

    cotizacion = (
        supabase
        .table("cotizaciones")
        .select("*")
        .eq("id", id)
        .single()
        .execute()
        .data
    )

    if cotizacion.get("estado") == "vendida":

        raise Exception(
            "Esta cotización ya fue convertida en venta."
        )

    detalles = (
        supabase
        .table("detalle_cotizacion")
        .select("*")
        .eq(
            "cotizacion_id",
            id
        )
        .execute()
        .data or []
    )

    if not detalles:

        raise Exception(
            "La cotización no tiene productos."
        )

    necesidades = {}

    for detalle in detalles:

        producto_id = detalle["producto_id"]

        producto = (
            supabase
            .table("productos")
            .select("*")
            .eq(
                "id",
                producto_id
            )
            .single()
            .execute()
            .data
        )

        existencias = (
            supabase
            .table("existencias_inventario")
            .select("*")
            .eq(
                "producto_id",
                producto_id
            )
            .eq(
                "estado",
                "disponible"
            )
            .order("numero")
            .execute()
            .data or []
        )

        if not existencias:

            raise Exception(
                f"No hay inventario disponible para: {producto['nombre']}"
            )

        unidad = existencias[0][
            "unidad_contenido"
        ]

        if producto["tipo_venta"] == "metro":

            cantidad_necesaria = (
                float(detalle["cantidad"])
                * float(
                    detalle["largo"] or 0
                )
            )

        else:

            cantidad_necesaria = float(
                detalle["cantidad"]
            )

        clave = (
            producto_id,
            unidad
        )

        necesidades[clave] = (
            necesidades.get(
                clave,
                0
            )
            + cantidad_necesaria
        )

    for clave, cantidad_necesaria in necesidades.items():

        producto_id, unidad = clave

        if not stock_disponible(
            producto_id,
            cantidad_necesaria,
            unidad
        ):

            producto = (
                supabase
                .table("productos")
                .select("nombre")
                .eq(
                    "id",
                    producto_id
                )
                .single()
                .execute()
                .data
            )

            raise Exception(
                f"No hay suficiente inventario de {producto['nombre']} ({unidad})."
            )

    numero = numero_siguiente(
        "VTA",
        "ventas"
    )

    forma_pago = request.form.get(
        "forma_pago",
        "Efectivo"
    )

    venta = (
        supabase
        .table("ventas")
        .insert({
            "numero": numero,
            "cotizacion_id": id,
            "cliente_id": cotizacion["cliente_id"],
            "subtotal": cotizacion["subtotal"],
            "descuento": cotizacion["descuento"],
            "total": cotizacion["total"],
            "forma_pago": forma_pago,
            "observaciones": cotizacion.get(
                "observaciones",
                ""
            )
        })
        .execute()
    )

    if not venta.data:

        raise Exception(
            "No se pudo crear la venta."
        )

    venta_id = venta.data[0]["id"]

    for detalle in detalles:

        (
            supabase
            .table("detalle_venta")
            .insert({
                "venta_id": venta_id,
                "producto_id": detalle["producto_id"],
                "producto_nombre": detalle["producto_nombre"],
                "cantidad": detalle["cantidad"],
                "largo": detalle["largo"],
                "precio": detalle["precio"],
                "subtotal": detalle["subtotal"]
            })
            .execute()
        )

        producto = (
            supabase
            .table("productos")
            .select("*")
            .eq(
                "id",
                detalle["producto_id"]
            )
            .single()
            .execute()
            .data
        )

        existencias = (
            supabase
            .table("existencias_inventario")
            .select("*")
            .eq(
                "producto_id",
                detalle["producto_id"]
            )
            .eq(
                "estado",
                "disponible"
            )
            .order("numero")
            .execute()
            .data or []
        )

        if not existencias:

            raise Exception(
                f"No hay existencias para {producto['nombre']}."
            )

        unidad = existencias[0][
            "unidad_contenido"
        ]

        if producto["tipo_venta"] == "metro":

            salida = (
                float(detalle["cantidad"])
                * float(
                    detalle["largo"] or 0
                )
            )

        else:

            salida = float(
                detalle["cantidad"]
            )

        descontar_existencia(
            detalle["producto_id"],
            salida,
            numero,
            unidad
        )

    (
        supabase
        .table("movimientos_caja")
        .insert({
            "venta_id": venta_id,
            "tipo": "INGRESO",
            "monto": cotizacion["total"],
            "forma_pago": forma_pago,
            "descripcion": f"Venta {numero}"
        })
        .execute()
    )

    (
        supabase
        .table("cotizaciones")
        .update({
            "estado": "vendida"
        })
        .eq(
            "id",
            id
        )
        .execute()
    )

    return redirect(
        url_for("ventas")
    )

except Exception as e:

    return (
        f"Error al convertir a venta: {e}",
        500
    )
```

# =========================================================

# VENTAS

# =========================================================

@app.route("/ventas")
def ventas():

```
datos = (
    supabase
    .table("ventas")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data or []
)

total = sum(
    float(x.get("total") or 0)
    for x in datos
)

return render_template(
    "ventas.html",
    ventas=datos,
    total=total
)
```

# =========================================================

# CAJA

# =========================================================

@app.route("/caja")
def caja():

```
movimientos = (
    supabase
    .table("movimientos_caja")
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
```

# =========================================================

# REPORTES

# =========================================================

@app.route("/reportes")
def reportes():

```
ventas = (
    supabase
    .table("ventas")
    .select("*")
    .execute()
    .data or []
)

cotizaciones = (
    supabase
    .table("cotizaciones")
    .select("*")
    .execute()
    .data or []
)

productos = (
    supabase
    .table("productos")
    .select("*")
    .execute()
    .data or []
)

total_ventas = sum(
    float(x.get("total") or 0)
    for x in ventas
)

total_cotizaciones = sum(
    float(x.get("total") or 0)
    for x in cotizaciones
)

return render_template(
    "reportes.html",
    ventas=ventas,
    cotizaciones=cotizaciones,
    productos=productos,
    total_ventas=total_ventas,
    total_cotizaciones=total_cotizaciones
)
```

# =========================================================

# EJECUTAR

# =========================================================

if **name** == "**main**":

```
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
