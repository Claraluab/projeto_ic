// static/js/table.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('Página de tabela carregada');
    
    // Adicionar eventos aos botões de exportação
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.dataset.format;
            const tableName = this.dataset.table;
            exportTableData(tableName, format);
        });
    });
    
    // Adicionar funcionalidade de busca
    const searchInput = document.getElementById('table-search');
    if (searchInput) {
        searchInput.addEventListener('keyup', filterTable);
    }
});

function exportTableData(tableName, format) {
    console.log(`Exportando tabela ${tableName} no formato ${format}`);
    
    if (format === 'csv') {
        window.location.href = `/export/${tableName}`;
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