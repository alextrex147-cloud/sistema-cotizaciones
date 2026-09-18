let items = [];


/* =========================================================
   INICIO
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const tipo =
            document.getElementById(
                "tipo"
            );


        if (tipo) {

            actualizarTipo();

        }


        const cliente =
            document.getElementById(
                "cliente_nombre"
            );


        const telefono =
            document.getElementById(
                "cliente_telefono"
            );


        if (cliente) {

            cliente.addEventListener(
                "change",
                function () {

                    const opciones =
                        document.querySelectorAll(
                            "#lista_clientes option"
                        );


                    for (
                        const opcion
                        of opciones
                    ) {

                        if (
                            opcion.value ===
                            cliente.value
                        ) {

                            if (telefono) {

                                telefono.value =
                                    opcion.dataset
                                        .telefono ||
                                    "";

                            }

                            break;

                        }

                    }

                }
            );

        }


        const precio =
            document.getElementById(
                "precio"
            );


        if (precio) {

            precio.addEventListener(
                "keydown",
                function (e) {

                    if (
                        e.key ===
                        "Enter"
                    ) {

                        e.preventDefault();

                        agregarProducto();

                    }

                }
            );

        }


        cargarItemsExistentes();

    }
);


/* =========================================================
   ACTUALIZAR TIPO
   ========================================================= */

function actualizarTipo() {

    const tipo =
        document.getElementById(
            "tipo"
        );


    const campo =
        document.getElementById(
            "campo-medida"
        );


    const texto =
        document.getElementById(
            "texto-medida"
        );


    const medida =
        document.getElementById(
            "medida"
        );


    if (
        !tipo ||
        !campo
    ) {

        return;

    }


    if (
        tipo.value ===
        "normal"
    ) {

        campo.style.display =
            "none";


        if (medida) {

            medida.value =
                "";

        }


        return;

    }


    campo.style.display =
        "block";


    if (
        tipo.value ===
        "metros"
    ) {

        if (texto) {

            texto.textContent =
                "Metros por producto";

        }


        if (medida) {

            medida.placeholder =
                "Ejemplo: 4";

        }

    }


    if (
        tipo.value ===
        "kilos"
    ) {

        if (texto) {

            texto.textContent =
                "Kilos por producto";

        }


        if (medida) {

            medida.placeholder =
                "Ejemplo: 10";

        }

    }

}


/* =========================================================
   CAMBIO DE TIPO
   ========================================================= */

document.addEventListener(
    "change",
    function (e) {

        if (
            e.target &&
            e.target.id ===
                "tipo"
        ) {

            actualizarTipo();

        }

    }
);


/* =========================================================
   AGREGAR PRODUCTO
   ========================================================= */

