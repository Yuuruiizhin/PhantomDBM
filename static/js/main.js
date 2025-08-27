// Variables globales para la gestión de la tabla y la base de datos actuales
let currentDb = null;
let currentTable = null;
let currentSchema = null;
let primaryKey = null;
let updateIntervalId = null;

let currentPage = 1;
const perPage = 30; // Se fija el número de resultados por página
let currentSearchQuery = '';
let currentSearchAttribute = '';

const sidebar = document.getElementById('sidebar');
const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
const mainContentWrapper = document.querySelector('.main-content-wrapper');
const dbAccordion = document.getElementById('db-accordion');
const mainContent = document.getElementById('main-content');
const welcomeJumbotron = document.getElementById('welcome-jumbotron');
const selectionIndicator = document.getElementById('selection-indicator');
const currentDbIndicator = document.getElementById('current-db-indicator');
const currentTableIndicator = document.getElementById('current-table-indicator');
const notificationContainer = document.getElementById('notification-container');
const toggleConsoleBtn = document.getElementById('toggle-sql-console');
const toggleConsoleBtnJumbotron = document.getElementById('toggle-sql-console-btn');

// Elementos para el modal de CRUD
const crudModalElement = document.getElementById('crudModal');
const crudModal = new bootstrap.Modal(crudModalElement);
const crudForm = document.getElementById('crud-form');
const crudModalLabel = document.getElementById('crudModalLabel');

// Elementos para el modal de creación
const createModalElement = document.getElementById('createModal');
const createModal = new bootstrap.Modal(createModalElement);
const createChoiceStep = document.getElementById('create-choice-step');
const createDbStep = document.getElementById('create-db-step');
const createTableStep = document.getElementById('create-table-step');
const createDbBtn = document.getElementById('create-db-btn');
const createTableBtn = document.getElementById('create-table-btn');
const createDbForm = document.getElementById('create-db-form');
const createTableForm = document.getElementById('create-table-form');
const tableDbNameSelect = document.getElementById('table-db-name');
const columnsContainer = document.getElementById('columns-container');
const addColumnBtn = document.getElementById('add-column-btn');

// Elementos para el CLI (Consola SQL)
const cliModalElement = document.getElementById('cliModal');
const cliModal = new bootstrap.Modal(cliModalElement);
const openCliBtn = document.getElementById('open-cli-btn');
const cliForm = document.getElementById('cli-form');
const cliInput = document.getElementById('cli-input');
const cliOutput = document.getElementById('cli-output');

// Funciones para la actualización en tiempo real
function stopRealtimeUpdates() {
    if (updateIntervalId) {
        clearInterval(updateIntervalId);
        updateIntervalId = null;
        console.log("Actualizaciones en tiempo real detenidas.");
    }
}

