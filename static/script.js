// ═══════════════════════════════════════════════════
// SpendSense Dashboard Script
// ═══════════════════════════════════════════════════

const CAT_COLORS = {
  Food: '#e84b3a', Transport: '#c9a84c', Entertainment: '#8b5cf6',
  Shopping: '#3a6ee8', Bills: '#6b6659', Health: '#2d9e6b',
  Education: '#0891b2', Other: '#94a3b8'
};

const CAT_ICONS = {
  Food: '🍽', Transport: '🚗', Entertainment: '🎬',
  Shopping: '🛍', Bills: '💡', Health: '❤️',
  Education: '📚', Other: '📦'
};

let lineChart, barChart, donutChart, donutChart2;
let chartsLoaded = false;
let aiLoaded = false;

// ─── Section Navigation ────────────────────────────
function showSection(id, el) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('section-' + id).classList.add('active');
  if (el) el.classList.add('active');

  if (id === 'charts' && !chartsLoaded) loadCharts();
  if (id === 'ai' && !aiLoaded) loadAI();
  if (id === 'overview' && !chartsLoaded) loadDonut();

  return false;
}

// ─── Modals ────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  document.body.style.overflow = '';
}
function openEdit(id, title, amount, category, date, note) {
  document.getElementById('editForm').action = '/edit_expense/' + id;
  document.getElementById('editTitle').value = title;
  document.getElementById('editAmount').value = amount;
  document.getElementById('editCat').value = category;
  document.getElementById('editDate').value = date;
  document.getElementById('editNote').value = note;
  openModal('editModal');
}

// ─── Filter ────────────────────────────────────────
function filterExpenses() {
  const cat = document.getElementById('filterCat').value;
  document.querySelectorAll('#expenseTable tbody tr').forEach(row => {
    row.style.display = (!cat || row.dataset.cat === cat) ? '' : 'none';
  });
}

// ─── Chart Helpers ─────────────────────────────────
function chartDefaults() {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: {
      backgroundColor: '#0d0d0d', titleFont: { family: 'Syne', weight: '700' },
      bodyFont: { family: 'DM Sans' }, padding: 10, cornerRadius: 8,
      callbacks: { label: ctx => ' ₹' + ctx.raw.toLocaleString('en-IN') }
    }}
  };
}

// ─── Load Donut (Overview) ─────────────────────────
async function loadDonut() {
  try {
    const res = await fetch('/api/chart_data');
    const d = await res.json();
    if (!d.category_labels.length) return;

    const colors = d.category_labels.map(l => CAT_COLORS[l] || '#94a3b8');
    const ctx = document.getElementById('donutChart');
    if (!ctx) return;
    if (donutChart) donutChart.destroy();

    donutChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: d.category_labels,
        datasets: [{ data: d.category_data, backgroundColor: colors, borderWidth: 2, borderColor: '#fff', hoverOffset: 6 }]
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          legend: { display: true, position: 'bottom', labels: { font: { family: 'DM Sans', size: 11 }, padding: 12, boxWidth: 10, usePointStyle: true } },
          tooltip: { ...chartDefaults().plugins.tooltip, callbacks: { label: ctx => ' ' + ctx.label + ': ₹' + ctx.raw.toLocaleString('en-IN') } }
        },
        cutout: '65%'
      }
    });
    chartsLoaded = true;
  } catch (e) { console.error('Chart error:', e); }
}

