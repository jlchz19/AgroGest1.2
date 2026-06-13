// Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    // Relocate dashboard summary modals to document.body to avoid stacking context / backdrop blocking issues
    const summaryModals = [
        'animalesModal',
        'potrerosModal',
        'empleadosModal',
        'inventarioModal',
        'partoModal',
        'ubicacionModal'
    ];
    summaryModals.forEach(id => {
        const modalEl = document.getElementById(id);
        if (modalEl && modalEl.parentElement !== document.body) {
            document.body.appendChild(modalEl);
        }
    });

    // Initialize progress bars
    const progressBars = document.querySelectorAll('.progress-bar[data-width]');
    progressBars.forEach(bar => {
        const width = bar.getAttribute('data-width');
        bar.style.width = `${width}%`;
    });

    // Initialize charts
    initializeCharts();

    // Solución para eliminar backdrops persistentes y restaurar interactividad
    document.addEventListener('hidden.bs.modal', function() {
        // Eliminar todos los backdrops persistentes
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // Restaurar el scroll del body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    });

    // Event listeners for summary cards
    const cardAnimales = document.getElementById('cardAnimales');
    const cardPotreros = document.getElementById('cardPotreros');
    const cardEmpleados = document.getElementById('cardEmpleados');
    const cardInventario = document.getElementById('cardInventario');

    if (cardAnimales) cardAnimales.addEventListener('click', showAnimalesResumen);
    if (cardPotreros) cardPotreros.addEventListener('click', showPotrerosResumen);
    if (cardEmpleados) cardEmpleados.addEventListener('click', showEmpleadosResumen);
    if (cardInventario) cardInventario.addEventListener('click', showInventarioResumen);
});

// Helper para colores
function getChartColors() {
    return {
        primary: 'rgba(54, 162, 235, 0.6)',
        success: 'rgba(75, 192, 192, 0.6)',
        warning: 'rgba(255, 206, 86, 0.6)',
        info: 'rgba(153, 102, 255, 0.6)',
        danger: 'rgba(255, 99, 132, 0.6)',
        blue: '#36A2EB',
        green: '#4BC0C0',
        yellow: '#FFCE56',
        purple: '#9966FF',
        red: '#FF6384',
        orange: '#FF9F40'
    };
}