function agregarProducto() {

    const nombreCampo =
        document.getElementById(
            "nombre_producto"
        );


    const cantidadCampo =
        document.getElementById(
            "cantidad"
        );


    const tipoCampo =
        document.getElementById(
            "tipo"
        );


    const medidaCampo =
        document.getElementById(
            "medida"
        );


    const precioCampo =
        document.getElementById(
            "precio"
        );


    if (!nombreCampo) {

        alert(
            "No se encontró el campo Producto."
        );


        return false;

    }


    const nombre =
        nombreCampo.value.trim();


    const cantidad =
        parseFloat(
            cantidadCampo.value
        );


    const tipo =
        tipoCampo.value;


    const precio =
        parseFloat(
            precioCampo.value
        );


    let medida = null;


    if (!nombre) {

        alert(
            "Escribe el nombre del producto."
        );


        nombreCampo.focus();


        return false;

    }


    if (
        Number.isNaN(
            cantidad
        ) ||
        cantidad <= 0
    ) {

        alert(
            "La cantidad debe ser mayor que 0."
        );


        cantidadCampo.focus();


        return false;

    }


    if (
        Number.isNaN(
            precio
        ) ||
        precio < 0
    ) {

        alert(
            "Escribe el precio."
        );


        precioCampo.focus();


        return false;

    }


    if (
        tipo === "metros" ||
        tipo === "kilos"
    ) {

        medida =
            parseFloat(
                medidaCampo.value
            );


        if (
            Number.isNaN(
                medida
            ) ||
            medida <= 0
        ) {

            if (
                tipo ===
                "metros"
            ) {

                alert(
                    "Escribe los metros por producto."
                );

            } else {

                alert(
                    "Escribe los kilos por producto."
                );

            }


            medidaCampo.focus();


            return false;

        }

    }


    let total;


    if (
        tipo === "metros" ||
        tipo === "kilos"
    ) {

        total =
            cantidad *
            medida *
            precio;

    } else {

        total =
            cantidad *
            precio;

    }


    items.push({

        producto_id:
            null,

        nombre_producto:
            nombre,

        cantidad:
            cantidad,

        tipo:
            tipo,

        medida:
            medida,

        precio:
            precio,

        total:
            Number(
                total.toFixed(2)
            )

    });


    mostrarItems();


    /* LIMPIAR CAMPOS */

    nombreCampo.value =
        "";


    cantidadCampo.value =
        "1";


    precioCampo.value =
        "";


    if (medidaCampo) {

        medidaCampo.value =
            "1";

    }


    actualizarTipo();


    nombreCampo.focus();


    return true;

}


/* =========================================================
   MOSTRAR PRODUCTOS
   ========================================================= */

function mostrarItems() {

    const body =
        document.getElementById(
            "items-body"
        );


    if (!body) {

        return;

    }


    body.innerHTML =
        "";


    let totalGeneral =
        0;


    items.forEach(
        function (
            item,
            index
        ) {

            totalGeneral +=
                Number(
                    item.total
                );


            const fila =
                document.createElement(
                    "tr"
                );


            let medidaTexto =
                "-";


            if (
                item.medida !==
                null &&
                item.medida !==
                undefined &&
                item.medida !== ""
            ) {

                if (
                    item.tipo ===
                    "metros"
                ) {

                    medidaTexto =
                        item.medida +
                        " m";

                } else if (
                    item.tipo ===
                    "kilos"
                ) {

                    medidaTexto =
                        item.medida +
                        " kg";

                } else {

                    medidaTexto =
                        item.medida;

                }

            }


            fila.innerHTML = `

                <td>
                    ${escapeHtml(
                        item.nombre_producto
                    )}
                </td>

                <td>
                    ${item.cantidad}
                </td>

                <td>
                    ${escapeHtml(
                        item.tipo
                    )}
                </td>

                <td>
                    ${medidaTexto}
                </td>

                <td>
                    ${Number(
                        item.precio
                    ).toFixed(2)}
                    Bs
                </td>

                <td>
                    ${Number(
                        item.total
                    ).toFixed(2)}
                    Bs
                </td>

                <td>

                    <button
                        type="button"
                        class="btn rojo pequeño"
                        onclick="eliminarItem(${index})"
                    >
                        🗑️
                    </button>

                </td>

            `;


            body.appendChild(
                fila
            );

        }
    );


    const total =
        document.getElementById(
            "total-general"
        );


    if (total) {

        total.textContent =
            totalGeneral.toFixed(2);

    }


    sincronizarFormulario();

}


/* =========================================================
   ELIMINAR PRODUCTO
   ========================================================= */

function eliminarItem(
    index
) {

    if (
        index < 0 ||
        index >= items.length
    ) {

        return;

    }


    items.splice(
        index,
        1
    );


    mostrarItems();

}


/* =========================================================
   SINCRONIZAR JSON
   ========================================================= */

function sincronizarFormulario() {

    const campo =
        document.getElementById(
            "items_json"
        );


    if (campo) {

        campo.value =
            JSON.stringify(
                items
            );

    }

}


