// static/js/admin.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('Página administrativa carregada');
    
    // Adicionar evento ao botão de atualização
    const updateBtn = document.getElementById('update-data-btn');
    if (updateBtn) {
        updateBtn.addEventListener('click', updateData);
    }
    
    // Adicionar evento ao botão de inicialização do banco
    const initDbBtn = document.getElementById('init-db-btn');
    if (initDbBtn) {
        initDbBtn.addEventListener('click', initializeDatabase);
    }
});

function updateData() {
    if (confirm('Tem certeza que deseja atualizar os dados? Esta operação pode demorar vários minutos.')) {
        // Mostrar indicador de carregamento
        const updateBtn = document.getElementById('update-data-btn');
        const originalText = updateBtn.innerHTML;
        updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Atualizando...';
        updateBtn.disabled = true;
        
        fetch('/api/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // Recarregar a página após 3 segundos para atualizar estatísticas
                setTimeout(() => {
                    location.reload();
                }, 3000);
            } else {
                showAlert(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            showAlert('Erro ao atualizar dados: ' + error.message, 'danger');
        })
        .finally(() => {
            // Restaurar botão
            updateBtn.innerHTML = originalText;
            updateBtn.disabled = false;
        });
    }
}

function initializeDatabase() {
    if (confirm('ATENÇÃO: Esta operação irá inicializar o banco de dados. Tem certeza que deseja continuar?')) {
        // Mostrar indicador de carregamento
        const initBtn = document.getElementById('init-db-btn');
        const originalText = initBtn.innerHTML;
        initBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Inicializando...';
        initBtn.disabled = true;
        
        fetch('/init-db')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert(data.message, 'success');
                // Recarregar a página após 5 segundos
                setTimeout(() => {
                    location.reload();
                }, 5000);
            } else {
                showAlert(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            showAlert('Erro ao inicializar banco de dados: ' + error.message, 'danger');
        })
        .finally(() => {
            // Restaurar botão
            initBtn.innerHTML = originalText;
            initBtn.disabled = false;
        });
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