// Inicializar gráficos
function initializeCharts() {
    const colors = getChartColors();
    
    // Gráfico de fincas (si existe el elemento)
    const fincaCtx = document.getElementById('finca-chart');
    if (fincaCtx) {
        try {
            const fincaLabels = JSON.parse(fincaCtx.dataset.labels || '[]');
            const fincaData = JSON.parse(fincaCtx.dataset.values || '[]');
            
            new Chart(fincaCtx, {
                type: 'bar',
                data: {
                    labels: fincaLabels,
                    datasets: [{
                        label: 'Nº de Animales',
                        data: fincaData,
                        backgroundColor: [
                            colors.primary, 
                            colors.success, 
                            colors.warning, 
                            colors.info, 
                            colors.danger, 
                            colors.orange
                        ],
                        borderColor: 'rgba(255, 255, 255, 0)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { 
                        legend: { display: false } 
                    },
                    scales: { 
                        y: { 
                            beginAtZero: true 
                        } 
                    }
                }
            });
        } catch (error) {
            console.error('Error al cargar gráfico de fincas:', error);
        }
    }

    
}

// Funciones de resumen
async function showAnimalesResumen() {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('animalesModal'));
    const content = document.getElementById('animalesContent');
    
    if (!content) return;
    
    content.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Cargando datos de animales...</p></div>';
    modal.show();
    
    try {
        const response = await fetch('/api/resumen/animales');
        
        if (!response.ok) throw new Error('Error en la respuesta del servidor');
        
        const data = await response.json();
        
        if (data.error) {
            content.innerHTML = `
                <div class="alert alert-warning m-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${data.error}
                </div>`;
            return;
        }
        
        // Build summary data
        const tiposUnicos = data.tipos_unicos && data.tipos_unicos.length ? data.tipos_unicos : [];
        const topTipo = data.top_tipo || '—';
        const totalTipos = tiposUnicos.length;
        const totalRazas = data.razas_unicas || 0;
        const porRaza = data.por_raza || [];

        const getAnimalIcon = (tipo) => {
            const tipoLower = (tipo || '').toLowerCase();
            if (tipoLower.includes('vaca') || tipoLower.includes('bovino')) return '🐄';
            if (tipoLower.includes('toro')) return '🐃';
            if (tipoLower.includes('cerdo') || tipoLower.includes('porcino')) return '🐷';
            if (tipoLower.includes('pollo') || tipoLower.includes('gallina') || tipoLower.includes('ave')) return '🐔';
            if (tipoLower.includes('caballo') || tipoLower.includes('yegua')) return '🐴';
            if (tipoLower.includes('oveja') || tipoLower.includes('cordero')) return '🐑';
            if (tipoLower.includes('cabra')) return '🐐';
            if (tipoLower.includes('perro')) return '🐶';
            if (tipoLower.includes('gato')) return '🐱';
            return '🐾';
        };

        content.innerHTML = `
            <!-- Stats Cards -->
            <div class="row g-3 mb-4">
                <div class="col-6 col-md-3">
                    <div class="card border-0 shadow-sm h-100" style="background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);">
                        <div class="card-body text-center text-white py-3">
                            <h2 class="mb-1 fw-bold">${data.total || 0}</h2>
                            <p class="mb-0 small opacity-75">Total Animales</p>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card border-0 shadow-sm h-100" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                        <div class="card-body text-center text-white py-3">
                            <h2 class="mb-1 fw-bold">${totalTipos}</h2>
                            <p class="mb-0 small opacity-75">Tipos de Animales</p>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card border-0 shadow-sm h-100" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);">
                        <div class="card-body text-center text-white py-3">
                            <h2 class="mb-1 fw-bold">${totalRazas}</h2>
                            <p class="mb-0 small opacity-75">Razas Registradas</p>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card border-0 shadow-sm h-100" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
                        <div class="card-body text-center text-white py-3">
                            <h6 class="mb-1 fw-bold text-truncate" title="${topTipo}">${topTipo}</h6>
                            <p class="mb-0 small opacity-75">Tipo Más Frecuente</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Two Column Layout: Types and Breeds -->
            <div class="row g-3">
                <!-- Animal Types -->
                <div class="col-md-6">
                    <h6 class="mb-3 fw-bold"><span style="font-size: 1.2rem; margin-right: 0.5rem; filter: drop-shadow(1px 2px 3px rgba(0,0,0,0.2));">🐾</span>Tipos de Animales</h6>
                    <div class="list-group">
                        ${(data.por_tipo && data.por_tipo.length > 0) ? 
                            data.por_tipo.map((item, index) => {
                                const colors = ['primary', 'success', 'info', 'warning', 'danger', 'secondary'];
                                const color = colors[index % colors.length];
                                const icon = getAnimalIcon(item.tipo);
                                const percentage = data.total > 0 ? Math.round((item.cantidad / data.total) * 100) : 0;
                                return `
                                <div class="list-group-item d-flex justify-content-between align-items-center py-2">
                                    <div class="d-flex align-items-center">
                                        <div class="bg-${color} bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 40px; height: 40px; font-size: 1.3rem;">
                                            ${icon}
                                        </div>
                                        <div>
                                            <span class="fw-bold d-block">${item.tipo || 'Sin especificar'}</span>
                                            <small class="text-muted">${percentage}% del total</small>
                                        </div>
                                    </div>
                                    <span class="badge bg-${color} rounded-pill">${item.cantidad || 0}</span>
                                </div>
                            `;
                            }).join('')
                            : '<div class="list-group-item"><i class="fas fa-info-circle me-2"></i>No hay datos disponibles</div>'
                        }
                    </div>
                </div>
                
                <!-- Breeds -->
                <div class="col-md-6">
                    <h6 class="mb-3 fw-bold"><span style="font-size: 1.2rem; margin-right: 0.5rem; filter: drop-shadow(1px 2px 3px rgba(0,0,0,0.2));">🧬</span>Razas Registradas</h6>
                    <div class="list-group">
                        ${(porRaza && porRaza.length > 0) ? 
                            porRaza.map((item, index) => {
                                const colors = ['primary', 'success', 'info', 'warning', 'danger', 'secondary'];
                                const color = colors[index % colors.length];
                                const percentage = data.total > 0 ? Math.round((item.cantidad / data.total) * 100) : 0;
                                return `
                                <div class="list-group-item d-flex justify-content-between align-items-center py-2">
                                    <div class="d-flex align-items-center">
                                        <div class="bg-${color} bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 40px; height: 40px; font-size: 1.2rem;">
                                            🏷️
                                        </div>
                                        <div>
                                            <span class="fw-bold d-block">${item.raza || 'Sin especificar'}</span>
                                            <small class="text-muted">${percentage}% del total</small>
                                        </div>
                                    </div>
                                    <span class="badge bg-${color} rounded-pill">${item.cantidad || 0}</span>
                                </div>
                            `;
                            }).join('')
                            : '<div class="list-group-item"><i class="fas fa-info-circle me-2"></i>No hay datos disponibles</div>'
                        }
                    </div>
                </div>
            </div>`;
    } catch (error) {
        console.error('Error al cargar datos de animales:', error);
        content.innerHTML = `
            <div class="alert alert-danger m-0">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${error.name === 'AbortError' ? 'Tiempo de espera agotado.' : 'Error al cargar los datos.'}
            </div>
            <div class="text-center mt-3">
                <button class="btn btn-primary btn-sm" onclick="showAnimalesResumen()">
                    <i class="fas fa-sync-alt me-1"></i> Reintentar
                </button>
            </div>`;
    }
}

