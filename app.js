let noticiasTotales = [];
let noticiasMostradas = 0;
const LIMITE_POR_PAGINA = 15;
let seccionActual = 'global';

function cambiarSeccion(seccion) {
    seccionActual = seccion;
    
    const botones = document.querySelectorAll('.tab-btn');
    if(botones.length >= 2) {
        botones[0].classList.toggle('active', seccion === 'global');
        botones[1].classList.toggle('active', seccion === 'local');
    }
    
    // Resetear y redibujar
    document.getElementById('buscador').value = '';
    filtrarNoticias();
}

function iniciarFondoTech() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    let width, height;
    let particles = [];
    
    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();
    
    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 1.5;
            this.vy = (Math.random() - 0.5) * 1.5;
            this.radius = Math.random() * 2 + 1;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > width) this.vx = -this.vx;
            if (this.y < 0 || this.y > height) this.vy = -this.vy;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = '#00f3ff'; // Azul Nexus
            ctx.fill();
        }
    }
    
    for (let i = 0; i < 70; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, width, height);
        
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw();
            
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < 180) {
                    ctx.beginPath();
                    // Gradiente sutil hacia el color morado basado en la distancia
                    ctx.strokeStyle = `rgba(181, 60, 255, ${(180 - dist) / 1000})`; 
                    ctx.lineWidth = 1;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    animate();
}

// Esperar a que el DOM esté cargado
document.addEventListener('DOMContentLoaded', () => {
    iniciarFondoTech();
    
    // Lógica para ocultar el header al hacer scroll hacia abajo
    let ultimoScrollY = window.scrollY;
    window.addEventListener('scroll', () => {
        const header = document.querySelector('header');
        if (window.scrollY > ultimoScrollY && window.scrollY > 150) {
            // Bajando
            header.classList.add('header-hidden');
        } else {
            // Subiendo
            header.classList.remove('header-hidden');
        }
        ultimoScrollY = window.scrollY;
    });

    // historial_noticias vendrá de historial_datos.js
    if (typeof historial_noticias !== 'undefined' && historial_noticias.length > 0) {
        noticiasTotales = historial_noticias;
        cargarMasNoticias();
    } else {
        document.getElementById('contenedor-noticias').innerHTML = '<p style="color:white; text-align:center; grid-column: 1 / -1;">No se encontraron noticias. Ejecuta main.py para generarlas.</p>';
    }

    document.getElementById('buscador').addEventListener('keyup', filtrarNoticias);
});

function renderizarTarjetas(noticias) {
    const contenedor = document.getElementById('contenedor-noticias');
    
    noticias.forEach((n) => {
        const clase_impacto = n.impacto && n.impacto.toLowerCase() === "alto" ? "card-grande" : "card-pequena";
        
        // Lógica para textos (fallback a 'resumen' u otros por defecto)
        const texto_gancho = n.gancho || n.resumen || 'Haz clic para leer el artículo completo...';
        
        // Construir la tarjeta
        const article = document.createElement('article');
        article.className = `tarjeta ${clase_impacto}`;
        article.dataset.titulo = n.titulo.toLowerCase();
        article.dataset.categoria = (n.categoria || '').toLowerCase();
        
        // Evento de clic
        article.onclick = () => abrirNoticia(n);
        
        article.innerHTML = `
            <span class="etiqueta-categoria">${n.categoria || 'GENERAL'}</span>
            <span class="etiqueta-fecha">${n.fecha || ''}</span>
            <h2>${n.titulo}</h2>
            <div class="contenido"><p>${texto_gancho} <span style="color: #0ea5e9; font-weight: bold;">Leer más...</span></p></div>
        `;
        
        contenedor.appendChild(article);
    });
}

function cargarMasNoticias() {
    const input = document.getElementById('buscador').value.toLowerCase();
    
    // 1. Filtrar por sección (Global vs Local)
    let noticiasFiltradasBase = [];
    if (seccionActual === 'global') {
        noticiasFiltradasBase = noticiasTotales.filter(n => n.fuente_nombre !== 'Actualización Local');
    } else {
        noticiasFiltradasBase = noticiasTotales.filter(n => n.fuente_nombre === 'Actualización Local');
    }
    
    // 2. Filtrar por búsqueda si existe
    let noticiasFiltradasFinal = noticiasFiltradasBase;
    if (input.trim() !== '') {
        noticiasFiltradasFinal = noticiasFiltradasBase.filter(n => 
            n.titulo.toLowerCase().includes(input) || 
            (n.categoria || '').toLowerCase().includes(input)
        );
    }

    const noticiasSiguientes = noticiasFiltradasFinal.slice(noticiasMostradas, noticiasMostradas + LIMITE_POR_PAGINA);
    renderizarTarjetas(noticiasSiguientes);
    noticiasMostradas += noticiasSiguientes.length;

    // Mostrar u ocultar el botón de cargar más
    const btnContenedor = document.getElementById('contenedor-paginacion');
    if (noticiasMostradas >= noticiasFiltradasFinal.length) {
        btnContenedor.style.display = 'none';
    } else {
        btnContenedor.style.display = 'block';
    }
}

function filtrarNoticias() {
    // Reiniciar al buscar
    noticiasMostradas = 0;
    const contenedor = document.getElementById('contenedor-noticias');
    contenedor.innerHTML = '';
    cargarMasNoticias();
}

function abrirNoticia(n) {
    document.getElementById('modal-categoria').innerText = n.categoria || 'GENERAL';
    document.getElementById('modal-fecha').innerText = n.fecha || '';
    document.getElementById('modal-titulo').innerText = n.titulo;
    
    const texto_completo = n.contenido_completo || n.resumen || 'Contenido no disponible.';
    document.getElementById('modal-texto').innerHTML = `<p>${texto_completo}</p>`;
    
    const fuenteHTML = n.fuente_nombre === 'Actualización Local' 
        ? `<strong>Origen:</strong> <span style="color:var(--accent-purple)">NEXUS 8 INTERNO</span>`
        : `<strong>Fuente original:</strong> <a href="${n.fuente_url}" target="_blank">${n.fuente_nombre}</a>`;
    document.getElementById('modal-fuente').innerHTML = fuenteHTML;

    document.getElementById('modal-noticia').style.display = 'flex';
    document.body.style.overflow = 'hidden'; 
}

function cerrarModal() {
    document.getElementById('modal-noticia').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function cerrarSiClickFuera(event) {
    if (event.target.id === 'modal-noticia') {
        cerrarModal();
    }
}
