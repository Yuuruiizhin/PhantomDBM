document.getElementById('AutoScrollButton').addEventListener('click', function(event) {
    // Prevenir el comportamiento por defecto del enlace
    event.preventDefault();

    // Obtener el destino
    const destino = document.querySelector(this.getAttribute('href'));
    
    // Hacer scroll suavemente hacia la sección
    destino.scrollIntoView({ behavior: 'smooth' });
});