async function showPotrerosResumen() {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('potrerosModal'));
    const content = document.getElementById('potrerosContent');
    
    if (!content) return;
    
    content.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Cargando datos de potreros...</p></div>';
    modal.show();
    
    try {
        const response = await fetch('/api/resumen/potreros');
        
        if (!response.ok) throw new Error('Error en la respuesta del servidor');
        
        const data = await response.json();
        
        if (data.error) {
            content.innerHTML = `
                <div class="alert alert-warning m-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${data.error}
                </div>`;
            return;
        }
        
        content.innerHTML = `
            <div class="row g-3 mb-4">
                <div class="col-6">
                    <div class="card border-0 shadow-sm">
                        <div class="card-body text-center">
                            <h2 class="mb-1 text-primary">${data.total || 0}</h2>
                            <p class="text-muted mb-0">Total Potreros</p>
                        </div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="card border-0 shadow-sm">
                        <div class="card-body text-center">
                            <h2 class="mb-1 text-success">${data.potreros ? data.potreros.reduce((sum, p) => sum + p.animales, 0) : 0}</h2>
                            <p class="text-muted mb-0">Animales en Potreros</p>
                        </div>
                    </div>
                </div>
            </div>
            <h6 class="mb-3">Estado de los Potreros</h6>
            <div class="table-responsive">
                <table class="table table-sm table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Potrero</th>
                            <th class="text-center">Capacidad</th>
                            <th class="text-center">Uso</th>
                            <th class="text-center">Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(data.potreros && data.potreros.length > 0) ? 
                            data.potreros.map(potrero => `
                                <tr>
                                    <td>
                                        <strong>${potrero.nombre || 'Sin nombre'}</strong>
                                        <div class="small text-muted">Área: ${potrero.area || 0} ha</div>
                                    </td>
                                    <td class="text-center">${potrero.capacidad || 0}</td>
                                    <td class="text-center">
                                        <div class="progress" style="height: 6px;">
                                            <div class="progress-bar ${potrero.ocupacion > 80 ? 'bg-danger' : potrero.ocupacion > 50 ? 'bg-warning' : 'bg-success'}" 
                                                 role="progressbar" 
                                                 style="width: ${Math.min(potrero.ocupacion || 0, 100)}%" 
                                                 aria-valuenow="${potrero.ocupacion || 0}" 
                                                 aria-valuemin="0" 
                                                 aria-valuemax="100">
                                            </div>
                                        </div>
                                        <small class="text-muted">${potrero.animales || 0} / ${potrero.capacidad || 0}</small>
                                    </td>
                                    <td class="text-center">
                                        <span class="badge ${potrero.estado === 'disponible' ? 'bg-success' : 'bg-secondary'}">
                                            ${potrero.estado || 'Desconocido'}
                                        </span>
                                    </td>
                                </tr>
                            `).join('')
                            : '<tr><td colspan="4" class="text-center py-3">No hay potreros registrados</td></tr>'
                        }
                    </tbody>
                </table>
            </div>`;
    } catch (error) {
        console.error('Error al cargar datos de potreros:', error);
        content.innerHTML = `
            <div class="alert alert-danger m-0">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error al cargar los datos de potreros.
            </div>
            <div class="text-center mt-3">
                <button class="btn btn-primary btn-sm" onclick="showPotrerosResumen()">
                    <i class="fas fa-sync-alt me-1"></i> Reintentar
                </button>
            </div>`;
    }
}

