/**
 * Funcionalidad para actualizar el estado de entrega de las órdenes
 * Archivo: order_delivery_status.js
 */

/**
 * Función para actualizar el estado de entrega de una orden
 * @param {number} orderId - ID de la orden
 * @param {string} newDeliveryStatus - Nuevo estado de entrega
 */
function updateOrderDeliveryStatus(orderId, newDeliveryStatus) {
    // Mostrar indicador de carga
    const selectElement = document.querySelector(`select[data-order-id="${orderId}"]`);
    const originalValue = selectElement.value;
    
    // Deshabilitar el select mientras se procesa
    selectElement.disabled = true;
    
    // Realizar la petición AJAX
    fetch('/sales/orders/update-delivery-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `order_id=${orderId}&delivery_status=${newDeliveryStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar el atributo data-delivery-status
            selectElement.setAttribute('data-delivery-status', newDeliveryStatus);
            
            // Aplicar estilos visuales según el nuevo estado
            updateDeliverySelectStyles(selectElement, newDeliveryStatus);
            
            // Si el estado es ENTREGADO o CANCELADO, deshabilitar el select
            if (newDeliveryStatus === 'E' || newDeliveryStatus === 'C') {
                selectElement.disabled = true;
            }
            
            // Mostrar mensaje de éxito
            showToast('success', data.message);
            
            // Opcional: Recargar la lista de órdenes para reflejar cambios
            // loadOrders();
            
        } else {
            // Restaurar el valor original en caso de error
            selectElement.value = originalValue;
            selectElement.disabled = false;
            showToast('error', data.message || 'Error al actualizar el estado de entrega');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Restaurar el valor original en caso de error
        selectElement.value = originalValue;
        selectElement.disabled = false;
        showToast('error', 'Error de conexión al actualizar el estado de entrega');
    });
}

/**
 * Función para actualizar los estilos visuales del select de entrega
 * @param {HTMLElement} selectElement - Elemento select
 * @param {string} newStatus - Nuevo estado
 */
function updateDeliverySelectStyles(selectElement, newStatus) {
    // Remover clases de estado anteriores
    selectElement.classList.remove('delivery-select-pending', 'delivery-select-delivered', 'delivery-select-cancelled');
    
    // Agregar nueva clase de estado
    switch(newStatus) {
        case 'P':
            selectElement.classList.add('delivery-select-pending');
            break;
        case 'E':
            selectElement.classList.add('delivery-select-delivered');
            break;
        case 'C':
            selectElement.classList.add('delivery-select-cancelled');
            break;
    }
}

/**
 * Función para obtener el token CSRF de las cookies
 * @param {string} name - Nombre de la cookie
 * @returns {string} Token CSRF
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Función para mostrar notificaciones toast
 * @param {string} type - Tipo de notificación (success, error, warning, info)
 * @param {string} message - Mensaje a mostrar
 */
function showToast(type, message) {
    // Verificar si toastr está disponible
    if (typeof toastr !== 'undefined') {
        toastr[type](message);
    } else {
        // Fallback simple si toastr no está disponible
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'error' ? 'alert-danger' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

/**
 * Función para inicializar los estilos de los selects de entrega
 * Se ejecuta cuando se carga la página
 */
function initializeDeliverySelects() {
    const deliverySelects = document.querySelectorAll('.delivery-select');
    
    deliverySelects.forEach(select => {
        const currentStatus = select.getAttribute('data-delivery-status');
        updateDeliverySelectStyles(select, currentStatus);
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeDeliverySelects();
});
