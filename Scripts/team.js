document.addEventListener('DOMContentLoaded', () => {
    const showTeamBtn = document.getElementById('showTeamBtn');
    const teamSection = document.getElementById('equipo-desarrollo');

    if (showTeamBtn && teamSection) {
        showTeamBtn.addEventListener('click', () => {
            teamSection.classList.toggle('visible-section');
        });
    }
});