async function showEmpleadosResumen() {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('empleadosModal'));
    const content = document.getElementById('empleadosContent');
    
    if (!content) return;
    
    content.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Cargando datos de empleados...</p></div>';
    modal.show();
    
    try {
        const response = await fetch('/api/resumen/empleados');
        
        if (!response.ok) throw new Error('Error en la respuesta del servidor');
        
        const data = await response.json();
        
        if (data.error) {
            content.innerHTML = `
                <div class="alert alert-warning m-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${data.error}
                </div>`;
            return;
        }
        
        content.innerHTML = `
            <div class="row">
                <div class="col-12">
                    <div class="card border-0 shadow-sm mb-4">
                        <div class="card-body text-center">
                            <h2 class="mb-1 text-primary">${data.total || 0}</h2>
                            <p class="text-muted mb-0">Total Empleados Activos</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <h6 class="mb-3">Distribución por Cargo</h6>
                    <div class="list-group">
                        ${(data.por_cargo && data.por_cargo.length > 0) ? 
                            data.por_cargo.map(item => `
                                <div class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>${item.cargo || 'Sin especificar'}</span>
                                    <span class="badge bg-primary rounded-pill">${item.cantidad || 0}</span>
                                </div>
                            `).join('')
                            : '<div class="alert alert-info mb-0">No hay datos de cargos</div>'
                        }
                    </div>
                </div>
                <div class="col-md-6">
                    <h6 class="mb-3">Estado Actual</h6>
                    <div class="list-group">
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>Empleados Activos</span>
                                <span class="badge bg-success rounded-pill">${data.activos || 0}</span>
                            </div>
                        </div>
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>Total Empleados</span>
                                <span class="badge bg-primary rounded-pill">${data.total || 0}</span>
                            </div>
                        </div>
                        ${(data.total && data.total > 0) ? 
                            `<div class="list-group-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span>Disponibilidad</span>
                                    <span class="badge bg-info rounded-pill">OK</span>
                                </div>
                            </div>`
                            : ''
                        }
                    </div>
                </div>
            </div>`;
    } catch (error) {
        console.error('Error al cargar datos de empleados:', error);
        content.innerHTML = `
            <div class="alert alert-danger m-0">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error al cargar los datos de empleados.
            </div>
            <div class="text-center mt-3">
                <button class="btn btn-primary btn-sm" onclick="showEmpleadosResumen()">
                    <i class="fas fa-sync-alt me-1"></i> Reintentar
                </button>
            </div>`;
    }
}

async function showInventarioResumen() {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('inventarioModal'));
    const content = document.getElementById('inventarioContent');
    
    if (!content) return;
    
    content.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Cargando datos de inventario...</p></div>';
    modal.show();
    
    try {
        const response = await fetch('/api/resumen/inventario');
        
        if (!response.ok) throw new Error('Error en la respuesta del servidor');
        
        const data = await response.json();
        
        if (data.error) {
            content.innerHTML = `
                <div class="alert alert-warning m-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${data.error}
                </div>`;
            return;
        }
        
        content.innerHTML = `
            <div class="row g-3 mb-4">
                <div class="col-md-6">
                    <div class="card border-0 shadow-sm h-100">
                        <div class="card-body text-center">
                            <h2 class="mb-1 text-primary">${data.total_items || 0}</h2>
                            <p class="text-muted mb-0">Total de Productos</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card border-0 shadow-sm h-100">
                        <div class="card-body text-center">
                            <h2 class="mb-1 text-success">$${data.valor_total ? data.valor_total.toLocaleString() : '0'}</h2>
                            <p class="text-muted mb-0">Valor Total</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6 mb-3">
                    <h6 class="mb-3">Por Categoría</h6>
                    <div class="list-group">
                        ${(data.por_categoria && data.por_categoria.length > 0) ? 
                            data.por_categoria.map(cat => `
                                <div class="list-group-item">
                                    <div class="d-flex w-100 justify-content-between">
                                        <h6 class="mb-1">${cat.categoria || 'Sin categoría'}</h6>
                                        <span class="badge bg-primary rounded-pill">${cat.items || 0}</span>
                                    </div>
                                    <p class="mb-0 text-muted small">Valor: $${cat.valor_total ? cat.valor_total.toLocaleString() : '0'}</p>
                                </div>
                            `).join('')
                            : '<div class="alert alert-info mb-0">No hay categorías disponibles</div>'
                        }
                    </div>
                </div>
                <div class="col-md-6">
                    <h6 class="mb-3">Estado del Inventario</h6>
                    <div class="list-group">
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>Productos con Stock Bajo</span>
                                <span class="badge bg-warning rounded-pill">${data.bajo_stock || 0}</span>
                            </div>
                        </div>
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>Total Productos</span>
                                <span class="badge bg-primary rounded-pill">${data.total_items || 0}</span>
                            </div>
                        </div>
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>Valor del Inventario</span>
                                <span class="badge bg-success rounded-pill">$${data.valor_total ? data.valor_total.toLocaleString() : '0'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
    } catch (error) {
        console.error('Error al cargar datos de inventario:', error);
        content.innerHTML = `
            <div class="alert alert-danger m-0">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error al cargar los datos de inventario.
            </div>
            <div class="text-center mt-3">
                <button class="btn btn-primary btn-sm" onclick="showInventarioResumen()">
                    <i class="fas fa-sync-alt me-1"></i> Reintentar
                </button>
            </div>`;
    }
}

// Inicializar tooltips y popovers cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Cerrar modales cuando se hace clic fuera de ellos
    var modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                var modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        });
        
        // Solucionar problema de modales bloqueados
        modal.addEventListener('hidden.bs.modal', function () {
            // Eliminar cualquier backdrop persistente
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => backdrop.remove());
            
            // Restaurar scroll del body
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
    });
});
