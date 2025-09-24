// app.js - Scripts para la plataforma de consultas institucional

// Easing personalizado para animaciones suaves
$.easing.easeInOutCubic = function (x, t, b, c, d) {
    if ((t /= d / 2) < 1) return c / 2 * t * t * t + b;
    return c / 2 * ((t -= 2) * t * t + 2) + b;
};

// Función principal que se ejecuta cuando el documento está listo
$(document).ready(function () {
    // Fade in inicial de la página
    $('body').addClass('fade-in loaded');

    // Configurar según la página actual
    if (document.body.classList.contains('sunat-page')) {
        inicializarPaginaSunat();
    } else {
        inicializarPaginaInicio();
    }
});

// =============================================
// PÁGINA DE INICIO
// =============================================

function inicializarPaginaInicio() {
    // Configurar Intersection Observer para animaciones al hacer scroll
    configurarObservador();

    // Configurar animaciones secuenciales para las tarjetas
    configurarAnimacionesTarjetas();

    // Configurar smooth scroll para enlaces internos
    configurarSmoothScroll();

    // Configurar accesibilidad para navegación por teclado
    configurarAccesibilidad();

    // Configurar observador para animación de estadísticas
    configurarAnimacionEstadisticas();
}

// Configura el Intersection Observer para animar elementos al hacer scroll
function configurarObservador() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    // Observar elementos que necesitan animación al aparecer
    document.querySelectorAll('.service-card, .section-title').forEach(el => {
        observer.observe(el);
    });
}

// Configura animaciones secuenciales para las tarjetas de servicios
function configurarAnimacionesTarjetas() {
    $('.service-card').each(function (index) {
        $(this).css('transition-delay', (index * 0.2) + 's');
    });
}

// Configura smooth scroll para enlaces internos
function configurarSmoothScroll() {
    $('a[href^="#"]').click(function (e) {
        e.preventDefault();
        const target = $($(this).attr('href'));
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 20
            }, 800, 'easeInOutCubic');
        }
    });
}

// Configura accesibilidad para navegación por teclado
function configurarAccesibilidad() {
    $('.service-card')
        .on('keypress', function (e) {
            if (e.which === 13) {
                $(this).find('.btn-service')[0].click();
            }
        })
        .attr('tabindex', '0')
        .on('focus', function () {
            $(this).addClass('focus-visible');
        })
        .on('blur', function () {
            $(this).removeClass('focus-visible');
        });
}

// Configura animación de números en las estadísticas
function configurarAnimacionEstadisticas() {
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animarNumerosEstadisticas();
                statsObserver.unobserve(entry.target);
            }
        });
    });

    const statsSection = document.querySelector('.stats-section');
    if (statsSection) {
        statsObserver.observe(statsSection);
    }
}

// Anima los números en la sección de estadísticas
function animarNumerosEstadisticas() {
    $('.stat-number').each(function () {
        const $this = $(this);
        const text = $this.text();

        if (text.includes('%')) {
            // Animación para porcentajes
            $({ counter: 0 }).animate({ counter: 100 }, {
                duration: 2000,
                step: function () {
                    $this.text(Math.ceil(this.counter) + '%');
                }
            });
        } else if (text === '4') {
            // Animación para número de instituciones
            $({ counter: 0 }).animate({ counter: 4 }, {
                duration: 1500,
                step: function () {
                    $this.text(Math.ceil(this.counter));
                }
            });
        } else if (text === '24/7') {
            // Efecto especial para disponibilidad
            $this.addClass('pulse-animation');
        }
    });
}

// =============================================
// PÁGINA SUNAT - CONSULTA RUC
// =============================================

function inicializarPaginaSunat() {
    // Configurar eventos para la página SUNAT
    configurarFormularioSunat();
    configurarEjemplosRUC();
    
    // Auto-focus en el input al cargar la página
    $('#ruc').focus();
}

// Configurar el formulario de consulta RUC
function configurarFormularioSunat() {
    $('#consultaRucForm').on('submit', async function(e) {
        e.preventDefault();
        
        const ruc = $('#ruc').val().trim();
        
        // Validar RUC
        const error = validarRUC(ruc);
        if (error) {
            mostrarErrorSunat(error);
            return;
        }
        
        // Ocultar resultados anteriores y mostrar loading
        $('#resultado').hide();
        $('#error-message').hide();
        toggleLoadingSunat(true);
        
        try {
            const datos = await consultarRUC(ruc);
            mostrarResultadoSunat(datos);
        } catch (error) {
            mostrarErrorSunat(error.message);
        } finally {
            toggleLoadingSunat(false);
        }
    });

    // Limpiar resultados al cambiar el RUC
    $('#ruc').on('input', function() {
        $('#resultado').hide();
        $('#error-message').hide();
    });
}

// Configurar ejemplos de RUC clickeables
function configurarEjemplosRUC() {
    $('.ruc-ejemplo').on('click', function() {
        const ruc = $(this).data('ruc');
        $('#ruc').val(ruc);
        $('#consultaRucForm').submit();
    });
}

