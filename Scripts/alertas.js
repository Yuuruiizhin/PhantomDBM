document.addEventListener('DOMContentLoaded', function() {
    // Selecciona el formulario en la página actual.
    // Usamos el selector universal para encontrar cualquiera de los dos formularios.
    const form = document.querySelector('.contact-form') || document.querySelector('.contact-form-extended');

    // Verifica si se encontró un formulario antes de agregar el event listener.
    if (form) {
        form.addEventListener('submit', function(event) {
            // Evita que el formulario se envíe de forma predeterminada
            event.preventDefault();

            // Obtiene los campos de entrada
            const nombre = document.getElementById('nombre').value.trim();
            const email = document.getElementById('email').value.trim();
            const mensaje = document.getElementById('mensaje').value.trim();
            
            // Si el formulario tiene un campo de 'asunto', lo obtiene también
            let asunto = '';
            const asuntoInput = document.getElementById('asunto');
            if (asuntoInput) {
                asunto = asuntoInput.value.trim();
            }

            // Comprueba si los campos obligatorios están vacíos
            if (nombre === '' || email === '' || mensaje === '' || (asuntoInput && asunto === '')) {
                alert("Por favor, llene todos los campos.");
            } else {
                alert("¡Mensaje enviado con éxito!");
                // Aquí podrías agregar el código para enviar el formulario, por ejemplo:
                // form.submit();
            }
        });
    }
});