// ===== EFECTOS LIMPIOS PARA DASHBOARD =====

document.addEventListener('DOMContentLoaded', function() {
    
    // Efecto de entrada suave para las tarjetas
    const cards = document.querySelectorAll('.small-box');
    
    function animateCards() {
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 150);
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
        });
    }
    
    // Ejecutar animación después de un breve delay
    setTimeout(animateCards, 200);
    
    // Efecto de hover suave para las tarjetas
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Efecto de hover para el sidebar
    const sidebarLinks = document.querySelectorAll('.nav-sidebar .nav-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(4px)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
    
    // Efecto de hover para el logo
    const logo = document.querySelector('.brand-image');
    if (logo) {
        logo.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        logo.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    }
    
    // Efecto de hover para el user panel
    const userPanel = document.querySelector('.user-panel');
    if (userPanel) {
        userPanel.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, 0.1)';
            this.style.borderColor = 'rgba(255, 255, 255, 0.2)';
        });
        
        userPanel.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, 0.05)';
            this.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        });
    }
    
    // Efecto de notificación
    const notifyBtn = document.querySelector('#btn-notify');
    if (notifyBtn) {
        notifyBtn.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    }
    
    // Efecto de resaltado para elementos activos
    const currentPath = window.location.pathname;
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Efecto de hover para iconos
    cards.forEach(card => {
        const icon = card.querySelector('.icon');
        if (icon) {
            card.addEventListener('mouseenter', function() {
                icon.style.transform = 'scale(1.1)';
                icon.style.opacity = '0.2';
            });
            
            card.addEventListener('mouseleave', function() {
                icon.style.transform = 'scale(1)';
                icon.style.opacity = '0.1';
            });
        }
    });
    
    // Efecto de resplandor en hover para tarjetas
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        });
    });
    
    console.log('Dashboard limpio cargado correctamente');
});
