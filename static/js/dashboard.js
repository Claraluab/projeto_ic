// static/js/dashboard.js
'use strict';

// === Estado de filtros (compartilhado) ===
let currentFilters = { start: "", end: "", subs: [] };

// ===== Utils =====
function showAlert(message, type = 'info') {
  // Remove alertas existentes
  const existingAlerts = document.querySelectorAll('.alert-dismissible');
  existingAlerts.forEach(alert => alert.remove());

  // Cria novo alerta
  const alert = document.createElement('div');
  alert.className = `alert alert-${type} alert-dismissible fade show`;
  alert.innerHTML = `
      <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'}"></i> 
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  // Adiciona no início do container principal
  const container = document.querySelector('.container');
  if (container) {
    container.insertBefore(alert, container.firstChild);
  } else {
    document.body.prepend(alert);
  }

  // Remove automático
  setTimeout(() => {
    if (alert.parentNode) {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (_) {
        alert.remove();
      }
    }
  }, 5000);
}

function buildQueryString(filters) {
  const params = new URLSearchParams();
  if (filters.start) params.append('start', filters.start);
  if (filters.end) params.append('end', filters.end);
  if (filters.subs && filters.subs.length) params.append('subs', filters.subs.join(','));
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

// ===== Gráficos =====
function createChart(data, elementId, title, chartType) {
  console.log(`Criando gráfico ${chartType} com ${data.length} pontos de dados`);

  const subsistemas = [...new Set(data.map(item => item.submarket))];
  const plotData = [];

  if (chartType === 'geracao') {
    const fontes = ['hydro', 'thermal', 'wind', 'solar'];
    const nomesFontes = { hydro: 'Hidráulica', thermal: 'Térmica', wind: 'Eólica', solar: 'Solar' };

    fontes.forEach(fonte => {
      subsistemas.forEach(subsistema => {
        const subsistemaData = data.filter(item => item.submarket === subsistema);
        plotData.push({
          x: subsistemaData.map(item => new Date(item.date)),
          y: subsistemaData.map(item => item[fonte] || 0),
          type: 'scatter',
          mode: 'lines',
          name: `${subsistema} - ${nomesFontes[fonte]}`,
          hovertemplate:
            '%{x|%d/%m/%Y}<br>' +
            `${nomesFontes[fonte]}: %{y:.2f} MWmed<extra>${subsistema}</extra>`
        });
      });
    });
  } else {
    const valorKey = chartType; // pld, ena, ear, cmo
    const unidades = { pld: 'R$/MWh', ena: 'MWmed', ear: 'MWmed', cmo: 'R$/MWh' };

    subsistemas.forEach(subsistema => {
      const subsistemaData = data.filter(item => item.submarket === subsistema);
      plotData.push({
        x: subsistemaData.map(item => new Date(item.date)),
        y: subsistemaData.map(item => item[valorKey]),
        type: 'scatter',
        mode: 'lines',
        name: subsistema,
        hovertemplate:
          '%{x|%d/%m/%Y}<br>' +
          `Valor: %{y:.2f} ${unidades[valorKey]}<extra>${subsistema}</extra>`
      });
    });
  }

  const layout = {
    title: { text: title, font: { size: 18, family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif' } },
    xaxis: { title: 'Data', showgrid: true, gridcolor: '#f0f0f0', tickformat: '%d/%m/%Y' },
    yaxis: { title: 'Valor', showgrid: true, gridcolor: '#f0f0f0' },
    hovermode: 'closest',
    plot_bgcolor: '#fff',
    paper_bgcolor: '#fff',
    font: { family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif' },
    legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 },
    margin: { l: 60, r: 40, b: 60, t: 80, pad: 4 }
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

function loadChart(chartType, elementId, title) {
  console.log(`Carregando gráfico: ${chartType}`);

  const target = document.getElementById(elementId);
  if (!target) return;

  target.innerHTML = `
    <div class="loading">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Carregando...</span>
      </div>
      <p class="mt-2">Carregando dados...</p>
    </div>
  `;

  const qs = buildQueryString(currentFilters);

  fetch(`/api/dashboard/${chartType}${qs}`)
    .then(response => {
      if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
      return response.json();
    })
    .then(data => {
      if (data.error) throw new Error(data.error);
      if (typeof createChart !== 'function') {
        throw new ReferenceError('Função createChart não carregada');
      }
      createChart(data, elementId, title, chartType);
    })
    .catch(error => {
      console.error('Erro ao carregar dados:', error);
      target.innerHTML = `
        <div class="alert alert-danger">
          <i class="bi bi-exclamation-triangle-fill"></i> 
          Erro ao carregar dados: ${error.message}
        </div>
      `;
    });
}

function updateDashboard() {
  const chartIds   = ['pld-chart', 'ena-chart', 'ear-chart', 'cmo-chart', 'geracao-chart'];
  const chartTypes = ['pld',       'ena',       'ear',       'cmo',       'geracao'];
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
}

// === Filtros ===
function applyFilters() {
  const start = document.getElementById('startDate')?.value || "";
  const end   = document.getElementById('endDate')?.value || "";
  const sel   = document.getElementById('subsistemaSelect');
  const subs  = sel ? Array.from(sel.selectedOptions).map(o => o.value) : [];

  if (start && end && new Date(start) > new Date(end)) {
    showAlert('A data inicial não pode ser maior que a final.', 'danger');
    return;
  }

  currentFilters = { start, end, subs };
  updateDashboard();
  showAlert('Filtros aplicados.', 'success');
}

// ===== Expõe funções no escopo global (garantia) =====
window.showAlert = showAlert;
window.buildQueryString = buildQueryString;
window.createChart = createChart;
window.loadChart = loadChart;
window.updateDashboard = updateDashboard;
window.applyFilters = applyFilters;

// ===== Bootstrap inicial =====
document.addEventListener('DOMContentLoaded', function () {
  console.log('Dashboard carregado');

  // (Opcional) Defina período padrão aqui
  // const today = new Date();
  // const prior = new Date(); prior.setDate(today.getDate() - 90);
  // document.getElementById('startDate').value = prior.toISOString().slice(0,10);
  // document.getElementById('endDate').value = today.toISOString().slice(0,10);
  // currentFilters.start = document.getElementById('startDate').value;
  // currentFilters.end   = document.getElementById('endDate').value;

  updateDashboard();
}); 