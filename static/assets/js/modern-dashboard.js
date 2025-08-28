// ===== EFECTOS MODERNOS PARA DASHBOARD =====

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
    
    // Efecto de scroll suave para enlaces internos
    const internalLinks = document.querySelectorAll('a[href^="#"]');
    internalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Efecto de resaltado para elementos activos
    const currentPath = window.location.pathname;
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Efecto de carga para las tarjetas
    function addLoadingEffect() {
        cards.forEach(card => {
            const loader = document.createElement('div');
            loader.className = 'card-loader';
            loader.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.1), transparent);
                transform: translateX(-100%);
                animation: loading 1.5s infinite;
                z-index: 5;
            `;
            
            card.appendChild(loader);
        });
    }
    
    // CSS para el loader
    const style = document.createElement('style');
    style.textContent = `
        @keyframes loading {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
    `;
    document.head.appendChild(style);
    
    // Agregar efecto de carga después de un delay
    setTimeout(addLoadingEffect, 1000);
    
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
            this.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)';
        });
    });
    
    console.log('Dashboard moderno cargado correctamente');
});
