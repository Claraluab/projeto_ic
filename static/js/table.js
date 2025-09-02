document.addEventListener('DOMContentLoaded', function() {
    console.log('Página de tabela carregada');
    
    // Adicionar eventos aos botões de exportação
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.dataset.format;
            const tableName = this.dataset.table;
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            exportTableData(tableName, format, startDate, endDate);
        });
    });
    
    // Adicionar funcionalidade de busca
    const searchInput = document.getElementById('table-search');
    if (searchInput) {
        searchInput.addEventListener('keyup', filterTable);
    }
    
    // Adicionar funcionalidade ao filtro de data
    const applyDateFilter = document.getElementById('apply-date-filter');
    if (applyDateFilter) {
        applyDateFilter.addEventListener('click', applyDateFilterToTable);
    }
    
    // Adicionar funcionalidade ao botão de limpar filtro
    const clearDateFilter = document.getElementById('clear-date-filter');
    if (clearDateFilter) {
        clearDateFilter.addEventListener('click', clearDateFilterFromTable);
    }
    
    // Verificar se há parâmetros de data na URL e preencher os campos
    const urlParams = new URLSearchParams(window.location.search);
    const startDateParam = urlParams.get('start_date');
    const endDateParam = urlParams.get('end_date');
    
    if (startDateParam) {
        document.getElementById('start-date').value = startDateParam;
    }
    
    if (endDateParam) {
        document.getElementById('end-date').value = endDateParam;
    }
});

function exportTableData(tableName, format, startDate, endDate) {
    console.log(`Exportando tabela ${tableName} no formato ${format} de ${startDate} até ${endDate}`);
    
    if (format === 'csv') {
        let url = `/export/${tableName}`;
        const params = [];
        
        if (startDate) {
            params.push(`start_date=${encodeURIComponent(startDate)}`);
        }
        
        if (endDate) {
            params.push(`end_date=${encodeURIComponent(endDate)}`);
        }
        
        if (params.length > 0) {
            url += `?${params.join('&')}`;
        }
        
        window.location.href = url;
    } else {
        showAlert(`Exportação no formato ${format.toUpperCase()} em desenvolvimento`, 'info');
    }
}

function filterTable() {
    const input = document.getElementById('table-search');
    const filter = input.value.toUpperCase();
    const table = document.querySelector('.table');
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        let found = false;
        const cells = rows[i].getElementsByTagName('td');
        
        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
            if (cell) {
                const textValue = cell.textContent || cell.innerText;
                if (textValue.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        
        if (found) {
            rows[i].style.display = '';
        } else {
            rows[i].style.display = 'none';
        }
    }
}

function applyDateFilterToTable() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    // Obter o nome da tabela da URL atual
    const pathParts = window.location.pathname.split('/');
    const tableName = pathParts[pathParts.length - 1];
    
    // Construir a URL com os parâmetros de filtro
    let url = `/tabelas/${tableName}?`;
    const params = [];
    
    if (startDate) {
        params.push(`start_date=${encodeURIComponent(startDate)}`);
    }
    
    if (endDate) {
        params.push(`end_date=${encodeURIComponent(endDate)}`);
    }
    
    // Manter o parâmetro de página se existir
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page');
    
    if (page) {
        params.push(`page=${page}`);
    }
    
    if (params.length > 0) {
        url += params.join('&');
    }
    
    window.location.href = url;
}

function clearDateFilterFromTable() {
    // Obter o nome da tabela da URL atual
    const pathParts = window.location.pathname.split('/');
    const tableName = pathParts[pathParts.length - 1];
    
    // Manter o parâmetro de página se existir
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page');
    
    let url = `/tabelas/${tableName}`;
    
    if (page) {
        url += `?page=${page}`;
    }
    
    window.location.href = url;
}


function showAlert(message, type = 'info') {
    // Remover alertas existentes
    const existingAlerts = document.querySelectorAll('.alert-dismissible');
    existingAlerts.forEach(alert => alert.remove());
    
    // Criar novo alerta
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : 'info-circle'}"></i> 
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Adicionar alerta no início do conteúdo
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    // Remover automaticamente após 5 segundos
    setTimeout(() => {
        if (alert.parentNode) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
} 