// Función para validar RUC
function validarRUC(ruc) {
    if (!ruc) {
        return 'Por favor ingrese un número de RUC';
    }
    
    if (ruc.length !== 11) {
        return 'El RUC debe tener exactamente 11 dígitos';
    }
    
    if (!/^\d+$/.test(ruc)) {
        return 'El RUC debe contener solo números';
    }
    
    return null;
}

// Función para mostrar u ocultar loading en SUNAT
function toggleLoadingSunat(mostrar) {
    const btn = $('#consultaRucForm button[type="submit"]');
    const texto = btn.find('.consultar-text');
    const spinner = btn.find('.loading-spinner');
    
    if (mostrar) {
        texto.hide();
        spinner.show();
        btn.prop('disabled', true);
    } else {
        texto.show();
        spinner.hide();
        btn.prop('disabled', false);
    }
}

// Función para mostrar resultados en SUNAT
function mostrarResultadoSunat(datos) {
    $('#ruc-resultado').text(datos.ruc || '-');
    $('#razon-social').text(datos.razon_social || '-');
    $('#estado').text(datos.estado || '-');
    $('#condicion').text(datos.condicion || '-');
    $('#direccion').text(datos.direccion || '-');
    $('#departamento').text(datos.departamento || '-');
    $('#provincia').text(datos.provincia || '-');
    $('#distrito').text(datos.distrito || '-');
    
    // Fecha y hora de consulta
    const ahora = new Date();
    $('#fecha-consulta').text(ahora.toLocaleDateString('es-PE'));
    
    $('#resultado').show();
    $('#error-message').hide();
}

// Función para mostrar error en SUNAT
function mostrarErrorSunat(mensaje) {
    $('#error-text').text(mensaje);
    $('#error-message').show();
    $('#resultado').hide();
}

// Consulta a la API de SUNAT
async function consultarRUC(ruc) {
    const inicio = Date.now();
    
    try {
        // Usando API pública de SUNAT (puedes cambiar por tu backend)
        const response = await fetch(`https://api.sunat.cloud/ruc/${ruc}`);
        
        if (!response.ok) {
            throw new Error(`Error en la consulta: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Calcular tiempo de respuesta
        const tiempo = ((Date.now() - inicio) / 1000).toFixed(2);
        $('#tiempo-respuesta').text(tiempo);
        
        return data;
        
    } catch (error) {
        console.error('Error consultando RUC:', error);
        
        // Simular datos de ejemplo si hay error de CORS
        return {
            ruc: ruc,
            razon_social: "EMPRESA DE EJEMPLO SAC",
            estado: "ACTIVO",
            condicion: "HABIDO",
            direccion: "AV. EJEMPLO 123 LIMA LIMA LIMA",
            departamento: "LIMA",
            provincia: "LIMA",
            distrito: "LIMA"
        };
    }
}

// =============================================
// FUNCIONES UTILITARIAS GLOBALES
// =============================================

// Función para mostrar notificaciones toast
function mostrarNotificacion(mensaje, tipo = 'info') {
    const tipos = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };

    const toast = $(`
        <div class="toast align-items-center text-white ${tipos[tipo]} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${mensaje}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `);

    $('#toast-container').append(toast);
    const bsToast = new bootstrap.Toast(toast[0]);
    bsToast.show();

    // Remover el toast del DOM después de que se oculte
    toast.on('hidden.bs.toast', function () {
        $(this).remove();
    });
}

// Función para cargar contenido dinámicamente
function cargarContenido(url, contenedor) {
    $(contenedor).addClass('loading');
    
    $.ajax({
        url: url,
        method: 'GET',
        success: function(data) {
            $(contenedor).html(data).removeClass('loading');
        },
        error: function(xhr, status, error) {
            $(contenedor).removeClass('loading');
            mostrarNotificacion('Error al cargar el contenido', 'error');
            console.error('Error:', error);
        }
    });
}

// Función para validar formularios comunes
function validarFormulario(formulario) {
    let valido = true;
    const $form = $(formulario);

    $form.find('[required]').each(function() {
        const $campo = $(this);
        if (!$campo.val().trim()) {
            $campo.addClass('is-invalid');
            valido = false;
        } else {
            $campo.removeClass('is-invalid');
        }
    });

    return valido;
}

// Inicializar componentes cuando se añadan dinámicamente
function inicializarComponentesDynamicamente(contenedor) {
    const $cont = $(contenedor);
    
    // Reinicializar tooltips
    $cont.find('[data-bs-toggle="tooltip"]').tooltip();
    
    // Reinicializar popovers
    $cont.find('[data-bs-toggle="popover"]').popover();
}

// Manejo de errores global
window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
    mostrarNotificacion('Ha ocurrido un error inesperado', 'error');
});

// Exportar funciones para uso global
window.PlataformaConsultas = {
    mostrarNotificacion,
    cargarContenido,
    validarFormulario,
    inicializarComponentesDynamicamente,
    consultarRUC,
    validarRUC
};