function fetchAndRenderTable() {
    if (currentDb && currentTable) {
        const queryParams = new URLSearchParams({
            page: currentPage,
            per_page: perPage,
            search_query: currentSearchQuery,
            search_attribute: currentSearchAttribute
        });
        
        // Guardar la posición de desplazamiento horizontal antes de la actualización
        const tableContainer = document.getElementById('table-container');
        let scrollPosition = 0;
        if (tableContainer) {
            scrollPosition = tableContainer.scrollLeft;
        }

        fetch(`/api/list/${currentDb}/${currentTable}?${queryParams.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error de red: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'danger');
                    stopRealtimeUpdates();
                    return;
                }
                
                currentSchema = data.schema;
                primaryKey = getPrimaryKeyFromSchema(currentSchema);
                renderTable(data.data, currentSchema, data.total_records, data.current_page, data.per_page);
                
                // Restaurar la posición de desplazamiento después de que la tabla se haya renderizado
                const newTableContainer = document.getElementById('table-container');
                if (newTableContainer) {
                    setTimeout(() => {
                        newTableContainer.scrollLeft = scrollPosition;
                    }, 0);
                }
            })
            .catch(error => {
                console.error('Error fetching table data:', error);
                showNotification(`Error al cargar datos de la tabla: ${error.message}`, 'danger');
                stopRealtimeUpdates();
            });
    } else {
        stopRealtimeUpdates();
    }
}

function startRealtimeUpdates() {
    stopRealtimeUpdates();
    fetchAndRenderTable();
    updateIntervalId = setInterval(fetchAndRenderTable, 3000);
    console.log(`Actualizaciones en tiempo real iniciadas para ${currentDb}.${currentTable}.`);
}

document.addEventListener('DOMContentLoaded', () => {
    fetchDatabases();
    document.getElementById('toggle-text-color').addEventListener('click', toggleTextColor);

    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Manejo de la consola SQL
    toggleConsoleBtn.addEventListener('click', () => toggleSqlConsole());
    if (toggleConsoleBtnJumbotron) {
        toggleConsoleBtnJumbotron.addEventListener('click', () => toggleSqlConsole());
    }

    cliInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            const query = cliInput.value.trim();
            if (query) {
                executeSql(query);
                cliInput.value = '';
            }
        }
    });

});

sidebarToggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('active');
    mainContentWrapper.classList.toggle('active');
});

function toggleTextColor() {
    document.body.classList.toggle('light-text-on-buttons');
}

function showNotification(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    notificationContainer.appendChild(alertDiv);
    setTimeout(() => {
        const bootstrapAlert = bootstrap.Alert.getOrCreateInstance(alertDiv);
        bootstrapAlert.close();
    }, duration);
}

function fetchDatabases() {
    stopRealtimeUpdates();
    fetch('/api/databases')
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => Promise.reject(errorData));
            }
            return response.json();
        })
        .then(data => {
            dbAccordion.innerHTML = '';
            tableDbNameSelect.innerHTML = '';
            if (data.length > 0) {
                data.forEach(db => {
                    const option = document.createElement('option');
                    option.value = db;
                    option.innerText = db;
                    tableDbNameSelect.appendChild(option);
                });
            }

            data.forEach(db => {
                const dbItem = document.createElement('li');
                dbItem.className = 'nav-item';
                dbItem.innerHTML = `
                    <div class="d-flex align-items-center justify-content-between">
                        <a class="nav-link text-white d-flex justify-content-between align-items-center flex-grow-1" href="#${db}-collapse" data-bs-toggle="collapse" role="button" aria-expanded="false" aria-controls="${db}-collapse" data-db="${db}">
                            ${db}
                        </a>
                        <button class="btn btn-delete-db ms-2" data-db="${db}" style="border-radius: 15px;">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                    <div class="collapse" id="${db}-collapse">
                        <ul class="btn-toggle-nav list-unstyled fw-normal pb-1 small" data-db="${db}" id="tables-for-${db}">
                        </ul>
                    </div>
                `;
                dbAccordion.appendChild(dbItem);
            });
        })
        .catch(error => {
            console.error('Error al obtener las bases de datos:', error);
            mainContent.innerHTML = `<div class="alert alert-danger">Error: ${error.error}</div>`;
        });
}

dbAccordion.addEventListener('click', (e) => {
    const dbLink = e.target.closest('a[data-db]');
    if (dbLink) {
        e.preventDefault();
        stopRealtimeUpdates();
        document.querySelectorAll('.sidebar .nav-link.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.sidebar .btn-toggle-nav a.active').forEach(el => el.classList.remove('active'));

        const dbName = dbLink.getAttribute('data-db');
        currentDb = dbName;
        currentTable = null;
        dbLink.classList.add('active');
        fetchTables(dbName);
        welcomeJumbotron.classList.remove('d-none');
        mainContent.innerHTML = '';
        updateSelectionIndicator();
        return;
    }

    const tableLink = e.target.closest('a[data-table]');
    if (tableLink) {
        e.preventDefault();
        document.querySelectorAll('.sidebar .btn-toggle-nav a.active').forEach(el => el.classList.remove('active'));
        const tableName = e.target.getAttribute('data-table');
        currentTable = tableName;
        tableLink.classList.add('active');
        currentPage = 1;
        currentSearchQuery = '';
        currentSearchAttribute = '';
        fetchTableData(currentPage, perPage, currentSearchQuery, currentSearchAttribute);
        updateSelectionIndicator();
        welcomeJumbotron.classList.add('d-none');
        startRealtimeUpdates();
        return;
    }

    const deleteDbBtn = e.target.closest('.btn-delete-db');
    if (deleteDbBtn) {
        const dbName = deleteDbBtn.getAttribute('data-db');
        if (confirm(`¿Estás seguro de que quieres eliminar la base de datos "${dbName}"? Esta acción es irreversible.`)) {
            fetch(`/api/delete_database/${dbName}`, { method: 'POST' })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errorData => Promise.reject(errorData));
                    }
                    return response.json();
                })
                .then(() => {
                    fetchDatabases();
                    mainContent.innerHTML = '';
                    welcomeJumbotron.classList.remove('d-none');
                    updateSelectionIndicator();
                    showNotification(`Base de datos "${dbName}" eliminada correctamente.`, 'success');
                })
                .catch(error => {
                    console.error('Error al eliminar la base de datos:', error);
                    showNotification(`Error al eliminar la base de datos: ${error.error}`, 'danger');
                });
        }
        return;
    }

    const deleteTableBtn = e.target.closest('.btn-delete-table');
    if (deleteTableBtn) {
        const dbName = deleteTableBtn.getAttribute('data-db');
        const tableName = deleteTableBtn.getAttribute('data-table');
        if (confirm(`¿Estás seguro de que quieres eliminar la tabla "${tableName}" de la base de datos "${dbName}"? Esta acción es irreversible.`)) {
            fetch(`/api/delete_table/${dbName}/${tableName}`, { method: 'POST' })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errorData => Promise.reject(errorData));
                    }
                    return response.json();
                })
                .then(() => {
                    fetchTables(dbName);
                    mainContent.innerHTML = '';
                    welcomeJumbotron.classList.remove('d-none');
                    updateSelectionIndicator();
                    showNotification(`Tabla "${tableName}" eliminada correctamente.`, 'success');
                })
                .catch(error => {
                    console.error('Error al eliminar la tabla:', error);
                    showNotification(`Error al eliminar la tabla: ${error.error}`, 'danger');
                });
        }
    }
});

function fetchTables(dbName) {
    const tableList = document.getElementById(`tables-for-${dbName}`);
    tableList.innerHTML = '<li class="p-2 text-white">Cargando tablas...</li>';

    fetch(`/api/tables/${dbName}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => Promise.reject(errorData));
            }
            return response.json();
        })
        .then(data => {
            tableList.innerHTML = '';
            data.forEach(table => {
                const li = document.createElement('li');
                li.className = "d-flex justify-content-between align-items-center";
                li.innerHTML = `<a class="link-light rounded ps-4 py-1 d-block flex-grow-1" href="#" data-table="${table}">${table}</a>
                                <button class="btn btn-delete-table" data-db="${dbName}" data-table="${table}">
                                    <i class="bi bi-trash"></i>
                                </button>`;
                tableList.appendChild(li);
            });
        })
        .catch(error => {
            console.error('Error al obtener las tablas:', error);
            tableList.innerHTML = `<li class="p-2 text-white">Error: ${error.error}</li>`;
        });
}

