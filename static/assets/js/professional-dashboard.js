// ===== DASHBOARD PROFESIONAL - EFECTOS AVANZADOS =====

document.addEventListener('DOMContentLoaded', function() {
    
    // Efecto de entrada escalonada para las tarjetas
    const cards = document.querySelectorAll('.small-box');
    
    function animateCards() {
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 200);
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
        });
    }
    
    // Ejecutar animación después de un breve delay
    setTimeout(animateCards, 300);
    
    // Efecto de hover 3D para las tarjetas
    cards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
        });
    });
    
    // Efecto de hover para el sidebar
    const sidebarLinks = document.querySelectorAll('.nav-sidebar .nav-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(8px)';
            this.style.background = 'rgba(37, 99, 235, 0.15)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
            this.style.background = '';
        });
    });
    
    // Efecto de hover para el logo
    const logo = document.querySelector('.brand-image');
    if (logo) {
        logo.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1) rotate(5deg)';
            this.style.borderColor = 'rgba(255, 255, 255, 0.4)';
        });
        
        logo.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
            this.style.borderColor = 'rgba(255, 255, 255, 0.2)';
        });
    }
    
    // Efecto de hover para el user panel
    const userPanel = document.querySelector('.user-panel');
    if (userPanel) {
        userPanel.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, 0.15)';
            this.style.borderColor = 'rgba(255, 255, 255, 0.3)';
            this.style.transform = 'scale(1.02)';
        });
        
        userPanel.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, 0.08)';
            this.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            this.style.transform = 'scale(1)';
        });
    }
    
    // Efecto de notificación mejorado
    const notifyBtn = document.querySelector('#btn-notify');
    if (notifyBtn) {
        notifyBtn.addEventListener('click', function() {
            this.style.transform = 'scale(0.9)';
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
    
    // Efecto de hover para iconos de las tarjetas
    cards.forEach(card => {
        const icon = card.querySelector('.icon');
        if (icon) {
            card.addEventListener('mouseenter', function() {
                icon.style.transform = 'scale(1.2) rotate(10deg)';
                icon.style.opacity = '0.3';
            });
            
            card.addEventListener('mouseleave', function() {
                icon.style.transform = 'scale(1) rotate(0deg)';
                icon.style.opacity = '0.1';
            });
        }
    });
    
    // Efecto de resplandor en hover para tarjetas
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.25)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
        });
    });
    
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
                background: linear-gradient(90deg, transparent, rgba(37, 99, 235, 0.1), transparent);
                transform: translateX(-100%);
                animation: loading 1.5s infinite;
                z-index: 5;
                border-radius: 12px;
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
        
        .card-loader {
            pointer-events: none;
        }
    `;
    document.head.appendChild(style);
    
    // Agregar efecto de carga después de un delay
    setTimeout(addLoadingEffect, 1000);
    
    // Efecto de hover para el header
    const headerLinks = document.querySelectorAll('.main-header .nav-link');
    headerLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Efecto de scroll para el sidebar
    const sidebar = document.querySelector('.main-sidebar');
    if (sidebar) {
        sidebar.addEventListener('scroll', function() {
            const scrolled = this.scrollTop;
            if (scrolled > 10) {
                this.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.3)';
            } else {
                this.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1)';
            }
        });
    }
    
    // Efecto de hover para el footer
    const footerLinks = document.querySelectorAll('.main-footer a');
    footerLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Efecto de entrada para el preloader
    const preloader = document.querySelector('.preloader');
    if (preloader) {
        preloader.addEventListener('animationend', function() {
            this.style.opacity = '0';
            setTimeout(() => {
                this.style.display = 'none';
            }, 300);
        });
    }
    
    // Efecto de hover para botones de acción
    const actionButtons = document.querySelectorAll('.btn, .btn-sidebar');
    actionButtons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.15)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
    
    console.log('Dashboard profesional cargado correctamente');
    
    // Efecto de parallax sutil para las tarjetas
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        cards.forEach((card, index) => {
            const speed = 0.5 + (index * 0.1);
            card.style.transform = `translateY(${scrolled * speed * 0.01}px)`;
        });
    });
});
