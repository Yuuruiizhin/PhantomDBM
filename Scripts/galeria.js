document.addEventListener('DOMContentLoaded', () => {
    const galeriaTrack = document.querySelector('.galeria-track');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const pageInfo = document.getElementById('page-info');
    const galeriaCards = document.querySelectorAll('.galeria-card');
    const modal = document.getElementById('modal-zoom');
    const modalImage = document.getElementById('modal-image');
    const closeBtn = document.querySelector('.close-btn');

    let currentPage = 1;
    const totalPages = 4;
    const transitionDuration = 700; // Misma duración que en CSS

    // Mapeo de nombres de archivo de miniaturas a sus extensiones originales
    // Basado en la información que proporcionaste.
    const originalFileExtensions = {
        'galeria_1': 'webp',
        'galeria_2': 'webp',
        'galeria_3': 'webp',
        'galeria_4': 'webp',
        'galeria_5': 'webp',
        'galeria_6': 'webp',
        'galeria_7': 'webp',
        'galeria_8': 'webp',
        'galeria_9': 'png',
        'galeria_10': 'png',
        'galeria_11': 'png',
        'galeria_12': 'webp'
    };

    function updateGallery() {
        galeriaTrack.style.transform = `translateX(-${(currentPage - 1) * 100}%)`;
        pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
        prevBtn.disabled = currentPage === 1;
        nextBtn.disabled = currentPage === totalPages;
    }

    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            updateGallery();
        }
    });

    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            updateGallery();
        }
    });

    galeriaCards.forEach(card => {
        card.addEventListener('click', () => {
            const imgSrcMiniatura = card.querySelector('img').src;
            // Extraer el nombre de la imagen (ej: "galeria_1") de la ruta de la miniatura
            const filenameWithExt = imgSrcMiniatura.split('/').pop();
            const filename = filenameWithExt.split('.')[0];
            
            // Obtener la extensión original del mapa que creamos
            const originalExt = originalFileExtensions[filename];
            
            // Construir la nueva ruta a la imagen original, con su extensión correcta
            const imgSrcOriginal = `../Img/Galeria/${filename}.${originalExt}`;
            
            modalImage.src = imgSrcOriginal;
            modal.classList.add('active');
        });
    });

    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    updateGallery(); // Inicializa la galería en la primera página
});