/* =========================================================
   PREPARAR FORMULARIO
   ========================================================= */

function prepararFormulario() {

    const nombreCampo =
        document.getElementById(
            "nombre_producto"
        );


    const precioCampo =
        document.getElementById(
            "precio"
        );


    /*
       Si el usuario escribió un producto
       pero no presionó ENTER, lo agregamos
       automáticamente antes de guardar.
    */

    if (

        nombreCampo &&

        (

            nombreCampo.value
                .trim() !== ""

            ||

            (
                precioCampo &&

                precioCampo.value
                    .trim() !== ""
            )

        )

    ) {

        if (
            !agregarProducto()
        ) {

            return false;

        }

    }


    if (
        items.length === 0
    ) {

        alert(
            "Agrega al menos un producto antes de guardar."
        );


        return false;

    }


    sincronizarFormulario();


    return true;

}


/* =========================================================
   GUARDAR COMO VENTA
   ========================================================= */

function guardarComoVenta() {

    if (
        !prepararFormulario()
    ) {

        return;

    }


    const clienteNombre =
        document.getElementById(
            "cliente_nombre"
        );


    const clienteTelefono =
        document.getElementById(
            "cliente_telefono"
        );


    const ventaClienteNombre =
        document.getElementById(
            "venta_cliente_nombre"
        );


    const ventaClienteTelefono =
        document.getElementById(
            "venta_cliente_telefono"
        );


    const ventaItems =
        document.getElementById(
            "venta_items_json"
        );


    const formularioVenta =
        document.getElementById(
            "form-venta-oculto"
        );


    if (
        !formularioVenta
    ) {

        alert(
            "No se encontró el formulario de venta."
        );


        return;

    }


    if (
        ventaClienteNombre &&
        clienteNombre
    ) {

        ventaClienteNombre.value =
            clienteNombre.value;

    }


    if (
        ventaClienteTelefono &&
        clienteTelefono
    ) {

        ventaClienteTelefono.value =
            clienteTelefono.value;

    }


    if (
        ventaItems
    ) {

        ventaItems.value =
            JSON.stringify(
                items
            );

    }


    formularioVenta.submit();

}


/* =========================================================
   CARGAR PRODUCTOS EXISTENTES
   ========================================================= */

function cargarItemsExistentes() {

    if (
        typeof detallesIniciales ===
        "undefined"
    ) {

        return;

    }


    if (
        !Array.isArray(
            detallesIniciales
        )
    ) {

        return;

    }


    items =
        detallesIniciales.map(
            function (item) {

                const cantidad =
                    Number(
                        item.cantidad
                    );


                const precio =
                    Number(
                        item.precio
                    );


                let medida =
                    null;


                if (
                    item.medida !==
                    null &&
                    item.medida !==
                    undefined &&
                    item.medida !== ""
                ) {

                    medida =
                        Number(
                            item.medida
                        );

                }


                let total =
                    Number(
                        item.total
                    );


                /*
                   Si el total guardado
                   no es válido, recalcular.
                */

                if (
                    Number.isNaN(
                        total
                    )
                ) {

                    if (
                        item.tipo ===
                        "metros" ||
                        item.tipo ===
                        "kilos"
                    ) {

                        total =
                            cantidad *
                            medida *
                            precio;

                    } else {

                        total =
                            cantidad *
                            precio;

                    }

                }


                return {

                    producto_id:
                        null,

                    nombre_producto:
                        item.nombre_producto ||
                        "",

                    cantidad:
                        cantidad,

                    tipo:
                        item.tipo ||
                        "normal",

                    medida:
                        medida,

                    precio:
                        precio,

                    total:
                        Number(
                            total.toFixed(2)
                        )

                };

            }
        );


    mostrarItems();

}


/* =========================================================
   SEGURIDAD
   ========================================================= */

function escapeHtml(
    text
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        text;


    return div.innerHTML;

}
