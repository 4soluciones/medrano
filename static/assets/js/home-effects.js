// ===== EFECTOS INTERACTIVOS PARA HOME =====

document.addEventListener('DOMContentLoaded', function() {
    
    // Efecto de entrada escalonada para las tarjetas
    const cards = document.querySelectorAll('.small-box');
    
    // Función para animar las tarjetas con delay
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
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
        });
        
        card.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
        });
    });
    
    // Efecto de partículas flotantes
    function createParticle() {
        const particle = document.createElement('div');
        particle.className = 'floating-particle';
        particle.style.cssText = `
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            pointer-events: none;
            z-index: 1;
        `;
        
        const startX = Math.random() * window.innerWidth;
        const startY = window.innerHeight + 10;
        const endX = startX + (Math.random() - 0.5) * 200;
        const endY = -10;
        const duration = 3000 + Math.random() * 2000;
        
        particle.style.left = startX + 'px';
        particle.style.top = startY + 'px';
        
        document.body.appendChild(particle);
        
        // Animación de la partícula
        particle.animate([
            { transform: 'translate(0, 0)', opacity: 0.8 },
            { transform: `translate(${endX - startX}px, ${endY - startY}px)`, opacity: 0 }
        ], {
            duration: duration,
            easing: 'ease-out'
        }).onfinish = () => {
            particle.remove();
        };
    }
    
    // Crear partículas periódicamente
    setInterval(createParticle, 2000);
    
    // Efecto de brillo en el navbar
    const navbar = document.querySelector('.main-header');
    if (navbar) {
        navbar.addEventListener('mousemove', function(e) {
            const rect = navbar.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            navbar.style.background = `linear-gradient(135deg, 
                var(--primary-color) 0%, 
                var(--dark-color) 50%, 
                rgba(52, 152, 219, 0.3) 100%)`;
        });
        
        navbar.addEventListener('mouseleave', function() {
            navbar.style.background = 'linear-gradient(135deg, var(--primary-color) 0%, var(--dark-color) 100%)';
        });
    }
    
    // Efecto de scroll suave para el sidebar
    const sidebarLinks = document.querySelectorAll('.nav-sidebar .nav-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.getAttribute('href') && this.getAttribute('href') !== '#') {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
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
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transform: translateX(-100%);
                animation: loading 1.5s infinite;
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
            z-index: 5;
        }
    `;
    document.head.appendChild(style);
    
    // Agregar efecto de carga después de un delay
    setTimeout(addLoadingEffect, 1000);
    
    // Efecto de hover para el logo
    const logo = document.querySelector('.brand-image');
    if (logo) {
        logo.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1) rotate(5deg)';
        });
        
        logo.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
        });
    }
    
    // Efecto de notificación mejorado
    const notifyBtn = document.querySelector('#btn-notify');
    if (notifyBtn) {
        notifyBtn.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    }
    
    // Efecto de scroll para el contenido
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const parallax = document.querySelector('.content-wrapper');
        if (parallax) {
            const speed = scrolled * 0.5;
            parallax.style.transform = `translateY(${speed}px)`;
        }
    });
    
    // Efecto de hover para los iconos de las tarjetas
    cards.forEach(card => {
        const icon = card.querySelector('.icon');
        if (icon) {
            card.addEventListener('mouseenter', function() {
                icon.style.animation = 'iconBounce 0.6s ease-in-out';
            });
            
            card.addEventListener('mouseleave', function() {
                icon.style.animation = 'none';
            });
        }
    });
    
    // Agregar CSS para la animación del icono
    const iconStyle = document.createElement('style');
    iconStyle.textContent = `
        @keyframes iconBounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0) scale(1.1) rotate(10deg); }
            40% { transform: translateY(-10px) scale(1.2) rotate(15deg); }
            60% { transform: translateY(-5px) scale(1.15) rotate(12deg); }
        }
    `;
    document.head.appendChild(iconStyle);
    
    // Efecto de resplandor en hover
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.boxShadow = `
                0 8px 30px rgba(0,0,0,0.2),
                0 0 0 3px rgba(255,255,255,0.1),
                0 0 20px rgba(255,255,255,0.2)
            `;
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.boxShadow = '';
        });
    });
    
    console.log('Efectos de home cargados correctamente');
});
