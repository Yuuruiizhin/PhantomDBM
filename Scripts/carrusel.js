document.addEventListener('DOMContentLoaded', () => {
    // Carrusel automático
    let actual = 0;
    const slides = document.querySelectorAll('.carrusel img');
    const carruselContainer = document.querySelector('.carrusel');

    if (slides.length > 0) {
        slides[actual].classList.add('activo');
        setInterval(() => {
            slides[actual].classList.remove('activo');
            actual = (actual + 1) % slides.length;
            slides[actual].classList.add('activo');
        }, 3000);
    }

    // Agregar evento de clic al contenedor del carrusel
    carruselContainer.addEventListener('click', () => {
        const imagenActiva = document.querySelector('.carrusel img.activo');
        if (imagenActiva) {
            mostrar(imagenActiva);
        }
    });
});

// Función para mostrar imagen grande
function mostrar(img) {
    const modal = document.getElementById("modal");
    const imagenGrande = document.getElementById("imagenGrande");
    if (modal && imagenGrande) {
        imagenGrande.src = img.src;
        modal.style.display = "flex";
    }
}

// Función para cerrar modal
function cerrarModal() {
    const modal = document.getElementById("modal");
    if (modal) {
        modal.style.display = "none";
    }
}