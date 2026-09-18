let items = [];


document.addEventListener(
    "DOMContentLoaded",
    function () {

        const tipo =
            document.getElementById("tipo");

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


                    for (const opcion of opciones) {

                        if (
                            opcion.value ===
                            cliente.value
                        ) {

                            telefono.value =
                                opcion.dataset.telefono ||
                                "";

                            break;
                        }
                    }

                }
            );

        }


        cargarItemsExistentes();

    }
);


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


    if (!tipo || !campo) {
        return;
    }


    if (tipo.value === "normal") {

        campo.style.display = "none";

    } else {

        campo.style.display = "block";


        if (
            tipo.value === "metros"
        ) {

            texto.textContent =
                "Metros por producto";

        } else {

            texto.textContent =
                "Kilos por producto";

        }

    }

}


document.addEventListener(
    "change",
    function (e) {

        if (
            e.target &&
            e.target.id === "tipo"
        ) {

            actualizarTipo();

        }

    }
);


function agregarProducto() {

    const nombre =
        document.getElementById(
            "nombre_producto"
        );


    const cantidadInput =
        document.getElementById(
            "cantidad"
        );


    const tipoInput =
        document.getElementById(
            "tipo"
        );


    const medidaInput =
        document.getElementById(
            "medida"
        );


    const precioInput =
        document.getElementById(
            "precio"
        );


    if (!nombre) {
        return;
    }


    const nombreProducto =
        nombre.value.trim();


    if (!nombreProducto) {

        alert(
            "Escribe el nombre del producto."
        );

        nombre.focus();

        return;
    }


    const cantidad =
        parseFloat(
            cantidadInput.value
        ) || 0;


    if (cantidad <= 0) {

        alert(
            "La cantidad debe ser mayor que 0."
        );

        cantidadInput.focus();

        return;
    }


    const tipo =
        tipoInput.value;


    const medida =
        parseFloat(
            medidaInput.value
        ) || 1;


    const precio =
        parseFloat(
            precioInput.value
        );


    if (
        Number.isNaN(precio) ||
        precio < 0
    ) {

        alert(
            "Escribe un precio válido."
        );

        precioInput.focus();

        return;
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

        producto_id: null,

        nombre_producto:
            nombreProducto,

        cantidad:
            cantidad,

        tipo:
            tipo,

        medida:
            tipo === "normal"
                ? null
                : medida,

        precio:
            precio,

        total:
            Number(
                total.toFixed(2)
            )

    });


    mostrarItems();


    nombre.value = "";

    cantidadInput.value = 1;

    precioInput.value = "";

    medidaInput.value = 1;


    nombre.focus();

}


function mostrarItems() {

    const body =
        document.getElementById(
            "items-body"
        );


    if (!body) {
        return;
    }


    body.innerHTML = "";


    let totalGeneral = 0;


    items.forEach(
        function (item, index) {

            totalGeneral +=
                Number(item.total);


            const fila =
                document.createElement(
                    "tr"
                );


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
                    ${
                        item.medida === null
                            ? "-"
                            : item.medida
                    }
                </td>

                <td>
                    ${Number(
                        item.precio
                    ).toFixed(2)} Bs
                </td>

                <td>
                    ${Number(
                        item.total
                    ).toFixed(2)} Bs
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


    prepararFormulario();

}


function eliminarItem(index) {

    items.splice(
        index,
        1
    );


    mostrarItems();

}


function prepararFormulario() {

    const campo =
        document.getElementById(
            "items_json"
        );


    if (campo) {

        campo.value =
            JSON.stringify(items);

    }

}


function guardarComoVenta() {

    if (items.length === 0) {

        alert(
            "Agrega al menos un producto."
        );

        return;

    }


    prepararFormulario();


    document.getElementById(
        "venta_cliente_nombre"
    ).value =
        document.getElementById(
            "cliente_nombre"
        ).value;


    document.getElementById(
        "venta_cliente_telefono"
    ).value =
        document.getElementById(
            "cliente_telefono"
        ).value;


    document.getElementById(
        "venta_items_json"
    ).value =
        JSON.stringify(items);


    document.getElementById(
        "form-venta-oculto"
    ).submit();

}


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

                return {

                    producto_id:
                        null,

                    nombre_producto:
                        item.nombre_producto,

                    cantidad:
                        Number(
                            item.cantidad
                        ),

                    tipo:
                        item.tipo,

                    medida:
                        item.medida === null ||
                        item.medida === undefined
                            ? null
                            : Number(
                                item.medida
                            ),

                    precio:
                        Number(
                            item.precio
                        ),

                    total:
                        Number(
                            item.total
                        )

                };

            }
        );


    mostrarItems();

}


function escapeHtml(text) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        text;


    return div.innerHTML;

}
