let items = [];


document.addEventListener("DOMContentLoaded", function () {

    const tipo = document.getElementById("tipo");

    if (tipo) {
        actualizarTipo();
    }


    const cliente = document.getElementById("cliente_nombre");
    const telefono = document.getElementById("cliente_telefono");

    if (cliente) {

        cliente.addEventListener("change", function () {

            const opciones =
                document.querySelectorAll("#lista_clientes option");

            for (const opcion of opciones) {

                if (opcion.value === cliente.value) {

                    telefono.value =
                        opcion.dataset.telefono || "";

                    break;
                }
            }
        });
    }


    const precio = document.getElementById("precio");

    if (precio) {

        precio.addEventListener("keydown", function (e) {

            if (e.key === "Enter") {

                e.preventDefault();

                agregarProducto();
            }
        });
    }


    cargarItemsExistentes();
});


function actualizarTipo() {

    const tipo = document.getElementById("tipo");
    const campo = document.getElementById("campo-medida");
    const texto = document.getElementById("texto-medida");
    const medida = document.getElementById("medida");

    if (!tipo || !campo) {
        return;
    }


    if (tipo.value === "normal") {

        campo.style.display = "none";

        if (medida) {
            medida.value = "";
        }

        return;
    }


    campo.style.display = "block";


    if (tipo.value === "metros") {

        texto.textContent = "Metros por producto";

        medida.placeholder = "Ejemplo: 4";

    }


    if (tipo.value === "kilos") {

        texto.textContent = "Kilos por producto";

        medida.placeholder = "Ejemplo: 10";

    }
}


document.addEventListener("change", function (e) {

    if (e.target && e.target.id === "tipo") {

        actualizarTipo();
    }
});


function agregarProducto() {

    const nombreCampo =
        document.getElementById("nombre_producto");

    const cantidadCampo =
        document.getElementById("cantidad");

    const tipoCampo =
        document.getElementById("tipo");

    const medidaCampo =
        document.getElementById("medida");

    const precioCampo =
        document.getElementById("precio");


    if (!nombreCampo) {

        alert("No se encontró el campo Producto.");

        return false;
    }


    const nombre =
        nombreCampo.value.trim();


    const cantidad =
        parseFloat(cantidadCampo.value);


    const tipo =
        tipoCampo.value;


    const precio =
        parseFloat(precioCampo.value);


    let medida = null;


    if (!nombre) {

        alert("Escribe el nombre del producto.");

        nombreCampo.focus();

        return false;
    }


    if (
        Number.isNaN(cantidad) ||
        cantidad <= 0
    ) {

        alert("La cantidad debe ser mayor que 0.");

        cantidadCampo.focus();

        return false;
    }


    if (
        Number.isNaN(precio) ||
        precio < 0
    ) {

        alert("Escribe el precio.");

        precioCampo.focus();

        return false;
    }


    if (
        tipo === "metros" ||
        tipo === "kilos"
    ) {

        medida =
            parseFloat(medidaCampo.value);


        if (
            Number.isNaN(medida) ||
            medida <= 0
        ) {

            if (tipo === "metros") {

                alert("Escribe los metros por producto.");

            } else {

                alert("Escribe los kilos por producto.");
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

        producto_id: null,

        nombre_producto: nombre,

        cantidad: cantidad,

        tipo: tipo,

        medida: medida,

        precio: precio,

        total: Number(total.toFixed(2))

    });


    mostrarItems();


    nombreCampo.value = "";

    cantidadCampo.value = "1";

    precioCampo.value = "";

    medidaCampo.value = "1";


    actualizarTipo();


    nombreCampo.focus();


    return true;
}


function mostrarItems() {

    const body =
        document.getElementById("items-body");


    if (!body) {
        return;
    }


    body.innerHTML = "";


    let totalGeneral = 0;


    items.forEach(function (item, index) {

        totalGeneral += Number(item.total);


        const fila =
            document.createElement("tr");


        let medidaTexto = "-";


        if (item.medida !== null) {

            if (item.tipo === "metros") {

                medidaTexto =
                    item.medida + " m";

            } else if (item.tipo === "kilos") {

                medidaTexto =
                    item.medida + " kg";

            } else {

                medidaTexto =
                    item.medida;
            }
        }


        fila.innerHTML = `

            <td>
                ${escapeHtml(item.nombre_producto)}
            </td>

            <td>
                ${item.cantidad}
            </td>

            <td>
                ${escapeHtml(item.tipo)}
            </td>

            <td>
                ${medidaTexto}
            </td>

            <td>
                ${Number(item.precio).toFixed(2)} Bs
            </td>

            <td>
                ${Number(item.total).toFixed(2)} Bs
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


        body.appendChild(fila);

    });


    const total =
        document.getElementById("total-general");


    if (total) {

        total.textContent =
            totalGeneral.toFixed(2);
    }


    sincronizarFormulario();
}


function eliminarItem(index) {

    items.splice(index, 1);

    mostrarItems();
}


function sincronizarFormulario() {

    const campo =
        document.getElementById("items_json");


    if (campo) {

        campo.value =
            JSON.stringify(items);
    }
}


function prepararFormulario() {

    const nombreCampo =
        document.getElementById("nombre_producto");

    const precioCampo =
        document.getElementById("precio");


    if (
        nombreCampo &&
        (
            nombreCampo.value.trim() !== "" ||
            (
                precioCampo &&
                precioCampo.value.trim() !== ""
            )
        )
    ) {

        if (!agregarProducto()) {

            return false;
        }
    }


    if (items.length === 0) {

        alert(
            "Agrega al menos un producto antes de guardar."
        );

        return false;
    }


    sincronizarFormulario();


    return true;
}


function guardarComoVenta() {

    if (!prepararFormulario()) {

        return;
    }


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
        !Array.isArray(detallesIniciales)
    ) {

        return;
    }


    items =
        detallesIniciales.map(function (item) {

            return {

                producto_id: null,

                nombre_producto:
                    item.nombre_producto,

                cantidad:
                    Number(item.cantidad),

                tipo:
                    item.tipo,

                medida:
                    item.medida === null
                        ? null
                        : Number(item.medida),

                precio:
                    Number(item.precio),

                total:
                    Number(item.total)

            };

        });


    mostrarItems();
}


function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text;

    return div.innerHTML;
}