// ─── Load All Charts (Reports) ────────────────────
async function loadCharts() {
  chartsLoaded = true;
  try {
    const res = await fetch('/api/chart_data');
    const d = await res.json();

    // Line chart
    const lCtx = document.getElementById('lineChart');
    if (lineChart) lineChart.destroy();
    lineChart = new Chart(lCtx, {
      type: 'line',
      data: {
        labels: d.daily_labels,
        datasets: [{
          data: d.daily_data,
          borderColor: '#e84b3a', backgroundColor: 'rgba(232,75,58,0.08)',
          borderWidth: 2, pointRadius: 2, pointHoverRadius: 5,
          fill: true, tension: 0.4
        }]
      },
      options: { ...chartDefaults(), scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 10, color: '#6b6659' } },
        y: { grid: { color: '#f0ede5' }, ticks: { font: { size: 10 }, color: '#6b6659', callback: v => '₹' + (v/1000).toFixed(0) + 'k' } }
      }}
    });

    // Bar chart
    const bCtx = document.getElementById('barChart');
    if (barChart) barChart.destroy();
    barChart = new Chart(bCtx, {
      type: 'bar',
      data: {
        labels: d.monthly_labels,
        datasets: [{
          data: d.monthly_data,
          backgroundColor: d.monthly_labels.map((_, i) => i === d.monthly_labels.length - 1 ? '#e84b3a' : '#0d0d0d'),
          borderRadius: 8, borderSkipped: false
        }]
      },
      options: { ...chartDefaults(), scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 }, color: '#6b6659' } },
        y: { grid: { color: '#f0ede5' }, ticks: { font: { size: 10 }, color: '#6b6659', callback: v => '₹' + (v/1000).toFixed(0) + 'k' } }
      }}
    });

    // Donut 2
    if (d.category_labels.length) {
      const dCtx = document.getElementById('donutChart2');
      if (donutChart2) donutChart2.destroy();
      const colors = d.category_labels.map(l => CAT_COLORS[l] || '#94a3b8');
      donutChart2 = new Chart(dCtx, {
        type: 'doughnut',
        data: {
          labels: d.category_labels,
          datasets: [{ data: d.category_data, backgroundColor: colors, borderWidth: 2, borderColor: '#fff', hoverOffset: 6 }]
        },
        options: {
          ...chartDefaults(),
          plugins: {
            ...chartDefaults().plugins,
            legend: { display: true, position: 'bottom', labels: { font: { family: 'DM Sans', size: 11 }, padding: 10, boxWidth: 10, usePointStyle: true } },
            tooltip: { ...chartDefaults().plugins.tooltip, callbacks: { label: ctx => ' ' + ctx.label + ': ₹' + ctx.raw.toLocaleString('en-IN') } }
          },
          cutout: '65%'
        }
      });
    }
  } catch (e) { console.error('Charts error:', e); }
}

// ─── Load AI Insights ──────────────────────────────
async function loadAI() {
  aiLoaded = true;
  document.getElementById('aiLoading').style.display = 'block';
  document.getElementById('aiContent').style.display = 'none';

  try {
    const res = await fetch('/api/ai_insights');
    const d = await res.json();

    // Summary
    const a = d.analysis;
    document.getElementById('aiSummary').innerHTML =
      `You've spent <strong style="color:#fff">₹${a.total.toLocaleString('en-IN')}</strong> in total, averaging <strong style="color:#fff">₹${a.avg_daily.toLocaleString('en-IN')}/day</strong>. Your top spending category is <strong style="color:var(--accent)">${a.top_category}</strong>.`;

    // Predictions
    const predEl = document.getElementById('aiPredictions');
    predEl.innerHTML = '';
    Object.entries(d.predictions).forEach(([cat, amount]) => {
      const color = CAT_COLORS[cat] || '#94a3b8';
      const icon = CAT_ICONS[cat] || '📦';
      predEl.innerHTML += `
        <div class="pred-row">
          <div class="pred-cat"><span style="color:${color}">${icon}</span> ${cat}</div>
          <div class="pred-amount" style="color:${color}">₹${Math.round(amount).toLocaleString('en-IN')}</div>
        </div>`;
    });

    // Alerts
    const alertEl = document.getElementById('aiAlerts');
    alertEl.innerHTML = '';
    d.alerts.forEach(al => {
      const icons = { success: '✓', warning: '⚠', danger: '!', info: 'ℹ' };
      alertEl.innerHTML += `<div class="alert-item ${al.type}"><span>${icons[al.type] || '!'}</span>${al.message}</div>`;
    });

    // Suggestions
    const sugEl = document.getElementById('aiSuggestions');
    sugEl.innerHTML = '';
    a.suggestions.forEach(s => {
      sugEl.innerHTML += `<div class="suggestion-item">${s}</div>`;
    });

    document.getElementById('aiLoading').style.display = 'none';
    document.getElementById('aiContent').style.display = 'block';
  } catch (e) {
    console.error('AI error:', e);
    document.getElementById('aiLoading').innerHTML = '<p style="color:#e84b3a">Failed to load AI insights. Please try again.</p>';
  }
}

// ─── Init ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Load donut on overview
  setTimeout(loadDonut, 300);

  // Keyboard ESC to close modals
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeModal('addModal');
      closeModal('editModal');
    }
  });
});