function fetchTableData(page = 1, perPage = 30, searchQuery = '', searchAttribute = '') {
    if (!currentDb || !currentTable) {
        mainContent.innerHTML = `<div class="alert alert-danger">Por favor, seleccione una base de datos y una tabla.</div>`;
        return;
    }
    const queryParams = new URLSearchParams({
        page: page,
        per_page: perPage,
        search_query: searchQuery,
        search_attribute: searchAttribute
    });

    fetch(`/api/list/${currentDb}/${currentTable}?${queryParams.toString()}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => Promise.reject(errorData));
            }
            return response.json();
        })
        .then(data => {
            currentSchema = data.schema;
            primaryKey = getPrimaryKeyFromSchema(currentSchema);
            renderTable(data.data, currentSchema, data.total_records, data.current_page, data.per_page);
        })
        .catch(error => {
            mainContent.innerHTML = `<div class="alert alert-danger">Error al cargar la tabla: ${error.error}</div>`;
            console.error('Error:', error);
        });
}

function getPrimaryKeyFromSchema(schema) {
    const pkColumn = schema.find(col => col.Key === 'PRI');
    return pkColumn ? pkColumn.Field : null;
}

function renderTable(data, schema, totalRecords, currentPage, perPage) {
    const headers = schema.map(col => `<th>${col.Field}</th>`).join('');
    const body = data.map(row => {
        const cells = schema.map(col => `<td>${row[col.Field] !== null ? row[col.Field] : ''}</td>`).join('');
        return `<tr>
            ${cells}
            <td>
                <button class="btn btn-sm btn-custom-edit edit-btn" data-id="${row[primaryKey]}">Editar</button>
                <button class="btn btn-sm btn-danger delete-btn" data-id="${row[primaryKey]}">Eliminar</button>
            </td>
        </tr>`;
    }).join('');

    mainContent.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>Listado de ${currentTable}</h2>
            <button class="btn btn-purple" id="add-btn">Añadir Nuevo</button>
        </div>
        <div class="mb-3 d-flex flex-wrap align-items-center justify-content-end gap-2">
            <form id="search-form" class="d-flex flex-grow-1" style="max-width: 600px;">
                <input type="text" class="form-control me-2" placeholder="Buscar..." id="search-input">
                <select class="form-select me-2" id="search-attribute-select" style="width: auto;"></select>
                <button type="submit" class="btn btn-info">Buscar</button>
            </form>
        </div>
        <div class="table-responsive draggable-table-container" id="table-container">
            <table class="table table-striped table-bordered" id="data-table">
                <thead class="thead-dark">
                    <tr>
                        ${headers}
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    ${body}
                </tbody>
            </table>
        </div>
        <div id="pagination-container" class="mt-4"></div>
    `;

    document.getElementById('add-btn').addEventListener('click', () => openFormModal(null));
    document.querySelectorAll('.edit-btn').forEach(btn => btn.addEventListener('click', (e) => {
        openFormModal(e.target.getAttribute('data-id'));
    }));
    document.querySelectorAll('.delete-btn').forEach(btn => btn.addEventListener('click', (e) => {
        deleteItem(e.target.getAttribute('data-id'));
    }));

    renderSearchAndPaginationControls(schema, totalRecords, currentPage, perPage);
}

function renderSearchAndPaginationControls(schema, totalRecords, currentPage, perPage) {
    const searchAttributeSelect = document.getElementById('search-attribute-select');
    searchAttributeSelect.innerHTML = '<option value="">Todos los atributos</option>';
    schema.forEach(col => {
        const option = document.createElement('option');
        option.value = col.Field;
        option.innerText = col.Field;
        searchAttributeSelect.appendChild(option);
    });

    document.getElementById('search-form').addEventListener('submit', handleSearch);
    document.getElementById('search-input').value = currentSearchQuery;
    document.getElementById('search-attribute-select').value = currentSearchAttribute;

    const paginationContainer = document.getElementById('pagination-container');
    paginationContainer.innerHTML = '';

    const totalPages = Math.ceil(totalRecords / perPage);

    if (totalPages > 1) {
        const paginationNav = document.createElement('nav');
        const paginationUl = document.createElement('ul');
        paginationUl.className = 'pagination justify-content-center';

        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage - 1}">Anterior</a>`;
        paginationUl.appendChild(prevLi);

        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            paginationUl.innerHTML += `<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`;
            if (startPage > 2) {
                paginationUl.innerHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
            paginationUl.appendChild(pageLi);
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationUl.innerHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationUl.innerHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a></li>`;
        }

        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage + 1}">Siguiente</a>`;
        paginationUl.appendChild(nextLi);

        paginationNav.appendChild(paginationUl);
        paginationContainer.appendChild(paginationNav);

        paginationContainer.addEventListener('click', handlePaginationClick);
    }
}

function handleSearch(e) {
    e.preventDefault();
    stopRealtimeUpdates();
    const newSearchQuery = document.getElementById('search-input').value;
    const newSearchAttribute = document.getElementById('search-attribute-select').value;

    if (newSearchQuery !== currentSearchQuery || newSearchAttribute !== currentSearchAttribute) {
        currentPage = 1;
        currentSearchQuery = newSearchQuery;
        currentSearchAttribute = newSearchAttribute;
        fetchTableData(currentPage, perPage, currentSearchQuery, currentSearchAttribute);
    }
}

function handlePaginationClick(e) {
    e.preventDefault();
    const pageLink = e.target.closest('.page-link');
    if (pageLink && !pageLink.parentElement.classList.contains('disabled') && !pageLink.parentElement.classList.contains('active')) {
        const newPage = parseInt(pageLink.getAttribute('data-page'));
        currentPage = newPage;
        fetchTableData(currentPage, perPage, currentSearchQuery, currentSearchAttribute);
    }
}

function openFormModal(id) {
    crudForm.innerHTML = '';
    crudForm.setAttribute('data-id', id);

    const isEditing = id !== null;
    crudModalLabel.innerText = isEditing ? `Editar Registro en ${currentTable}` : `Añadir Nuevo Registro en ${currentTable}`;

    const tableContainer = document.getElementById('table-container');
    if (tableContainer) {
        tableContainer.classList.add('main-content-shrunk');
    }

    currentSchema.forEach(column => {
        if (column.Extra.includes('auto_increment')) {
            return;
        }
        if (column.Default && (column.Default.toUpperCase().includes('CURRENT_TIMESTAMP') || column.Default.toUpperCase().includes('NOW()'))) {
            return;
        }

        const div = document.createElement('div');
        div.className = 'mb-3';

        const label = document.createElement('label');
        label.className = 'form-label';
        label.innerText = column.Field;

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control';
        input.name = column.Field;
        input.required = column.Null !== 'YES' && !column.Default;

        if (isEditing && column.Key === 'PRI') {
            input.type = 'hidden';
            input.readOnly = true;
            div.appendChild(input);
        } else {
            div.appendChild(label);
            div.appendChild(input);
        }

        crudForm.appendChild(div);
    });

    if (isEditing) {
        fetch(`/api/manage/${currentDb}/${currentTable}/${id}`)
            .then(response => response.json())
            .then(data => {
                for (const key in data) {
                    const input = crudForm.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.value = data[key];
                    }
                }
            })
            .catch(error => console.error('Error al obtener datos para editar:', error));
    }

    crudModal.show();
}

crudForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const id = crudForm.getAttribute('data-id');
    const isEditing = id !== 'null';

    const formData = new FormData(crudForm);
    const data = Object.fromEntries(formData.entries());

    const url = isEditing ? `/api/manage/${currentDb}/${currentTable}/${id}` : `/api/manage/${currentDb}/${currentTable}`;
    const method = 'POST';

    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => Promise.reject(errorData));
        }
        return response.json();
    })
    .then(() => {
        crudModal.hide();
        fetchTableData(currentPage, perPage, currentSearchQuery, currentSearchAttribute);
        showNotification(isEditing ? 'Registro actualizado correctamente.' : 'Registro agregado correctamente.', 'success');
    })
    .catch(error => {
        console.error('Error al guardar el formulario:', error);
        showNotification(`Error al guardar el registro: ${error.error}`, 'danger');
    });
});

crudModalElement.addEventListener('hidden.bs.modal', () => {
    const tableContainer = document.getElementById('table-container');
    if (tableContainer) {
        tableContainer.classList.remove('main-content-shrunk');
    }
});

function deleteItem(id) {
    if (confirm('¿Está seguro de que desea eliminar este registro?')) {
        fetch(`/api/delete/${currentDb}/${currentTable}/${id}`, { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => Promise.reject(errorData));
                }
                return response.json();
            })
            .then(() => {
                fetchTableData(currentPage, perPage, currentSearchQuery, currentSearchAttribute);
                showNotification('Registro eliminado correctamente.', 'success');
            })
            .catch(error => {
                console.error('Error al eliminar el registro:', error);
                showNotification(`Error al eliminar el registro: ${error.error}`, 'danger');
            });
    }
}

