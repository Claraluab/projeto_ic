// static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard carregado');
    
    // Carregar gráficos
    loadChart('pld', 'pld-chart', 'PLD por Subsistema (R$/MWh)');
    loadChart('ena', 'ena-chart', 'ENA por Subsistema (MWmed)');
    loadChart('ear', 'ear-chart', 'EAR por Subsistema (MWmed)');
    loadChart('cmo', 'cmo-chart', 'CMO por Subsistema (R$/MWh)');
    loadChart('geracao', 'geracao-chart', 'Geração por Fonte (MWmed)');
});

function loadChart(chartType, elementId, title) {
    console.log(`Carregando gráfico: ${chartType}`);
    
    // Mostrar indicador de carregamento
    document.getElementById(elementId).innerHTML = `
        <div class="loading">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
            <p class="mt-2">Carregando dados...</p>
        </div>
    `;
    
    fetch(`/api/dashboard/${chartType}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            createChart(data, elementId, title, chartType);
        })
        .catch(error => {
            console.error('Erro ao carregar dados:', error);
            document.getElementById(elementId).innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i> 
                    Erro ao carregar dados: ${error.message}
                </div>
            `;
        });
}

function createChart(data, elementId, title, chartType) {
    console.log(`Criando gráfico ${chartType} com ${data.length} pontos de dados`);
    
    // Agrupar dados por subsistema
    const subsistemas = [...new Set(data.map(item => item.submarket))];
    const plotData = [];
    
    if (chartType === 'geracao') {
        // Gráfico de geração por fonte
        const fontes = ['hydro', 'thermal', 'wind', 'solar'];
        const nomesFontes = {
            'hydro': 'Hidráulica',
            'thermal': 'Térmica',
            'wind': 'Eólica',
            'solar': 'Solar'
        };
        
        // Para cada fonte, criar uma série para cada subsistema
        fontes.forEach(fonte => {
            subsistemas.forEach(subsistema => {
                const subsistemaData = data.filter(item => item.submarket === subsistema);
                
                plotData.push({
                    x: subsistemaData.map(item => new Date(item.date)),
                    y: subsistemaData.map(item => item[fonte] || 0),
                    type: 'scatter',
                    mode: 'lines',
                    name: `${subsistema} - ${nomesFontes[fonte]}`,
                    hovertemplate: '%{x|%d/%m/%Y}<br>' + 
                                 `${nomesFontes[fonte]}: %{y:.2f} MWmed<extra>${subsistema}</extra>`
                });
            });
        });
    } else {
        // Gráficos de PLD, ENA, EAR, CMO
        const valorKey = chartType; // pld, ena, ear, cmo
        const unidades = {
            'pld': 'R$/MWh',
            'ena': 'MWmed',
            'ear': 'MWmed',
            'cmo': 'R$/MWh'
        };
        
        subsistemas.forEach(subsistema => {
            const subsistemaData = data.filter(item => item.submarket === subsistema);
            
            plotData.push({
                x: subsistemaData.map(item => new Date(item.date)),
                y: subsistemaData.map(item => item[valorKey]),
                type: 'scatter',
                mode: 'lines',
                name: subsistema,
                hovertemplate: '%{x|%d/%m/%Y}<br>' + 
                             `Valor: %{y:.2f} ${unidades[valorKey]}<extra>${subsistema}</extra>`
            });
        });
    }
    
    const layout = {
        title: {
            text: title,
            font: {
                size: 18,
                family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'
            }
        },
        xaxis: {
            title: 'Data',
            showgrid: true,
            gridcolor: '#f0f0f0',
            tickformat: '%d/%m/%Y'
        },
        yaxis: {
            title: 'Valor',
            showgrid: true,
            gridcolor: '#f0f0f0'
        },
        hovermode: 'closest',
        plot_bgcolor: '#fff',
        paper_bgcolor: '#fff',
        font: {
            family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'
        },
        legend: {
            orientation: 'h',
            yanchor: 'bottom',
            y: 1.02,
            xanchor: 'right',
            x: 1
        },
        margin: {
            l: 60,
            r: 40,
            b: 60,
            t: 80,
            pad: 4
        }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        modeBarButtonsToAdd: ['hoverClosestGl2d']
    };
    
    Plotly.newPlot(elementId, plotData, layout, config);
}

// Função para atualizar o dashboard
function updateDashboard() {
    if (confirm('Tem certeza que deseja atualizar todos os gráficos?')) {
        // Recarregar todos os gráficos
        const chartIds = ['pld-chart', 'ena-chart', 'ear-chart', 'cmo-chart', 'geracao-chart'];
        const chartTypes = ['pld', 'ena', 'ear', 'cmo', 'geracao'];
        const chartTitles = [
            'PLD por Subsistema (R$/MWh)',
            'ENA por Subsistema (MWmed)',
            'EAR por Subsistema (MWmed)',
            'CMO por Subsistema (R$/MWh)',
            'Geração por Fonte (MWmed)'
        ];
        
        chartIds.forEach((id, index) => {
            loadChart(chartTypes[index], id, chartTitles[index]);
        });
        
        // Mostrar mensagem de sucesso
        showAlert('Gráficos atualizados com sucesso!', 'success');
    }
}

// Função para mostrar alertas
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

// Funções para filtrar dados (a serem implementadas)
function applyFilters() {
    console.log('Aplicando filtros...');
    // Implementar lógica de filtros
    showAlert('Funcionalidade de filtros em desenvolvimento', 'info');
}

function exportChartData(chartType) {
    console.log(`Exportando dados do gráfico: ${chartType}`);
    // Implementar exportação de dados
    showAlert('Funcionalidade de exportação em desenvolvimento', 'info');
}