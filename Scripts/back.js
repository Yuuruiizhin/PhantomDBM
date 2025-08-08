document.addEventListener('DOMContentLoaded', () => {
    const backButton = document.getElementById('backButton');
    
    if (backButton) {
        backButton.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Verifica si hay una página anterior en el historial
            if (window.history.length > 2) {
                // Si existe, vuelve a la página anterior
                window.history.back();
            } else {
                // Si no, redirige a la página de inicio
                window.location.href = 'index.html';
            }
        });
    }
});