function updateSelectionIndicator() {
    if (currentDb && currentTable) {
        currentDbIndicator.innerText = currentDb;
        currentTableIndicator.innerText = currentTable;
        selectionIndicator.classList.remove('d-none');
    } else {
        selectionIndicator.classList.add('d-none');
    }
}


// --- Funciones para el nuevo modal de creación ---
createDbBtn.addEventListener('click', () => {
    createChoiceStep.classList.add('d-none');
    createDbStep.classList.remove('d-none');
});

createTableBtn.addEventListener('click', () => {
    createChoiceStep.classList.add('d-none');
    createTableStep.classList.remove('d-none');
    fetchDatabases(); // Asegurarse de que el select de BDs está actualizado
});

document.getElementById('back-to-choice-db').addEventListener('click', () => {
    createDbStep.classList.add('d-none');
    createChoiceStep.classList.remove('d-none');
});

document.getElementById('back-to-choice-table').addEventListener('click', () => {
    createTableStep.classList.add('d-none');
    createChoiceStep.classList.remove('d-none');
});

createDbForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const dbName = document.getElementById('new-db-name').value;
    fetch('/api/create_database', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ db_name: dbName })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => Promise.reject(errorData));
        }
        return response.json();
    })
    .then(() => {
        createModal.hide();
        fetchDatabases(); // Recarga la lista de DBs
        showNotification(`Base de datos "${dbName}" creada correctamente.`, 'success');
    })
    .catch(error => {
        console.error('Error al crear la base de datos:', error);
        showNotification(`Error: ${error.error}`, 'danger');
    });
});

addColumnBtn.addEventListener('click', () => {
    const columnCount = columnsContainer.children.length + 1;
    const newColumnRow = document.createElement('div');
    newColumnRow.className = 'column-row';
    newColumnRow.innerHTML = `
        <input type="text" class="form-control column-name" placeholder="Nombre" required>
        <select class="form-select column-type" required>
            <option value="INT">INT</option>
            <option value="VARCHAR">VARCHAR</option>
            <option value="TEXT">TEXT</option>
            <option value="DATE">DATE</option>
            <option value="DATETIME">DATETIME</option>
            <option value="FLOAT">FLOAT</option>
            <option value="BOOLEAN">BOOLEAN</option>
        </select>
        <input type="text" class="form-control column-length" placeholder="Longitud (ej: 255)">
        <div class="form-check">
            <input class="form-check-input column-pk" type="checkbox" id="pk-${columnCount}">
            <label class="form-check-label" for="pk-${columnCount}">PK</label>
        </div>
        <div class="form-check">
            <input class="form-check-input column-nn" type="checkbox" id="nn-${columnCount}">
            <label class="form-check-label" for="nn-${columnCount}">NOT NULL</label>
        </div>
        <div class="form-check">
            <input class="form-check-input column-ai" type="checkbox" id="ai-${columnCount}">
            <label class="form-check-label" for="ai-${columnCount}">AI</label>
        </div>
        <button type="button" class="btn btn-danger remove-column-btn">&times;</button>
    `;
    columnsContainer.appendChild(newColumnRow);
    attachColumnListeners(newColumnRow);
});

function attachColumnListeners(row) {
    const pkCheckbox = row.querySelector('.column-pk');
    const aiCheckbox = row.querySelector('.column-ai');
    const typeSelect = row.querySelector('.column-type');
    const lengthInput = row.querySelector('.column-length');
    const removeBtn = row.querySelector('.remove-column-btn');

    pkCheckbox.addEventListener('change', () => {
        if (pkCheckbox.checked) {
            aiCheckbox.disabled = false;
        } else {
            aiCheckbox.checked = false;
            aiCheckbox.disabled = true;
        }
    });

    typeSelect.addEventListener('change', () => {
        if (typeSelect.value === 'INT' || typeSelect.value === 'VARCHAR') {
            lengthInput.disabled = false;
        } else {
            lengthInput.value = '';
            lengthInput.disabled = true;
        }
    });

    removeBtn.addEventListener('click', () => {
        row.remove();
    });
}

createTableForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const dbName = document.getElementById('table-db-name').value;
    const tableName = document.getElementById('new-table-name').value;
    const columns = [];
    document.querySelectorAll('#columns-container .column-row').forEach(row => {
        const columnName = row.querySelector('.column-name').value;
        const columnType = row.querySelector('.column-type').value;
        const columnLength = row.querySelector('.column-length').value;
        const isPk = row.querySelector('.column-pk').checked;
        const isNotNull = row.querySelector('.column-nn').checked;
        const isAutoIncrement = row.querySelector('.column-ai').checked;
        columns.push({
            name: columnName,
            type: columnType,
            length: columnLength,
            is_pk: isPk,
            is_not_null: isNotNull,
            is_auto_increment: isAutoIncrement
        });
    });

    fetch('/api/create_table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            db_name: dbName,
            table_name: tableName,
            columns: columns
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => Promise.reject(errorData));
        }
        return response.json();
    })
    .then(() => {
        createModal.hide();
        fetchTables(dbName);
        showNotification(`Tabla "${tableName}" creada correctamente en la base de datos "${dbName}".`, 'success');
    })
    .catch(error => {
        console.error('Error al crear la tabla:', error);
        showNotification(`Error: ${error.error}`, 'danger');
    });
});

createModalElement.addEventListener('shown.bs.modal', () => {
    // Restablecer el modal a la vista de elección cada vez que se abre
    createDbStep.classList.add('d-none');
    createTableStep.classList.add('d-none');
    createChoiceStep.classList.remove('d-none');
    // Limpiar formularios
    createDbForm.reset();
    createTableForm.reset();
    columnsContainer.innerHTML = '';
});

function toggleSqlConsole() {
    if (cliModalElement.classList.contains('d-none')) {
        cliModalElement.classList.remove('d-none');
        cliModalElement.classList.add('d-block');
        mainContent.classList.add('d-none');
        stopRealtimeUpdates(); // Detenemos la actualización al cambiar a la consola
    } else {
        cliModalElement.classList.remove('d-block');
        cliModalElement.classList.add('d-none');
        mainContent.classList.remove('d-none');
    }
}

function executeSql(query) {
    printToConsole(query, 'user-query');
    fetch('/api/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            printToConsole(`Error: ${data.error}`, 'text-danger');
        } else if (data.output) {
            if (Array.isArray(data.output)) {
                if (data.output.length > 0) {
                    renderSqlResultsTable(data.output);
                } else {
                    printToConsole('La consulta se ejecutó correctamente. No se encontraron resultados.', 'text-white-50');
                }
            } else {
                printToConsole(data.output, 'text-success');
            }
        }
    })
    .catch(error => {
        printToConsole(`Error de red: ${error}`, 'text-danger');
    });
}

function printToConsole(text, className = '') {
    const line = document.createElement('div');
    line.innerText = text;
    if (className) {
        line.classList.add(className);
    }
    cliOutput.appendChild(line);
    cliOutput.scrollTop = cliOutput.scrollHeight;
}

function renderSqlResultsTable(results) {
    const table = document.createElement('table');
    table.className = 'sql-table-results table-striped table-bordered';
    
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    Object.keys(results[0]).forEach(key => {
        const th = document.createElement('th');
        th.innerText = key;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    results.forEach(row => {
        const tr = document.createElement('tr');
        Object.values(row).forEach(value => {
            const td = document.createElement('td');
            td.innerText = value;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    cliOutput.appendChild(table);
    cliOutput.scrollTop = cliOutput.scrollHeight;
}

// Se elimina la función fetchTableData() duplicada e incompleta del código original.