// --- Configuration ---
const API_BASE = '/api/v1';

// --- State Management ---
let currentView = 'dashboard';
let charts = {};
let warRoomInterval = null;
let viewState = {
    products: { query: '', sortBy: 'id', sortOrder: 'desc', page: 1, limit: 100, filters: { category: '' } },
    orders: { query: '', sortBy: 'created_at', sortOrder: 'desc', page: 1, limit: 100, filters: { status: '' } },
    users: { query: '', sortBy: 'id', sortOrder: 'desc', page: 1, limit: 100, filters: { segment: '' } },
    sales: { activeTab: 'orders' },
    globalFilters: {
        startDate: '',
        endDate: '',
        category: '',
        segment: ''
    }
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    lucide.createIcons();
    initNavigation();
    initAIChat();
    loadView('dashboard');
});

// --- Navigation ---
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const view = item.getAttribute('data-view');
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            loadView(view);
        });
    });
}

async function loadView(view) {
    currentView = view;
    const container = document.getElementById('content-view');
    
    // Clear war room interval if switching away
    if (warRoomInterval) {
        clearInterval(warRoomInterval);
        warRoomInterval = null;
    }

    // 1. Re-render the container base with the sticky filter bar
    container.innerHTML = `
        <div id="filter-bar-container"></div>
        <div id="view-content-area" class="view-container">
            <div class="loading-spinner"><div class="spinner"></div></div>
        </div>
    `;
    
    // 2. Render the Filter Bar
    renderGlobalFilterBar(document.getElementById('filter-bar-container'));

    const contentArea = document.getElementById('view-content-area');
    const titleEl = document.getElementById('view-title');
    const viewTitles = {
        'dashboard': 'Dashboard',
        'sales': 'Sales Hub',
        'analytics': 'Analytics & Reports',
        'whatif': 'What-If Analysis',
        'monitoring': 'Live Monitoring'
    };
    if (titleEl) titleEl.textContent = viewTitles[view] || view.charAt(0).toUpperCase() + view.slice(1);

    try {
        switch (view) {
            case 'dashboard':
                await renderDashboard(contentArea);
                break;
            case 'sales':
                await renderSales(contentArea);
                break;
            case 'analytics':
                await renderIntelligence(contentArea);
                break;
            case 'whatif':
                await renderWhatIfHub(contentArea);
                break;
            case 'monitoring':
                await renderWarRoom(contentArea);
                break;
        }
    } catch (error) {
        console.error('Error loading view:', error);
        contentArea.textContent = `Failed to load view: ${error.message}`;
    }
    
    lucide.createIcons();
}

/**
 * --- WHAT-IF STRATEGIC HUB ---
 */
async function renderWhatIfHub(container) {
    container.innerHTML = `
        <div class="charts-row" style="grid-template-columns: 320px 1fr; gap: 32px; align-items: start;">
            <!-- Simulation Controls Sidebar -->
            <div class="card" style="background: rgba(255,255,255,0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); position: sticky; top: 100px;">
                <div class="flex items-center gap-2 mb-6 text-accent">
                    <i data-lucide="sliders" class="w-5 h-5"></i>
                    <h3 class="m-0">Scenario Controls</h3>
                </div>
                
                <div class="flex-stack-gap" style="gap: 24px;">
                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <label class="text-xs text-secondary uppercase font-bold tracking-wider">Price Change</label>
                            <span id="label-price" class="text-xs font-bold text-accent">0%</span>
                        </div>
                        <input type="range" id="sim-price" min="-50" max="50" value="0" class="w-full accentuate">
                    </div>

                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <label class="text-xs text-secondary uppercase font-bold tracking-wider">Order Volume</label>
                            <span id="label-volume" class="text-xs font-bold text-accent">0%</span>
                        </div>
                        <input type="range" id="sim-volume" min="-50" max="50" value="0" class="w-full accentuate">
                    </div>

                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <label class="text-xs text-secondary uppercase font-bold tracking-wider">Customer Retention</label>
                            <span id="label-retention" class="text-xs font-bold text-accent">0%</span>
                        </div>
                        <input type="range" id="sim-retention" min="-50" max="50" value="0" class="w-full accentuate">
                    </div>

                    <div style="padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.05);">
                        <button id="reset-sim" class="btn btn-accent w-full" style="background: transparent; border: 1px solid var(--accent-color); color: var(--accent-color);">Reset Baseline</button>
                    </div>
                </div>
            </div>

            <!-- Main Simulation Results -->
            <div class="flex-stack-gap" style="gap: 32px;">
                <div class="grid-responsive" style="grid-template-columns: repeat(3, 1fr); gap: 24px;">
                    <div class="kpi-card" style="background: var(--sidebar-bg); border-left: 4px solid var(--accent-color);">
                        <div class="kpi-label">Projected Revenue Delta</div>
                        <div id="impact-revenue" class="kpi-value">+$0.00</div>
                        <div id="impact-revenue-pct" class="text-xs mt-1 text-success">0.0% increase</div>
                    </div>
                    <div class="kpi-card" style="background: var(--sidebar-bg); border-left: 4px solid var(--success-color);">
                        <div class="kpi-label">Projected Profit Delta</div>
                        <div id="impact-profit" class="kpi-value">+$0.00</div>
                        <p class="text-xs text-secondary mt-1">Based on 30% baseline margin</p>
                    </div>
                    <div class="kpi-card" style="background: var(--sidebar-bg); border-left: 4px solid var(--warning-color);">
                        <div class="kpi-label">Simulation Stability</div>
                        <div class="kpi-value">HIGH</div>
                        <p class="text-xs text-secondary mt-1">ML Confidence: 94.2%</p>
                    </div>
                </div>

                <div class="chart-container" style="min-height: 500px;">
                    <div class="flex justify-between items-center mb-6">
                        <div>
                            <h3 class="m-0">Trajectory Comparison</h3>
                            <p class="text-xs text-secondary mt-1">Baseline vs. Simulated Outcome (30 Days)</p>
                        </div>
                        <div class="flex gap-4">
                            <div class="items-center gap-2 text-xs text-secondary" style="display: flex;"><span style="width: 12px; height: 12px; border: 2px dashed #6366f1; border-radius: 2px;"></span> Baseline</div>
                            <div class="items-center gap-2 text-xs text-secondary" style="display: flex;"><span style="width: 12px; height: 12px; background: #10b981; border-radius: 2px;"></span> Scenario</div>
                        </div>
                    </div>
                    <canvas id="whatIfChart"></canvas>
                </div>
            </div>
        </div>
    `;

    lucide.createIcons();

    const sliders = {
        price: document.getElementById('sim-price'),
        volume: document.getElementById('sim-volume'),
        retention: document.getElementById('sim-retention')
    };
    const labels = {
        price: document.getElementById('label-price'),
        volume: document.getElementById('label-volume'),
        retention: document.getElementById('label-retention')
    };

    const runSimulation = debounce(async () => {
        const pVal = parseInt(sliders.price.value);
        const vVal = parseInt(sliders.volume.value);
        const rVal = parseInt(sliders.retention.value);
        
        labels.price.textContent = `${pVal > 0 ? '+' : ''}${pVal}%`;
        labels.volume.textContent = `${vVal > 0 ? '+' : ''}${vVal}%`;
        labels.retention.textContent = `${rVal > 0 ? '+' : ''}${rVal}%`;

        const pMult = 1 + (pVal / 100);
        const vMult = 1 + (vVal / 100);
        const rMult = 1 + (rVal / 100);

        try {
            const data = await fetchApi(`/analytics/what-if-forecast?price_mult=${pMult}&volume_mult=${vMult}&retention_mult=${rMult}`);
            renderWhatIfChart(data);
            updateImpactScoreboard(data);
        } catch (e) {
            console.error("Simulation error", e);
        }
    }, 150);

    Object.values(sliders).forEach(s => s.addEventListener('input', runSimulation));
    document.getElementById('reset-sim').addEventListener('click', () => {
        Object.values(sliders).forEach(s => s.value = 0);
        runSimulation();
    });
    runSimulation();
}

function updateImpactScoreboard(data) {
    const meta = data.metadata.scenario;
    const revDelta = data.simulated_forecast.reduce((sum, d) => sum + d.revenue, 0) - 
                   data.baseline_forecast.reduce((sum, d) => sum + d.revenue, 0);
    const profitDelta = data.simulated_forecast.reduce((sum, d) => sum + d.profit, 0) - 
                      (data.baseline_forecast.reduce((sum, d) => sum + d.revenue, 0) * 0.3);

    const revEl = document.getElementById('impact-revenue');
    const revPctEl = document.getElementById('impact-revenue-pct');
    const profitEl = document.getElementById('impact-profit');

    if (revEl) {
        revEl.textContent = `${revDelta >= 0 ? '+' : ''}$${Math.abs(revDelta).toLocaleString(undefined, {maximumFractionDigits: 0})}`;
        revEl.style.color = revDelta >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
    }
    if (revPctEl) {
        revPctEl.textContent = `${meta.net_revenue_delta_percent >= 0 ? '+' : ''}${meta.net_revenue_delta_percent}% shift`;
        revPctEl.className = `text-xs mt-1 ${meta.net_revenue_delta_percent >= 0 ? 'text-success' : 'text-danger'}`;
    }
    if (profitEl) {
        profitEl.textContent = `${profitDelta >= 0 ? '+' : ''}$${Math.abs(profitDelta).toLocaleString(undefined, {maximumFractionDigits: 0})}`;
        profitEl.style.color = profitDelta >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
    }
}

function renderWhatIfChart(data) {
    const ctx = document.getElementById('whatIfChart');
    if (!ctx) return;
    
    const baseline = data.baseline_forecast || [];
    const simulated = data.simulated_forecast || [];
    const labels = baseline.map(d => new Date(d.date).toLocaleDateString(undefined, {month: 'short', day: 'numeric'}));

    if (charts.whatif) charts.whatif.destroy();

    charts.whatif = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Simulated Scenario',
                    data: simulated.map(d => d.revenue),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    borderWidth: 3
                },
                {
                    label: 'Baseline Forecast',
                    data: baseline.map(d => d.revenue),
                    borderColor: '#6366f1',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { mode: 'index', intersect: false, backgroundColor: '#1e293b' }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } }
            }
        }
    });
}

function renderGlobalFilterBar(container) {
    const f = viewState.globalFilters;
    container.innerHTML = `
        <div class="global-filter-bar">
            <div class="filter-group">
                <span class="filter-label">Date Range</span>
                <input type="date" id="filter-start" class="filter-input" value="${f.startDate}">
                <span style="color:var(--text-secondary)">to</span>
                <input type="date" id="filter-end" class="filter-input" value="${f.endDate}">
            </div>
            
            <div class="filter-group">
                <span class="filter-label">Category</span>
                <select id="filter-category" class="filter-input">
                    <option value="">All Categories</option>
                    <option value="Hardware" ${f.category === 'Hardware' ? 'selected' : ''}>Hardware</option>
                    <option value="Software" ${f.category === 'Software' ? 'selected' : ''}>Software</option>
                    <option value="Peripherals" ${f.category === 'Peripherals' ? 'selected' : ''}>Peripherals</option>
                    <option value="Furniture" ${f.category === 'Furniture' ? 'selected' : ''}>Furniture</option>
                </select>
            </div>

            <div class="filter-group">
                <span class="filter-label">Segment</span>
                <select id="filter-segment" class="filter-input">
                    <option value="">All Segments</option>
                    <option value="Enterprise" ${f.segment === 'Enterprise' ? 'selected' : ''}>Enterprise</option>
                    <option value="SMB" ${f.segment === 'SMB' ? 'selected' : ''}>SMB</option>
                    <option value="Retail" ${f.segment === 'Retail' ? 'selected' : ''}>Retail</option>
                    <option value="Individual" ${f.segment === 'Individual' ? 'selected' : ''}>Individual</option>
                </select>
            </div>

            <div class="filter-group" style="margin-left: auto;">
                <button class="btn-filter" id="apply-filters">Apply Filters</button>
                <button class="btn-reset" id="reset-filters">Reset</button>
            </div>
        </div>
    `;

    document.getElementById('apply-filters').addEventListener('click', () => {
        viewState.globalFilters.startDate = document.getElementById('filter-start').value;
        viewState.globalFilters.endDate = document.getElementById('filter-end').value;
        viewState.globalFilters.category = document.getElementById('filter-category').value;
        viewState.globalFilters.segment = document.getElementById('filter-segment').value;
        loadView(currentView); // Re-render current view with new filters
    });

    document.getElementById('reset-filters').addEventListener('click', () => {
        viewState.globalFilters = { startDate: '', endDate: '', category: '', segment: '' };
        loadView(currentView);
    });
}

// --- View Renderers ---

async function renderDashboard(container) {
    const [ordersRes, productsRes, usersRes, revenueData, insights, drilldownData] = await Promise.all([
        fetchApi('/orders/', { limit: 10 }), // Only need recent for dashboard
        fetchApi('/products/', { limit: 5 }), 
        fetchApi('/users/', { limit: 5 }),
        fetchApi('/orders/analytics/revenue'),
        fetchApi('/analytics/insights'),
        fetchApi('/analytics/drilldown') // Pulls foundational 30-day top products and segments
    ]);

    const orders = ordersRes.items;
    const products = productsRes.items;
    const users = usersRes.items;

    const activeOrdersArr = orders.filter(o => o.status !== 'cancelled');
    const totalRevenue = activeOrdersArr.reduce((acc, o) => acc + (o.total_price || 0), 0);
    const avgOrderValue = activeOrdersArr.length > 0 ? totalRevenue / activeOrdersArr.length : 0;
    const growthRate = 12.5; // Simulate a growth metric

    container.innerHTML = `
        <div class="kpi-grid mb-6" id="dashboard-kpi-container">
            ${Array(4).fill(0).map(() => `<div class="kpi-card skeleton-loading" style="height: 160px;"></div>`).join('')}
        </div>


        <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
                <h3 class="m-0">💡 Strategy Action Board</h3>
                <span class="status-badge badge-accent">AI Generated Insights</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; align-items: stretch;">
                ${renderPulseInsights(insights.ai_pulse)}
            </div>
        </div>

        <div class="chart-hero-container mb-8">
            <div id="revenue-analysis-summary" class="chart-brief-header">
                <div class="skeleton-loading h-20 w-full rounded"></div>
            </div>
            <div class="chart-container" id="revenue-container" style="height: 450px !important;">
                <div class="flex justify-between items-center mb-6">
                    <div class="flex items-center gap-3">
                        <h3 class="m-0">Revenue Trajectory</h3>
                        <span class="status-badge badge-accent">Live Analysis</span>
                    </div>
                    <div class="flex gap-2">
                        <button class="reset-zoom-btn" onclick="resetChartZoom('revenue')">Reset View</button>
                    </div>
                </div>
                <div style="flex-grow: 1; min-height: 350px;">
                    <canvas id="revenueChart"></canvas>
                </div>
            </div>
        </div>

        
        <h3 class="mb-4">Audience & Product Distribution</h3>
        <div class="bento-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 32px;">
            <div class="chart-container border-l-accent" style="border-left: 4px solid var(--accent-color); height: auto !important; min-height: 500px;">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="m-0">Core Demographics</h3>
                    <span class="status-badge badge-accent">Strategic Segments</span>
                </div>
                <div id="segments-analysis" class="analysis-banner"></div>
                <div style="position: relative; height: 300px;">
                    <canvas id="segmentsChart"></canvas>
                </div>
            </div>
            <div class="chart-container border-l-success" style="border-left: 4px solid #10b981; height: auto !important; min-height: 500px;">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="m-0">Product Revenue Drivers</h3>
                    <span class="status-badge badge-success">Top Movers</span>
                </div>
                <div id="products-analysis" class="analysis-banner"></div>
                <div style="position: relative; height: 300px;">
                    <canvas id="topProductsChart"></canvas>
                </div>
            </div>
        </div>

    `;

    renderRevenueChart(revenueData);
    renderBreakdownCharts(drilldownData);
    loadDashboardKPIs(); 
    renderRevenueAnalysis(revenueData);
}

function renderRevenueAnalysis(data) {
    const analysis = analyzeRevenueTrends(data);
    const container = document.getElementById('revenue-analysis-summary');
    if (!container || !analysis) return;

    const trendClass = parseFloat(analysis.trend) >= 0 ? 'text-success' : 'text-danger';
    const trendIcon = parseFloat(analysis.trend) >= 0 ? 'trending-up' : 'trending-down';

    container.innerHTML = `
        <div class="analysis-grid">
            <div class="analysis-item">
                <span class="label">Historical Peak</span>
                <span class="value">$${analysis.peak.revenue.toLocaleString()}</span>
                <span class="subtext">Recorded on ${new Date(analysis.peak.date).toLocaleDateString()}</span>
            </div>
            <div class="analysis-item">
                <span class="label">Growth Momentum</span>
                <span class="value ${trendClass}">${analysis.trend}%</span>
                <span class="subtext"><i data-lucide="${trendIcon}" class="inline w-3 h-3"></i> vs start of period</span>
            </div>
            <div class="analysis-item">
                <span class="label">Performance Delta</span>
                <span class="value">$${analysis.avg.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                <span class="subtext">Avg Daily Contribution</span>
            </div>
            <div class="analysis-item highlight">
                <span class="label">Predictive Insight</span>
                <p class="text-xs text-secondary m-0">
                    The ${analysis.trend > 0 ? 'upward' : 'downward'} trajectory suggests a ${Math.abs(analysis.trend)}% shift in capital velocity. 
                    <b>Peak detected</b> on ${new Date(analysis.peak.date).toLocaleDateString()} indicates a high-conversion anomaly.
                </p>
            </div>
        </div>
    `;
    lucide.createIcons();
}


async function loadDashboardKPIs() {
    try {
        const strategic = await fetchApi('/analytics/strategic');
        const container = document.getElementById('dashboard-kpi-container');
        if (!container) return;

        const cards = [
            renderKPICard({
                label: 'Total Revenue',
                value: `$${strategic.revenue.current.toLocaleString(undefined, {maximumFractionDigits: 0})}`,
                delta: `${strategic.revenue.mom_delta}%`,
                subtext: 'vs last month',
                trend: strategic.revenue.mom_delta >= 0 ? 'up' : 'down',
                interpretation: getInterpretation(strategic.revenue.mom_delta),
                drilldownKey: 'Total Revenue'
            }),
            renderKPICard({
                label: 'Avg Order Value',
                value: `$${(strategic.revenue.current / strategic.active_users.current || 0).toFixed(2)}`,
                delta: `${strategic.revenue.wow_delta}%`,
                subtext: 'vs last week',
                trend: strategic.revenue.wow_delta >= 0 ? 'up' : 'down',
                interpretation: getInterpretation(strategic.revenue.wow_delta),
                drilldownKey: 'Avg Order Value'
            }),
            renderKPICard({
                label: 'Active Clients',
                value: strategic.active_users.current,
                delta: `${strategic.active_users.delta >= 0 ? '+' : ''}${strategic.active_users.delta}`,
                subtext: 'this cycle',
                trend: strategic.active_users.delta >= 0 ? 'up' : 'down',
                interpretation: strategic.active_users.delta >= 0 ? 'Improving' : 'Declining',
                drilldownKey: 'Active Segments'
            }),
            renderKPICard({
                label: 'Customer Retention',
                value: `${strategic.retention.value}%`,
                delta: `${strategic.retention.delta}%`,
                subtext: 'vs benchmark',
                trend: strategic.retention.delta >= 0 ? 'up' : 'down',
                interpretation: getInterpretation(strategic.retention.delta),
                drilldownKey: 'Customer Retention'
            })
        ];

        container.innerHTML = cards.join('');
        lucide.createIcons();
    } catch (e) { console.error(e); }
}


function renderBreakdownCharts(drilldownData) {
    const isDark = document.body.classList.contains('dark-theme');
    const textColor = isDark ? '#f8fafc' : '#0f172a';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';
    
    // 1. Segments Doughnut Chart & Analysis
    if (charts.segments) charts.segments.destroy();
    const segCtx = document.getElementById('segmentsChart');
    const segAnalysisEl = document.getElementById('segments-analysis');
    
    if (segCtx && drilldownData.segments) {
        // --- Analysis Logic ---
        const sortedSegs = [...drilldownData.segments].sort((a,b) => b.revenue - a.revenue);
        const leader = sortedSegs[0];
        const gap = sortedSegs[sortedSegs.length - 1];
        
        if (segAnalysisEl) {
            segAnalysisEl.innerHTML = `
                <div class="analysis-pills-row">
                    <span class="pill-insight pill-leader"><i data-lucide="crown" class="w-2.5 h-2.5"></i> Leader: ${leader.segment}</span>
                    <span class="pill-insight pill-gap"><i data-lucide="alert-circle" class="w-2.5 h-2.5"></i> Gap: ${gap.segment}</span>
                    <span class="pill-insight pill-action"><i data-lucide="zap" class="w-2.5 h-2.5"></i> Target: ${gap.segment} Churn</span>
                </div>
                <div class="analysis-narrative">
                    <b>${leader.segment}</b> maintains dominance, contributing <b>$${leader.revenue.toLocaleString()}</b>. 
                    Critical under-exposure in <b>${gap.segment}</b> ($${gap.revenue.toLocaleString()}) represents a strategic expansion opportunity.
                </div>
            `;
        }

        charts.segments = new Chart(segCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: drilldownData.segments.map(s => s.segment),
                datasets: [{
                    data: drilldownData.segments.map(s => s.revenue),
                    backgroundColor: ['#4f46e5', '#10b981', '#f59e0b', '#3b82f6', '#8b5cf6'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: textColor, font: { family: 'Inter', size: 11 }, boxWidth: 12 }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        padding: 10,
                        callbacks: {
                            label: function(context) {
                                const rev = context.raw || 0;
                                return ' $' + rev.toLocaleString(undefined, {minimumFractionDigits: 0});
                            }
                        }
                    }
                }
            }
        });
    }

    // 2. Top Products Horizontal Bar Chart & Analysis
    if (charts.products) charts.products.destroy();
    const prodCtx = document.getElementById('topProductsChart');
    const prodAnalysisEl = document.getElementById('products-analysis');
    
    if (prodCtx && drilldownData.top_products) {
        // --- Analysis Logic ---
        const sortedProds = [...drilldownData.top_products].sort((a,b) => b.revenue - a.revenue);
        const alpha = sortedProds[0];
        const laggard = sortedProds[sortedProds.length - 1];
        
        if (prodAnalysisEl) {
            prodAnalysisEl.innerHTML = `
                <div class="analysis-pills-row">
                    <span class="pill-insight pill-leader"><i data-lucide="star" class="w-2.5 h-2.5"></i> Alpha: ${alpha.name.substring(0, 12)}...</span>
                    <span class="pill-insight pill-gap"><i data-lucide="trending-down" class="w-2.5 h-2.5"></i> Weak: ${laggard.name.substring(0, 12)}...</span>
                    <span class="pill-insight pill-action"><i data-lucide="package" class="w-2.5 h-2.5"></i> Bundle: ${laggard.name.substring(0, 10)}</span>
                </div>
                <div class="analysis-narrative">
                    <b>${alpha.name}</b> is the primary driver at <b>$${alpha.revenue.toLocaleString()}</b>. 
                    <b>${laggard.name}</b> is underperforming relative to Top 5; consider promotional bundling.
                </div>
            `;
        }

        charts.products = new Chart(prodCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: drilldownData.top_products.map(p => p.name.length > 15 ? p.name.substring(0, 15) + '...' : p.name),
                datasets: [{
                    label: 'Revenue',
                    data: drilldownData.top_products.map(p => p.revenue),
                    backgroundColor: '#10b981',
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        callbacks: {
                            label: function(context) {
                                const units = drilldownData.top_products[context.dataIndex].units;
                                return ` $${context.raw.toLocaleString()} (${units} units)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            font: { size: 10 },
                            callback: value => '$' + (value >= 1000 ? (value/1000).toFixed(0) + 'k' : value)
                        }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: textColor, font: { family: 'Inter', size: 10 } }
                    }
                }
            }
        });
    }
    lucide.createIcons();
}


function renderRevenueChart(rawData) {
    const ctx = document.getElementById('revenueChart').getContext('2d');
    if (charts.revenue) charts.revenue.destroy();

    const chartData = rawData; // Show more points for full-width
    const movingAverage = calculateMovingAverage(chartData.map(d => d.revenue), 7);

    charts.revenue = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.map(d => d.date),
            datasets: [
                {
                    label: 'Daily Performance ($)',
                    data: chartData.map(d => d.revenue),
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.05)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#6366f1'
                },
                {
                    label: '7D Moving Average',
                    data: movingAverage,
                    borderColor: '#10b981',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.4,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { 
                    display: true, 
                    position: 'top',
                    align: 'end',
                    labels: { color: getThemeColors().text, font: { family: 'Inter', size: 12, weight: '500' }, boxWidth: 12 }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    padding: 12,
                    titleFont: { size: 14, weight: '700' },
                    bodyFont: { size: 13 },
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
                            }
                            return label;
                        }
                    }
                },
                zoom: {
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'x',
                        drag: { enabled: true, backgroundColor: 'rgba(99, 102, 241, 0.1)' }
                    },
                    pan: { enabled: true, mode: 'x' }
                }
            },
            scales: {
                y: { 
                    grid: { color: getThemeColors().grid }, 
                    ticks: { 
                        color: getThemeColors().text,
                        font: { size: 11 },
                        callback: value => '$' + (value >= 1000 ? (value/1000).toFixed(1) + 'k' : value)
                    } 
                },
                x: { 
                    grid: { display: false }, 
                    ticks: { 
                        color: getThemeColors().text,
                        font: { size: 11 },
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 15,
                        callback: function(val, index) {
                            const date = new Date(this.getLabelForValue(val));
                            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                        }
                    } 
                }
            }
        }
    });
}


async function renderSales(container) {
    const activeTab = viewState.sales.activeTab;
    
    // Only render the layout/tabs if it's not already there
    if (!document.getElementById('sales-layout-container')) {
        container.innerHTML = `
            <div id="sales-layout-container">
                <div class="sales-hub-header mb-6">
                    <div class="tabs-bar">
                        <button class="tab-item ${activeTab === 'orders' ? 'active' : ''}" data-tab="orders">
                            <i data-lucide="shopping-cart"></i> Orders
                        </button>
                        <button class="tab-item ${activeTab === 'products' ? 'active' : ''}" data-tab="products">
                            <i data-lucide="package"></i> Products
                        </button>
                        <button class="tab-item ${activeTab === 'users' ? 'active' : ''}" data-tab="users">
                            <i data-lucide="users"></i> Customers
                        </button>
                    </div>
                </div>
                <div id="sales-content-view" class="fade-in">
                    <div class="loading-spinner"><div class="spinner"></div></div>
                </div>
            </div>
        `;

        // Tab Navigation Listeners (Registered only once)
        container.querySelectorAll('.tab-item').forEach(tab => {
            tab.addEventListener('click', async () => {
                const newTab = tab.getAttribute('data-tab');
                if (viewState.sales.activeTab === newTab) return;
                
                // Update UI State Immediately for Snappiness
                container.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                viewState.sales.activeTab = newTab;
                await renderSalesContent();
            });
        });
        lucide.createIcons();
    }

    await renderSalesContent();
}

async function renderSalesContent() {
    const salesContent = document.getElementById('sales-content-view');
    if (!salesContent) return;

    const activeTab = viewState.sales.activeTab;
    
    try {
        if (activeTab === 'orders') {
            const state = viewState.orders;
            const [rawOrders, rawProducts, rawUsers] = await Promise.all([
                fetchApi('/orders/', { 
                    skip: (state.page - 1) * state.limit, 
                    limit: state.limit, 
                    search: state.query,
                    sort_by: state.sortBy,
                    sort_order: state.sortOrder
                }),
                fetchApi('/products/', { limit: 1000 }), // For the dropdown, fetch all
                fetchApi('/users/', { limit: 1000 })
            ]);
            renderSalesOrders(salesContent, rawOrders, rawProducts.items, rawUsers.items);
        } else if (activeTab === 'products') {
            const state = viewState.products;
            const res = await fetchApi('/products/', {
                skip: (state.page - 1) * state.limit,
                limit: state.limit,
                search: state.query,
                sort_by: state.sortBy,
                sort_order: state.sortOrder
            });
            renderSalesProducts(salesContent, res);
        } else if (activeTab === 'users') {
            const state = viewState.users;
            const res = await fetchApi('/users/', {
                skip: (state.page - 1) * state.limit,
                limit: state.limit,
                search: state.query,
                sort_by: state.sortBy,
                sort_order: state.sortOrder
            });
            renderSalesUsers(salesContent, res);
        }
        lucide.createIcons();
    } catch (err) {
        salesContent.innerHTML = `<div class="intel-card intel-error">Sync Failed: ${err.message}</div>`;
    }
}

function renderSalesOrders(container, orderData, products, users) {
    const state = viewState.orders;
    const paginated = orderData.items;
    const totalItems = orderData.total;

    container.innerHTML = `
        <div class="explorer-container">
            <div class="explorer-toolbar">
                <div class="flex items-center gap-4">
                    <h2 class="m-0 text-lg">Orders Ledger</h2>
                    <div class="explorer-filters">
                        <select id="filter-order-status">
                            <option value="">All Statuses</option>
                            <option value="pending" ${state.filters.status === 'pending' ? 'selected' : ''}>Pending</option>
                            <option value="shipped" ${state.filters.status === 'shipped' ? 'selected' : ''}>Shipped</option>
                            <option value="delivered" ${state.filters.status === 'delivered' ? 'selected' : ''}>Delivered</option>
                            <option value="cancelled" ${state.filters.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                        </select>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    ${renderTableControls({ id: 'orders', placeholder: 'search ledger...', query: state.query })}
                    <button class="btn-primary flex items-center gap-2" onclick="document.getElementById('quick-order-panel').classList.toggle('active')">
                        <i data-lucide="plus"></i> New Order
                    </button>
                </div>
            </div>

            <div id="quick-order-panel" class="quick-action-panel">
                <div class="grid-responsive" style="grid-template-columns: repeat(4, 1fr); align-items: flex-end; gap: 20px;">
                    <div class="form-group mb-0">
                        <label>Customer</label>
                        <select id="order-customer" required>
                            <option value="">Select Customer</option>
                            ${users.map(u => `<option value="${u.id}">${u.full_name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group mb-0">
                        <label>Product</label>
                        <select id="order-product">
                            ${products.map(p => `<option value="${p.id}">${p.name} ($${p.price})</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group mb-0">
                        <label>Quantity</label>
                        <input type="number" id="order-qty" min="1" value="1" required>
                    </div>
                    <button type="button" id="submit-quick-order" class="btn-primary">Process Order</button>
                </div>
            </div>

            <div class="explorer-table-wrapper">
                <table class="explorer-table">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="id">Order ID <i data-lucide="chevron-down" class="w-3 h-3 inline"></i></th>
                            <th>Customer</th>
                            <th>Items</th>
                            <th class="sortable" data-sort="total_price">Revenue <i data-lucide="chevron-down" class="w-3 h-3 inline"></i></th>
                            <th class="sortable" data-sort="status">Status</th>
                            <th class="sortable" data-sort="created_at">Date</th>
                            <th class="text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${paginated.length > 0 ? paginated.map(o => `
                            <tr>
                                <td><span class="text-xs font-mono font-bold text-accent">#${o.id}</span></td>
                                <td>
                                    <div class="flex flex-col">
                                        <span class="font-bold">${o.customer ? o.customer.full_name : 'ID: ' + o.customer_id}</span>
                                        <span class="text-xs text-secondary">${o.customer ? o.customer.email : ''}</span>
                                    </div>
                                </td>
                                <td class="text-truncate" title="${formatProductName(o)}">${formatProductName(o)}</td>
                                <td><span class="font-bold text-success">$${o.total_price.toFixed(2)}</span></td>
                                <td><span class="status-badge badge-${getStatusColor(o.status)}">${o.status}</span></td>
                                <td><span class="text-xs text-secondary">${new Date(o.created_at).toLocaleDateString()}</span></td>
                                <td class="text-right">
                                    <button class="btn-icon" title="View details"><i data-lucide="more-horizontal"></i></button>
                                </td>
                            </tr>
                        `).join('') : '<tr><td colspan="7" class="empty-state">No matching orders found</td></tr>'}
                    </tbody>
                </table>
            </div>

            <div class="explorer-footer">
                ${renderPagination(totalItems, state.page, state.limit, 'orders')}
            </div>
        </div>
    `;

    // --- Listeners ---
    const handleSearch = debounce((e) => {
        state.query = e.target.value;
        state.page = 1;
        renderSalesContent();
    }, 300);

    document.getElementById('orders-search').addEventListener('input', handleSearch);
    
    document.getElementById('filter-order-status').addEventListener('change', (e) => {
        state.filters.status = e.target.value;
        state.page = 1;
        renderSalesContent();
    });

    document.getElementById('submit-quick-order').addEventListener('click', async () => {
        const payload = {
            customer_id: Number(document.getElementById('order-customer').value),
            product_id: Number(document.getElementById('order-product').value),
            quantity: Number(document.getElementById('order-qty').value)
        };
        try {
            await postApi('/orders/', payload);
            renderSalesContent();
        } catch (err) { alert(err.message); }
    });

    initTableSort(container, 'orders');
    lucide.createIcons();
}


function renderSalesProducts(container, productData) {
    const state = viewState.products;
    const paginated = productData.items;
    const totalItems = productData.total;

    container.innerHTML = `
        <div class="explorer-container">
            <div class="explorer-toolbar">
                <div class="flex items-center gap-4">
                    <h2 class="m-0 text-lg">Product Catalog</h2>
                    <div class="explorer-filters">
                        <select id="filter-product-cat">
                            <option value="">All Categories</option>
                            <option value="General" ${state.filters.category === 'General' ? 'selected' : ''}>General</option>
                            <option value="Electronics" ${state.filters.category === 'Electronics' ? 'selected' : ''}>Electronics</option>
                            <option value="Apparel" ${state.filters.category === 'Apparel' ? 'selected' : ''}>Apparel</option>
                        </select>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    ${renderTableControls({ id: 'products', placeholder: 'search catalog...', query: state.query })}
                    <button class="btn-primary flex items-center gap-2" onclick="document.getElementById('quick-prod-panel').classList.toggle('active')">
                        <i data-lucide="package-plus"></i> Register Sku
                    </button>
                </div>
            </div>

            <div id="quick-prod-panel" class="quick-action-panel">
                <div class="grid-responsive" style="grid-template-columns: 2fr 1fr 1fr 1fr 100px; align-items: flex-end; gap: 15px;">
                    <div class="form-group mb-0"><label>Name</label><input type="text" id="prod-name" required></div>
                    <div class="form-group mb-0"><label>Price ($)</label><input type="number" step="0.01" id="prod-price" required></div>
                    <div class="form-group mb-0"><label>Stock</label><input type="number" id="prod-stock" required></div>
                    <div class="form-group mb-0"><label>SKU</label><input type="text" id="prod-sku" required></div>
                    <button type="button" id="submit-quick-prod" class="btn-primary">Register</button>
                </div>
            </div>

            <div class="explorer-table-wrapper">
                <table class="explorer-table">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="sku">SKU</th>
                            <th class="sortable" data-sort="name">Product Name</th>
                            <th class="sortable" data-sort="category">Category</th>
                            <th class="sortable" data-sort="price">Unit Price</th>
                            <th class="sortable" data-sort="stock_quantity">Inventory</th>
                            <th class="text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${paginated.length > 0 ? paginated.map(p => `
                            <tr>
                                <td><span class="text-xs font-mono font-bold text-secondary">${p.sku || '#' + p.id}</span></td>
                                <td class="font-bold">${p.name}</td>
                                <td><span class="status-badge" style="background: rgba(255,255,255,0.05); color: var(--text-secondary);">${p.category || 'General'}</span></td>
                                <td><span class="font-mono">$${p.price.toFixed(2)}</span></td>
                                <td>
                                    <span class="status-badge ${p.stock_quantity <= 10 ? 'badge-danger' : 'badge-success'}">
                                        ${p.stock_quantity} units
                                    </span>
                                </td>
                                <td class="text-right">
                                    <button class="btn-icon"><i data-lucide="edit-3"></i></button>
                                </td>
                            </tr>
                        `).join('') : '<tr><td colspan="6" class="empty-state">No matching products found</td></tr>'}
                    </tbody>
                </table>
            </div>

            <div class="explorer-footer">
                ${renderPagination(totalItems, state.page, state.limit, 'products')}
            </div>
        </div>
    `;

    document.getElementById('products-search').addEventListener('input', debounce((e) => {
        state.query = e.target.value;
        state.page = 1;
        renderSalesContent();
    }, 300));

    document.getElementById('filter-product-cat').addEventListener('change', (e) => {
        state.filters.category = e.target.value;
        state.page = 1;
        renderSalesContent();
    });

    document.getElementById('submit-quick-prod').addEventListener('click', async () => {
        const payload = {
            name: document.getElementById('prod-name').value,
            category: "General",
            price: parseFloat(document.getElementById('prod-price').value),
            stock_quantity: parseInt(document.getElementById('prod-stock').value),
            sku: document.getElementById('prod-sku').value
        };
        try {
            await postApi('/products/', payload);
            renderSalesContent();
        } catch (err) { alert(err.message); }
    });

    initTableSort(container, 'products');
    lucide.createIcons();
}


function renderSalesUsers(container, userData) {
    const state = viewState.users;
    const paginated = userData.items;
    const totalItems = userData.total;

    container.innerHTML = `
        <div class="explorer-container">
            <div class="explorer-toolbar">
                <div class="flex items-center gap-4">
                    <h2 class="m-0 text-lg">Client Master Registry</h2>
                    <div class="explorer-filters">
                        <select id="filter-user-segment">
                            <option value="">All Segments</option>
                            <option value="Enterprise" ${state.filters.segment === 'Enterprise' ? 'selected' : ''}>Enterprise</option>
                            <option value="SME" ${state.filters.segment === 'SME' ? 'selected' : ''}>SME</option>
                            <option value="Retail" ${state.filters.segment === 'Retail' ? 'selected' : ''}>Retail</option>
                        </select>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    ${renderTableControls({ id: 'users', placeholder: 'search identity...', query: state.query })}
                    <button class="btn-primary flex items-center gap-2" onclick="document.getElementById('quick-user-panel').classList.toggle('active')">
                        <i data-lucide="user-plus"></i> New Client
                    </button>
                </div>
            </div>

            <div id="quick-user-panel" class="quick-action-panel">
                <div class="grid-responsive" style="grid-template-columns: 2fr 2fr 1fr 100px; align-items: flex-end; gap: 15px;">
                    <div class="form-group mb-0"><label>Full Name</label><input type="text" id="user-name" required></div>
                    <div class="form-group mb-0"><label>Email Address</label><input type="email" id="user-email" required></div>
                    <div class="form-group mb-0"><label>Segment</label><select id="user-segment"><option>Retail</option><option>SME</option><option>Enterprise</option></select></div>
                    <button type="button" id="submit-quick-user" class="btn-primary">Register</button>
                </div>
            </div>

            <div class="explorer-table-wrapper">
                <table class="explorer-table">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="id">Account ID</th>
                            <th class="sortable" data-sort="full_name">Full Name</th>
                            <th class="sortable" data-sort="email">Email</th>
                            <th class="sortable" data-sort="segment">Market Segment</th>
                            <th class="sortable" data-sort="created_at">Onboarding</th>
                            <th class="text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${paginated.length > 0 ? paginated.map(u => `
                            <tr>
                                <td><span class="text-xs font-mono font-bold text-accent">#${u.id}</span></td>
                                <td class="font-bold">${u.full_name}</td>
                                <td><span class="text-secondary">${u.email}</span></td>
                                <td><span class="status-badge badge-accent">${u.segment || 'Retail'}</span></td>
                                <td><span class="text-xs text-secondary">${new Date(u.created_at).toLocaleDateString()}</span></td>
                                <td class="text-right">
                                    <button class="btn-icon"><i data-lucide="settings"></i></button>
                                </td>
                            </tr>
                        `).join('') : '<tr><td colspan="6" class="empty-state">No matching clients found</td></tr>'}
                    </tbody>
                </table>
            </div>

            <div class="explorer-footer">
                ${renderPagination(totalItems, state.page, state.limit, 'users')}
            </div>
        </div>
    `;

    document.getElementById('users-search').addEventListener('input', debounce((e) => {
        state.query = e.target.value;
        state.page = 1;
        renderSalesContent();
    }, 300));

    document.getElementById('filter-user-segment').addEventListener('change', (e) => {
        state.filters.segment = e.target.value;
        state.page = 1;
        renderSalesContent();
    });

    document.getElementById('submit-quick-user').addEventListener('click', async () => {
        const payload = {
            full_name: document.getElementById('user-name').value,
            email: document.getElementById('user-email').value,
            password: "password123", // Default for quick entry
            segment: document.getElementById('user-segment').value
        };
        try {
            await postApi('/users/', payload);
            renderSalesContent();
        } catch (err) { alert(err.message); }
    });

    initTableSort(container, 'users');
    lucide.createIcons();
}


async function renderIntelligence(container) {
    // 1. Initial Shell & Skeletons (Instant Painting)
    container.innerHTML = `
        <div class="kpi-grid" id="kpi-skeleton-container">
            ${Array(4).fill(0).map(() => `<div class="kpi-card skeleton-loading" style="height: 140px;"></div>`).join('')}
        </div>

        <div class="enterprise-layout mb-12">
            <div class="enterprise-main">
                <div class="chart-container" id="forecast-skeleton-container" style="min-height: 500px;">
                    <div class="skeleton-loading" style="height: 100%; width: 100%; border-radius: 12px;"></div>
                </div>
            </div>
            <div class="enterprise-side" id="forecast-insight-container">
                <div class="card pulse-card skeleton-loading" style="height: 200px;"></div>
                <div class="card pulse-card skeleton-loading" style="height: 250px;"></div>
            </div>
        </div>

        <div class="enterprise-layout mb-12" style="grid-template-columns: 340px 1fr;">
             <div class="enterprise-side" id="funnel-insight-container">
                <div class="card pulse-card skeleton-loading" style="height: 300px;"></div>
            </div>
            <div class="enterprise-main">
                <div class="data-table-container" id="funnel-container" style="min-height: 400px; padding: 24px;">
                    <div class="skeleton-loading" style="height: 100%; width: 100%; border-radius: 12px;"></div>
                </div>
            </div>
        </div>

        <div class="data-table-container mt-12 mb-12" id="customer-value-container">
            <div class="skeleton-loading" style="height: 450px; width: 100%; border-radius: 12px;"></div>
        </div>

        <div class="data-table-container mt-12 mb-12" id="ai-pulse-container">
            <div class="skeleton-loading" style="height: 250px; width: 100%; border-radius: 12px;"></div>
        </div>

        <div class="data-table-container mt-12 mb-12" id="anomalies-container" style="padding: 24px;">
            <div class="skeleton-loading" style="height: 300px; width: 100%; border-radius: 12px;"></div>
        </div>
    `;

    // 2. Parallel Fire-and-Forget Loading (Non-Blocking)
    loadStrategicKPIs();
    loadForecast();
    loadFulfillmentFunnel();
    loadCustomerValue();
    loadAIPulse();
    loadAnomalies();

    // Attach What-If Simulator listeners are now handled within loadForecast to ensure elements exist

}

// --- Independent Module Loaders ---

async function loadStrategicKPIs() {
    try {
        const strategic = await fetchApi('/analytics/strategic');
        document.getElementById('kpi-skeleton-container').innerHTML = `
            ${renderKPICard({
                label: 'Revenue Growth',
                value: `${strategic.revenue.mom_delta >= 0 ? '+' : ''}${strategic.revenue.mom_delta}%`,
                delta: `WoW: ${strategic.revenue.wow_delta}%`,
                subtext: 'weekly velocity',
                trend: strategic.revenue.mom_delta >= 0 ? 'up' : 'down',
                interpretation: getInterpretation(strategic.revenue.mom_delta),
                drilldownKey: 'Revenue Trends'
            })}
            ${renderKPICard({
                label: 'Returning Customers',
                value: `${strategic.retention.value}%`,
                delta: `${strategic.retention.delta}%`,
                subtext: 'vs benchmark',
                trend: strategic.retention.delta >= 0 ? 'up' : 'down',
                interpretation: getInterpretation(strategic.retention.delta),
                drilldownKey: 'Customer Retention'
            })}
            ${renderKPICard({
                label: 'Lost Customers',
                value: `${strategic.churn.value}%`,
                delta: `${strategic.churn.delta}%`,
                subtext: 'vs average',
                trend: strategic.churn.delta <= 0 ? 'up' : 'down', // Inverted logic: down is good for churn
                interpretation: getInterpretation(strategic.churn.delta, true),
                drilldownKey: 'Churn Rate'
            })}
            ${renderKPICard({
                label: 'Active Customers',
                value: strategic.active_users.current,
                delta: `${strategic.active_users.delta >= 0 ? '+' : ''}${strategic.active_users.delta}`,
                subtext: 'vs last month',
                trend: strategic.active_users.delta >= 0 ? 'up' : 'down',
                interpretation: strategic.active_users.delta >= 0 ? 'Improving' : 'Declining',
                drilldownKey: 'Active Segments'
            })}
        `;

    } catch(e) { console.error(e); }
}

async function loadForecast() {
    try {
        const forecast = await fetchApi('/analytics/ml-revenue-forecast');
        document.getElementById('forecast-skeleton-container').innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <div><h3 class="m-0 text-xl">Advanced Revenue Projections</h3><p class="text-xs text-secondary mt-1">Multi-variate ML Inference Model</p></div>
                <div class="badge badge-success">Confidence: 98.2%</div>
            </div>
            <div style="flex-grow: 1;"><canvas id="forecastChart"></canvas></div>
        `;

        document.getElementById('forecast-insight-container').innerHTML = `
            <div class="card pulse-card" style="border-left: 4px solid var(--accent-color); background: var(--sidebar-bg);">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="m-0">AI Diagnosis</h3>
                    <span class="status-badge badge-accent">Strategic</span>
                </div>
                <p class="text-sm text-secondary" style="line-height: 1.6;">
                    The model predicts a <b>positive 12.4% trajectory</b> over the next cycle. Historical volume correlations suggest that Q3 performance will be driven primarily by high-tier client retention.
                </p>
                <div class="status-badge badge-success mt-4">Growth Signal: Strong</div>
            </div>

            <div class="card pulse-card" style="border-left: 4px solid var(--accent-color); background: var(--sidebar-bg);">
                <h3 class="m-0 mb-4">🎛️ Scenario Simulator</h3>
                <div class="mb-4">
                    <label class="text-xs text-secondary mb-2 block" style="text-transform: uppercase;">Price Adjustment <span id="price-val" class="text-accent" style="float: right;">0%</span></label>
                    <input type="range" id="sim-price" min="-50" max="50" value="0" class="w-full" style="accent-color: var(--accent-color);">
                </div>
                <div class="mb-4">
                    <label class="text-xs text-secondary mb-2 block" style="text-transform: uppercase;">Volume Adjustment <span id="volume-val" class="text-accent" style="float: right;">0%</span></label>
                    <input type="range" id="sim-volume" min="-50" max="50" value="0" class="w-full" style="accent-color: var(--accent-color);">
                </div>
                <div class="status-badge badge-accent w-full text-center" id="whatif-impact" style="padding: 10px;">Net Impact: 0.0%</div>
            </div>
        `;
        if (forecast && forecast.historical_data) renderForecastChart(forecast);
        attachSimulatorListeners();
    } catch(e) { console.error(e); }
}

function attachSimulatorListeners() {
    const simPrice = document.getElementById('sim-price');
    const simVolume = document.getElementById('sim-volume');
    if (simPrice && simVolume) {
        const handleSimulation = debounce(async () => {
            const pVal = parseInt(simPrice.value);
            const vVal = parseInt(simVolume.value);
            
            const priceValEl = document.getElementById('price-val');
            const volumeValEl = document.getElementById('volume-val');
            if (priceValEl) priceValEl.textContent = pVal > 0 ? `+${pVal}%` : `${pVal}%`;
            if (volumeValEl) volumeValEl.textContent = vVal > 0 ? `+${vVal}%` : `${vVal}%`;
            
            const pMult = 1 + (pVal / 100);
            const vMult = 1 + (vVal / 100);
            const netImpact = ((pMult * vMult) - 1) * 100;
            
            const impactEl = document.getElementById('whatif-impact');
            if (impactEl) {
                impactEl.textContent = `Net Impact: ${netImpact > 0 ? '+' : ''}${netImpact.toFixed(1)}%`;
                impactEl.className = `status-badge ${netImpact >= 0 ? 'badge-success' : 'badge-danger'}`;
            }
            
            try {
                const simData = await fetchApi(`/analytics/what-if-forecast?price_mult=${pMult}&volume_mult=${vMult}`);
                if (simData && simData.forecast_data) renderForecastChart(simData);
            } catch (err) { console.error(err); }
        }, 150);
        simPrice.addEventListener('input', handleSimulation);
        simVolume.addEventListener('input', handleSimulation);
    }
}

async function loadFulfillmentFunnel() {
    try {
        const funnelData = await fetchApi('/analytics/fulfillment-funnel');
        document.getElementById('funnel-container').innerHTML = `
            <div class="flex justify-between items-center mb-8">
                <h3 class="m-0">📊 Order Processing Efficiency</h3>
                <span class="status-badge badge-success">Real-time Pipeline</span>
            </div>
            <div class="funnel-container" style="display: flex; flex-direction: column; align-items: center; gap: 0;">
                ${(funnelData.stages || []).map((stage, idx) => `
                    <div class="funnel-stage-wrapper" style="width: 100%; display: flex; flex-direction: column; align-items: center;">
                        <div class="funnel-layer fade-in" style="width: ${100 - (idx * 15)}%; min-width: 300px; background: linear-gradient(90deg, rgba(99, 102, 241, ${0.8 - (idx * 0.15)}), rgba(16, 185, 129, ${0.8 - (idx * 0.15)})); padding: 16px 24px; border-radius: 12px; display: flex; justify-content: space-between;">
                            <div class="flex-stack-gap"><div class="text-xs font-bold" style="text-transform: uppercase; color: rgba(255,255,255,0.7);">${stage.label}</div><div class="text-xl font-bold">${stage.count}</div></div>
                            <div class="text-right flex-stack-gap"><div class="text-xl font-bold text-success">$${stage.revenue.toLocaleString()}</div><div class="text-xs opacity-80">${stage.conversion_top}% Yield</div></div>
                        </div>
                        ${idx < funnelData.stages.length - 1 ? `<div class="funnel-connector" style="height: 32px; width: 2px; background: rgba(255,255,255,0.1); margin: -2px 0;"><div class="status-badge badge-accent" style="font-size: 0.6rem;">-${stage.drop_off}%</div></div>` : ''}
                    </div>
                `).join('')}
            </div>
        `;

        document.getElementById('funnel-insight-container').innerHTML = `
            <div class="card pulse-card" style="border-left: 4px solid var(--success); background: var(--sidebar-bg);">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="m-0">Pipeline Health</h3>
                    <i data-lucide="activity" class="text-success"></i>
                </div>
                <p class="text-sm text-secondary" style="line-height: 1.6; margin-bottom: 20px;">
                    Current throughput is optimal. The most significant drop-off (<b>-${funnelData.stages[1].drop_off}%</b>) occurs at the stage between <b>${funnelData.stages[0].label}</b> and <b>${funnelData.stages[1].label}</b>.
                </p>
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); padding: 12px; border-radius: 8px;">
                     <div class="text-xs text-secondary mb-1">Recommended Action</div>
                     <p class="text-xs font-bold text-success">Monitor fulfillment latency for high-value orders.</p>
                </div>
            </div>
        `;
        lucide.createIcons();
    } catch(e) { console.error(e); }
}

async function loadCustomerValue() {
    try {
        const customerValue = await fetchApi('/analytics/customer-value');
        document.getElementById('customer-value-container').innerHTML = `
            <h3 class="mb-6">💎 Customer Spending Habits</h3>
            <div class="charts-row" style="grid-template-columns: 1fr 400px; gap: 32px;">
                <div class="chart-container" style="background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.05);">
                    <div class="flex justify-between items-center mb-4"><h4 class="m-0 text-secondary text-sm">Revenue Contribution</h4><span class="status-badge badge-accent">LTV</span></div>
                    <div style="height: 300px;"><canvas id="valueSegmentsChart"></canvas></div>
                </div>
                <div><h4 class="mb-4 text-secondary text-sm">Top Revenue Whales</h4>
                    <div class="intel-list flex-stack-gap">
                        ${(customerValue.top_whales || []).map((w, idx) => `
                            <div class="intel-card intel-info fade-in" style="animation-delay: ${idx * 0.1}s">
                                <div class="flex justify-between items-center w-full"><span>${w.name}</span><span class="text-success font-bold">$${w.revenue.toLocaleString()}</span></div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        renderCustomerValueChart(customerValue);
    } catch(e) { console.error(e); }
}

async function loadAIPulse() {
    try {
        const insights = await fetchApi('/analytics/insights');
        let pulseData = [];
        try {
            pulseData = typeof insights.ai_pulse === 'string' ? JSON.parse(insights.ai_pulse) : insights.ai_pulse;
        } catch (e) { console.error("Could not parse AI Pulse JSON", e); }

        const container = document.getElementById('ai-pulse-container');
        container.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h3 class="m-0">💡 AI Smart Advice</h3>
                <span class="status-badge badge-accent">Strategic Feed</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 24px; justify-content: center; align-items: stretch;">
                ${(pulseData || []).map((item, idx) => {
                    const isCritical = item.priority.includes('Critical');
                    const isWarning = item.priority.includes('Warning');
                    const priorityColor = isCritical ? 'var(--danger-color)' : (isWarning ? 'var(--warning-color)' : 'var(--success-color)');
                    const priorityBg = isCritical ? 'badge-danger' : (isWarning ? 'badge-warning' : 'badge-success');
                    
                    return `
                        <div class="entity-card fade-in" style="animation-delay: ${idx * 0.1}s; display: flex; flex-direction: column; height: 100%; border-top: 4px solid ${priorityColor}; padding: 24px;">
                            <div class="flex justify-between items-center mb-4">
                                <span class="status-badge ${priorityBg}" style="font-size: 0.7rem; text-transform: uppercase; padding: 4px 8px; font-weight: 700; letter-spacing: 0.5px;">
                                    ${item.priority}
                                </span>
                                <span class="text-xs font-bold text-accent" style="background: rgba(99, 102, 241, 0.1); padding: 4px 8px; border-radius: 4px;">${item.metric}</span>
                            </div>
                            <h4 class="mb-3" style="font-size: 1.15rem; line-height: 1.4;">${item.title}</h4>
                            <p class="text-sm text-secondary" style="line-height: 1.6; margin-bottom: 24px; flex-grow: 1;">${item.explanation}</p>
                            
                            <div style="background: rgba(0,0,0,0.15); padding: 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px;">
                                <div class="text-xs text-secondary mb-2" style="text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Recommended Action</div>
                                <div class="text-sm" style="color: var(--accent-color); font-weight: 500; line-height: 1.4;">${item.action}</div>
                            </div>
                            
                            <button class="btn btn-accent w-full" style="padding: 10px; font-size: 0.85rem; font-weight: 600; background: transparent; border: 1px solid var(--accent-color); color: var(--accent-color); transition: all 0.2s;" 
                                    onmouseover="this.style.background='var(--accent-color)'; this.style.color='white'" 
                                    onmouseout="this.style.background='transparent'; this.style.color='var(--accent-color)'"
                                    onclick="window.openChatWithQuestion('Can you give me a detailed deep-dive for: ${item.title.replace(/'/g, "\\'")}?')">
                                Request Deep Dive
                            </button>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        lucide.createIcons();
    } catch(e) { console.error(e); }
}

async function loadAnomalies() {
    try {
        const anomalies = await fetchApi('/analytics/anomalies');
        
        let unifiedAnomalies = [];
        (anomalies.revenue_anomalies || []).forEach(a => unifiedAnomalies.push({ type: 'Revenue', ...a }));
        (anomalies.order_anomalies || []).forEach(a => unifiedAnomalies.push({ type: 'Order', ...a }));
        
        document.getElementById('anomalies-container').innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <div>
                    <h3 class="m-0">🕵️ System Anomaly Ledger</h3>
                    <p class="text-xs text-secondary mt-1">High-Precision outlier detection event log</p>
                </div>
                <span class="status-badge badge-warning">Monitoring Active</span>
            </div>
            
            <table class="dense-table">
                <thead>
                    <tr>
                        <th>Context</th>
                        <th>Event Summary</th>
                        <th>Subject</th>
                        <th>Impact</th>
                        <th>Detection Reason</th>
                    </tr>
                </thead>
                <tbody>
                    ${unifiedAnomalies.length > 0 ? unifiedAnomalies.map(anom => {
                        const isRevenue = anom.type === 'Revenue';
                        const badgeClass = isRevenue ? 'badge-danger' : 'badge-warning';
                        const title = isRevenue ? `$${anom.revenue.toLocaleString()}` : `$${anom.total_price.toLocaleString()}`;
                        const subject = isRevenue ? new Date(anom.date).toLocaleDateString() : `Order #${anom.order_id}`;
                        const tag = isRevenue ? anom.severity : anom.product;

                        return `
                            <tr>
                                <td><span class="status-badge" style="background: rgba(255,255,255,0.05); color: var(--text-color); font-size: 0.65rem;">${anom.type.toUpperCase()}</span></td>
                                <td class="font-bold">${anom.type} Alert</td>
                                <td><span class="text-xs text-secondary">${subject}</span></td>
                                <td><span class="font-bold ${isRevenue ? 'text-danger' : 'text-warning'}">${title}</span> <span class="status-badge ${badgeClass}" style="font-size: 0.6rem; transform: scale(0.9);">${tag}</span></td>
                                <td class="text-sm text-secondary">${anom.reason}</td>
                            </tr>
                        `;
                    }).join('') : '<tr><td colspan="5" class="empty-state">No anomalous activity detected. All systems within standard deviation.</td></tr>'}
                </tbody>
            </table>
        `;
        lucide.createIcons();
    } catch(e) { console.error(e); }
}

function renderForecastChart(data) {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;
    const ctx2d = ctx.getContext('2d');
    
    // Fix: Backend returns objects with .date and .revenue
    const historicalDates = data.historical_data.map(d => d.date);
    const historicalRevenue = data.historical_data.map(d => d.revenue);
    const forecastDates = data.forecast_data.map(d => d.date);
    const forecastRevenue = data.forecast_data.map(d => d.revenue);

    const combinedLabels = [...historicalDates, ...forecastDates];
    const historicalSeries = [...historicalRevenue, ...new Array(forecastDates.length).fill(null)];
    const futureSeries = [...new Array(historicalDates.length).fill(null), ...forecastRevenue];

    if (charts.forecast) charts.forecast.destroy();

    charts.forecast = new Chart(ctx2d, {
        type: 'line',
        data: {
            labels: combinedLabels.map(l => new Date(l).toLocaleDateString()),
            datasets: [
                {
                    label: 'Historical Revenue',
                    data: historicalSeries,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    datalabels: { display: false }
                },
                {
                    label: 'ML Forecast',
                    data: futureSeries,
                    borderColor: '#10b981',
                    borderDash: [5, 5],
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#10b981',
                    datalabels: {
                        display: (ctx) => ctx.dataIndex % 5 === 0,
                        align: 'top',
                        color: '#10b981',
                        font: { weight: 'bold', size: 10 },
                        formatter: (val) => `$${Math.round(val/1000)}k`
                    }
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    bottom: 50,
                    left: 10,
                    right: 10,
                    top: 10
                }
            },
            onClick: (e, elements) => {
                if (elements.length > 0) {
                    const idx = elements[0].index;
                    const date = combinedLabels[idx];
                    const val = (historicalSeries[idx] || futureSeries[idx]);
                    const isForecast = futureSeries[idx] !== null;
                    showDrilldownDetail(date, val, isForecast);
                }
            },
            plugins: {
                legend: { position: 'top', labels: { color: '#94a3b8', font: { family: 'Inter' } } },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleFont: { size: 14 },
                    bodyFont: { size: 13 },
                    callbacks: {
                        label: (ctx) => ` Revenue: $${ctx.raw.toFixed(2)}`
                    }
                },
                zoom: {
                    pan: { enabled: true, mode: 'x', modifierKey: 'shift' },
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'x',
                    }
                },
                datalabels: {
                    display: false
                }
            },
            scales: {
                x: { 
                    grid: { display: false }, 
                    ticks: { 
                        color: '#94a3b8',
                        autoSkip: true,
                        maxTicksLimit: 10,
                        maxRotation: 0,
                        font: { size: 11 },
                        padding: 15
                    } 
                },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

/**
 * Enhanced Drill-down: Injects a detailed analytics layer below the chart
 */
async function showDrilldownDetail(date, value, isForecast) {
    const drilldownEl = document.getElementById('drilldown-display');
    if (!drilldownEl) return;

    drilldownEl.style.display = 'block';
    const cleanDate = new Date(date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    
    drilldownEl.innerHTML = `
        <div class="card pulse-card" style="border-left: 4px solid var(--accent-color); animation: none; background: var(--sidebar-bg); margin-top: 24px;">
            <div class="flex justify-between items-center mb-4">
                <h3 class="m-0">Fetching Deep Dive...</h3>
            </div>
            <div class="loading-spinner"><div class="spinner"></div></div>
        </div>
    `;

    try {
        let qs = isForecast ? "" : `?date=${date}`;
        const drillData = await fetchApi(`/analytics/drilldown${qs}`);
        
        let segmentsHtml = '';
        if (drillData.segments && drillData.segments.length > 0) {
             segmentsHtml = drillData.segments.map(seg => `
                <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); padding: 10px 14px; border-radius: 8px; gap: 12px;">
                    <span class="text-sm truncate-safe">${seg.segment}</span>
                    <span style="font-weight: 700; color: var(--accent-color); white-space: nowrap;">${seg.percentage}%</span>
                </div>
            `).join('');
        } else {
             segmentsHtml = `<div class="text-secondary text-sm">No segmented data available for this timeframe.</div>`;
        }
        
        let productsHtml = '';
        if (drillData.top_products && drillData.top_products.length > 0) {
             productsHtml = drillData.top_products.map(p => `
                <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); padding: 10px 14px; border-radius: 8px; gap: 12px;">
                    <span class="text-sm truncate-safe">${p.name}</span>
                    <span style="font-size: 0.8rem; color: var(--text-color); opacity: 0.8;">${p.units} units</span>
                </div>
            `).join('');
        } else {
             productsHtml = `<div class="text-secondary text-sm">No product data available for this selection.</div>`;
        }

        drilldownEl.innerHTML = `
        <div class="card pulse-card" style="border-left: 4px solid var(--accent-color); animation: none; background: var(--sidebar-bg); margin-top: 24px;">
            <div class="flex justify-between items-center mb-4">
                <h3 class="m-0">Detailed Report: ${cleanDate}</h3>
                <span class="status-badge badge-accent">${isForecast ? 'ML Projection Model' : 'Actual Verified Data'}</span>
            </div>
            <div class="grid-responsive" style="grid-template-columns: repeat(3, 1fr);">
                <div class="flex-stack-gap">
                    <h4 class="text-secondary mb-2 truncate-safe" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;">Revenue Analysis</h4>
                    <div class="kpi-value text-wrap-safe" style="font-size: 2.2rem;">$${value.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
                    <p class="text-xs text-secondary mt-2 text-wrap-safe" style="line-height: 1.5;">
                        ${isForecast ? 'Projection utilizes multi-variant linear regression. Distribution is modeled on 30-day historical averages.' : 'Verified transactional daily data retrieved from the ledger.'}
                    </p>
                </div>
                <div class="flex-stack-gap">
                    <h4 class="text-secondary mb-3 truncate-safe" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;">${isForecast ? 'Projected Distribution' : 'Segment Distribution'}</h4>
                    <div class="flex-stack-gap" style="gap: 8px;">
                        ${segmentsHtml}
                    </div>
                </div>
                 <div class="flex-stack-gap">
                    <h4 class="text-secondary mb-3 truncate-safe" style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;">${isForecast ? 'Projected Hot Products' : 'Hot Products'}</h4>
                    <div class="flex-stack-gap" style="gap: 8px;">
                        ${productsHtml}
                    </div>
                </div>
            </div>
        </div>
        `;
        lucide.createIcons();
    } catch (e) {
        drilldownEl.innerHTML = `<div class="card pulse-card intel-error">Failed to load drill-down: ${e.message}</div>`;
    }
    drilldownEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

window.openKPIDrilldown = async function(kpiName) {
    let modal = document.getElementById('drilldown-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'drilldown-modal';
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6); backdrop-filter: blur(8px);
            z-index: 9999; display: flex; justify-content: center; align-items: center;
        `;
        document.body.appendChild(modal);
    }
    
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="card" style="width: 100%; max-width: 600px; background: var(--sidebar-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 24px; position: relative;">
            <button onclick="document.getElementById('drilldown-modal').style.display='none'" style="position: absolute; top: 16px; right: 16px; background: transparent; border: none; color: var(--text-color); cursor: pointer;"><i data-lucide="x"></i></button>
            <h3 class="m-0 mb-4 flex items-center gap-2"><i data-lucide="activity"></i> KPI Drill-Down: ${kpiName}</h3>
            <div class="loading-spinner"><div class="spinner"></div></div>
        </div>
    `;
    lucide.createIcons();

    try {
        const drillData = await fetchApi('/analytics/drilldown'); // default 30 days
        
        let rows = '';
        if (drillData.top_customers && drillData.top_customers.length > 0) {
             rows = drillData.top_customers.map(c => `
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 12px 0;">
                    <span class="text-sm font-medium">${c.name}</span>
                    <span class="text-accent font-bold">$${c.revenue.toLocaleString()}</span>
                </div>
            `).join('');
        }
        
        modal.innerHTML = `
            <div class="card fade-in" style="width: 100%; max-width: 600px; background: var(--sidebar-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 32px; position: relative; max-height: 85vh; overflow-y: auto;">
                <button onclick="document.getElementById('drilldown-modal').style.display='none'" style="position: absolute; top: 16px; right: 16px; background: rgba(255,255,255,0.1); border-radius: 50%; width: 32px; height: 32px; border: none; color: var(--text-color); cursor: pointer; display: flex; align-items: center; justify-content: center;"><i data-lucide="x" class="w-4 h-4"></i></button>
                <div class="mb-6">
                    <span class="status-badge badge-accent mb-2 flex items-center" style="display: inline-flex; width: fit-content; gap: 4px;"><i data-lucide="clock" class="w-3 h-3"></i> Past 30 Days</span>
                    <h2 class="m-0" style="font-size: 1.8rem;">${kpiName} Analysis</h2>
                    <p class="text-secondary text-sm mt-1">Foundational data structuring this top-line metric.</p>
                </div>
                
                <h4 class="text-secondary mb-3" style="text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">Top Driving Clients</h4>
                <div class="mb-8" style="background: rgba(0,0,0,0.2); padding: 16px; border-radius: 12px;">
                    ${rows || '<div class="text-secondary">No client data found.</div>'}
                </div>
                
                <h4 class="text-secondary mb-3" style="text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">Customer Types</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    ${(drillData.segments || []).map(s => `
                        <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: 12px; border-left: 3px solid var(--accent-color);">
                            <div class="text-xs text-secondary mb-1">${s.segment}</div>
                            <div class="font-bold" style="font-size: 1.2rem;">${s.percentage}%</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        lucide.createIcons();
    } catch (e) {
        modal.innerHTML = `
            <div class="card intel-error" style="width: 100%; max-width: 600px;">
                <button onclick="document.getElementById('drilldown-modal').style.display='none'" style="position: absolute; top: 16px; right: 16px; background: transparent; border: none; color: white; cursor: pointer;"><i data-lucide="x"></i></button>
                Failed to load drill-down layer: ${e.message}
            </div>
        `;
        lucide.createIcons();
    }
}

async function renderWarRoom(container) {
    container.innerHTML = `
        <div class="kpi-grid">
            <div class="kpi-card" style="border-left: 4px solid var(--success);">
                <div class="kpi-label">Node Status</div>
                <div class="flex items-center gap-3">
                    <div class="pulse-dot"></div>
                    <div class="kpi-value text-success" style="font-size: 1.5rem;">PRIMARY_UP</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Cumulative Volume</div>
                <div id="warroom-total" class="kpi-value">...</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Order Velocity</div>
                <div class="flex items-baseline gap-2">
                    <div id="warroom-opm" class="kpi-value text-accent">0</div>
                    <span class="text-xs text-secondary">OPM</span>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Revenue Flow</div>
                <div id="warroom-rpm" class="kpi-value text-success">$0.00</div>
            </div>
        </div>

        <div class="enterprise-layout mb-8">
            <div class="enterprise-main">
                <div class="chart-container">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="m-0">Real-time Transaction Stream</h3>
                        <div class="status-indicator">
                            <span class="status-dot online"></span>
                            <span class="text-xs">Live Socket</span>
                        </div>
                    </div>
                    <canvas id="liveChart"></canvas>
                </div>
            </div>
            <div class="enterprise-side">
                <div class="card pulse-card" style="border-left: 4px solid var(--accent-color); background: var(--sidebar-bg); height: 100%;">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="m-0">Live Diagnosis</h3>
                        <i data-lucide="zap" class="text-accent"></i>
                    </div>
                    <div id="live-diagnosis-text" class="text-sm text-secondary" style="line-height: 1.6; margin-bottom: 20px;">
                        Initializing system heuristics... Monitoring transaction packets for anomalies.
                    </div>
                    <div id="system-health-badge" class="status-badge badge-success w-full text-center">System: Optimal</div>
                </div>
            </div>
        </div>

        <div class="terminal-container">
            <div class="terminal-header">
                <div class="terminal-title">Direct Event Log [v2.4.0]</div>
                <div class="text-xs text-secondary opacity-50">UTF-8 STREAM</div>
            </div>
            <div id="live-activity-feed">
                <div class="terminal-entry">
                    <span class="timestamp">[${new Date().toLocaleTimeString()}]</span>
                    <span class="event">SYSTEM_INIT: Secure data tunnel established.</span>
                    <span class="status success">READY</span>
                </div>
            </div>
        </div>
    `;
    
    lucide.createIcons();
    const ctx = document.getElementById('liveChart').getContext('2d');
    const liveChart = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Price', data: [], borderColor: '#10b981', tension: 0.4, borderWidth: 2, pointRadius: 2 }] },
        options: { 
            animation: false, 
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { 
                y: { 
                    grid: { color: getThemeColors().grid }, 
                    ticks: { 
                        color: getThemeColors().text, 
                        font: { size: 12, weight: '500' },
                        padding: 15
                    } 
                },
                x: { 
                    grid: { display: false },
                    ticks: { 
                        color: getThemeColors().text, 
                        font: { size: 12, weight: '500' }, 
                        padding: 15,
                        autoSkip: true, 
                        maxTicksLimit: 6 
                    } 
                } 
            } 
        }
    });

    let lastTotalCount = null;
    let lastCheckTime = Date.now();
    let opmHistory = [];

    warRoomInterval = setInterval(async () => {
        try {
            const ordersRes = await fetchApi('/orders/', { limit: 50, sort_by: 'created_at', sort_order: 'desc' });
            if (currentView !== 'monitoring') return; 
            
            const orders = ordersRes.items;
            const currentTotal = ordersRes.total;
            const now = Date.now();
            
            const totalEl = document.getElementById('warroom-total');
            if (totalEl) totalEl.textContent = currentTotal;

            const opmEl = document.getElementById('warroom-opm');
            const rpmEl = document.getElementById('warroom-rpm');
            const feedEl = document.getElementById('live-activity-feed');
            
            if (lastTotalCount !== null && currentTotal >= lastTotalCount) {
                const diffOrders = currentTotal - lastTotalCount;
                const timeDiffSec = (now - lastCheckTime) / 1000;
                
                const opm = Math.round((diffOrders / timeDiffSec) * 60);
                
                // Slice the top `diffOrders` from orders to calculate revenue
                const latestOrders = orders.slice(0, diffOrders);
                const diffRevenue = latestOrders.reduce((sum, o) => sum + (o.total_price || 0), 0);
                
                const rpm = (diffRevenue / timeDiffSec) * 60;
                
                if (opmEl) opmEl.textContent = opm;
                if (rpmEl) rpmEl.textContent = '$' + rpm.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
                
                // Diagnostic Update
                const diagText = document.getElementById('live-diagnosis-text');
                const healthBadge = document.getElementById('system-health-badge');
                
                opmHistory.push(opm);
                if (opmHistory.length > 8) opmHistory.shift();
                const avgOpm = opmHistory.reduce((a, b) => a + b, 0) / opmHistory.length;

                if (opm > avgOpm * 2.5 && opm > 5) {
                    if (diagText) diagText.innerHTML = `System detected a <b>significant surge</b> in transaction volume. <br><br>Action: Scale worker nodes if latency exceeds 200ms.`;
                    if (healthBadge) { healthBadge.textContent = 'Status: Traffic Spike'; healthBadge.className = 'status-badge badge-accent w-full text-center'; }
                    
                    if (feedEl) {
                        feedEl.insertAdjacentHTML('afterbegin', `
                            <div class="terminal-entry warning fade-in">
                                <span class="timestamp">[${new Date().toLocaleTimeString()}]</span>
                                <span class="event">NETWORK_ALERT: Abnormal transaction spike (${opm} OPM)</span>
                                <span class="status">SPIKE</span>
                            </div>
                        `);
                    }
                } else if (opm < avgOpm * 0.2 && avgOpm > 5) {
                    if (diagText) diagText.innerHTML = `System detected a <b>critical drop</b> in transaction velocity. <br><br>Action: Verify upstream payment provider status.`;
                    if (healthBadge) { healthBadge.textContent = 'Status: Low Velocity'; healthBadge.className = 'status-badge badge-danger w-full text-center'; }

                     if (feedEl) {
                        feedEl.insertAdjacentHTML('afterbegin', `
                            <div class="terminal-entry error fade-in">
                                <span class="timestamp">[${new Date().toLocaleTimeString()}]</span>
                                <span class="event">FLOW_CRITICAL: Throughput below threshold</span>
                                <span class="status">DROP</span>
                            </div>
                        `);
                    }
                } else {
                    if (diagText) diagText.innerHTML = `Inbound flow is <b>stable at ${opm} OPM</b>. Revenue generation is consistent with historical patterns for this time window.`;
                    if (healthBadge) { healthBadge.textContent = 'System: Optimal'; healthBadge.className = 'status-badge badge-success w-full text-center'; }
                    
                    if (feedEl && Math.random() > 0.7) { // Random heartbeat events
                         feedEl.insertAdjacentHTML('afterbegin', `
                            <div class="terminal-entry success fade-in">
                                <span class="timestamp">[${new Date().toLocaleTimeString()}]</span>
                                <span class="event">TRANSACTION_RECV: Packet verified (OPM: ${opm})</span>
                                <span class="status">OK</span>
                            </div>
                        `);
                    }
                }
                
                if (feedEl && feedEl.children.length > 20) {
                    feedEl.removeChild(feedEl.lastChild);
                }
                lucide.createIcons();
            }
            
            lastTotalCount = currentTotal;
            lastCheckTime = now;
            
            const recent = orders.slice(0, 15).reverse(); // Show top 15 in correct order for line chart
            liveChart.data.labels = recent.map(o => `#${o.id}`);
            liveChart.data.datasets[0].data = recent.map(o => o.total_price);
            liveChart.update();
        } catch (err) {
            console.error('War Room update error:', err);
        }
    }, 1500);
}

// --- Data Visualization Helpers ---
function getThemeColors() {
    const isDark = document.body.classList.contains('dark-theme');
    return {
        text: isDark ? '#f8fafc' : '#0f172a', /* Maximum contrast for axis values */
        grid: isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)',
        accent: isDark ? '#6366f1' : '#4f46e5'
    };
}

function analyzeRevenueTrends(data) {
    if (!data || data.length === 0) return null;
    
    let total = 0;
    let peak = { revenue: 0, date: '' };
    
    data.forEach(d => {
        total += d.revenue;
        if (d.revenue > peak.revenue) {
            peak = { ...d };
        }
    });

    const avg = total / data.length;
    
    // Trend (Last 7 vs First 7)
    const first7 = data.slice(0, 7).reduce((a, b) => a + b.revenue, 0) / 7;
    const last7 = data.slice(-7).reduce((a, b) => a + b.revenue, 0) / 7;
    const trend = first7 > 0 ? ((last7 - first7) / first7) * 100 : 0;

    return {
        total,
        peak,
        avg,
        trend: trend.toFixed(1)
    };
}

function downsampleData(data, maxPoints) {
    if (data.length <= maxPoints) return data;
    
    const factor = Math.ceil(data.length / maxPoints);
    return data.filter((_, i) => i % factor === 0);
}

function calculateMovingAverage(data, window) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
        const start = Math.max(0, i - window + 1);
        const sub = data.slice(start, i + 1);
        const sum = sub.reduce((a, b) => a + b, 0);
        result.push(sum / sub.length);
    }
    return result;
}

function resetChartZoom(chartId) {
    if (charts[chartId]) {
        charts[chartId].resetZoom();
    }
}

// --- AI Chat Logic ---
function initAIChat() {
    const trigger = document.getElementById('ai-trigger');
    const container = document.getElementById('ai-container');
    const closeBtn = document.getElementById('close-chat');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-chat');
    const messagesBody = document.getElementById('chat-messages');

    if (!trigger || !container || !sendBtn || !input) {
        console.error('AI Chat components missing in DOM');
        return;
    }

    trigger.addEventListener('click', () => {
        const isHidden = container.style.display === 'none' || container.style.display === '';
        container.style.display = isHidden ? 'flex' : 'none';
        if (isHidden) input.focus();
    });

    closeBtn.addEventListener('click', () => {
        container.style.display = 'none';
    });

    const sendMessage = async (presetText = null) => {
        const text = presetText || input.value.trim();
        if (!text || sendBtn.disabled) return;

        appendMessage('user', text);
        if (!presetText) input.value = '';
        
        sendBtn.disabled = true;
        const originalContent = sendBtn.innerHTML;
        sendBtn.innerHTML = '<div class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></div>';

        const loaderId = appendLoader();
        try {
            const res = await fetch(`${API_BASE}/analytics/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text })
            });
            
            if (!res.ok) throw new Error(`Server returned ${res.status}`);
            const data = await res.json();
            removeLoader(loaderId);
            appendMessage('assistant', data.answer);
        } catch (error) {
            removeLoader(loaderId);
            appendMessage('assistant', `❌ **Error**: ${error.message}`);
        } finally {
            sendBtn.disabled = false;
            sendBtn.innerHTML = originalContent;
            input.focus();
        }
    };

    window.openChatWithQuestion = (question) => {
        container.style.display = 'flex';
        sendMessage(question);
    };

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

    function formatChatMessage(text) {
        if (!text) return '...';
        
        let lines = text.split('\n');
        let formattedLines = [];
        let inTable = false;
        let tableHeader = null;
        let tableRows = [];

        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();
            
            // Table Detection
            if (line.startsWith('|') && line.endsWith('|')) {
                let cells = line.split('|').map(c => c.trim()).filter(c => c !== '');
                
                // Detection for header separator (e.g. |---|---|)
                if (line.includes('---')) {
                    continue; 
                }

                if (!inTable) {
                    inTable = true;
                    tableHeader = cells;
                } else {
                    tableRows.push(cells);
                }
                continue;
            }

            // If we were in a table but this line is not table data, close it
            if (inTable) {
                formattedLines.push(renderChatTable(tableHeader, tableRows));
                inTable = false;
                tableHeader = null;
                tableRows = [];
            }

            // Normal line processing
            let formattedLine = line
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            
            formattedLines.push(formattedLine);
        }

        // Final table close if text ended with a table
        if (inTable) {
            formattedLines.push(renderChatTable(tableHeader, tableRows));
        }

        return formattedLines.filter(l => l !== '').join('<br>');
    }

    function renderChatTable(header, rows) {
        let html = '<div class="chat-table-wrapper"><table><thead><tr>';
        header.forEach(h => html += `<th>${h}</th>`);
        html += '</tr></thead><tbody>';
        rows.forEach(row => {
            html += '<tr>';
            row.forEach(cell => html += `<td>${cell}</td>`);
            html += '</tr>';
        });
        html += '</tbody></table></div>';
        return html;
    }

    function appendMessage(role, text) {
        if (!messagesBody) return;
        const div = document.createElement('div');
        div.className = `message ${role}`;
        
        div.innerHTML = formatChatMessage(text);
        messagesBody.appendChild(div);
        
        requestAnimationFrame(() => {
            messagesBody.scrollTop = messagesBody.scrollHeight;
        });
    }

    function appendLoader() {
        if (!messagesBody) return;
        const id = 'loader-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'message assistant loader-message';
        div.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; border-width: 2px;"></div>';
        messagesBody.appendChild(div);
        messagesBody.scrollTop = messagesBody.scrollHeight;
        return id;
    }

    function removeLoader(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
}

function renderCustomerValueChart(data) {
    const isDark = document.body.classList.contains('dark-theme');
    const textColor = isDark ? '#f8fafc' : '#0f172a';
    
    if (charts.customerValue) charts.customerValue.destroy();
    const ctx = document.getElementById('valueSegmentsChart');
    if (!ctx || !data.segments) return;

    charts.customerValue = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: data.segments.map(s => s.label),
            datasets: [{
                data: data.segments.map(s => s.revenue),
                backgroundColor: ['#10b981', '#6366f1', '#f59e0b'],
                borderWidth: 0,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: textColor, font: { family: 'Inter', size: 11 }, padding: 20 }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12,
                    callbacks: {
                        label: function(ctx) {
                            const rev = ctx.raw || 0;
                            const perc = data.segments[ctx.dataIndex].percentage;
                            return ` Revenue: $${rev.toLocaleString()} (${perc}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderPulseInsights(rawJson) {
    if (!rawJson) return '<div class="loading-pulse">Analyzing business performance...</div>';
    
    try {
        // Clean markdown blocks if AI included them
        const cleanJson = rawJson.replace(/```json\n?|\n?```/g, '').trim();
        const insights = JSON.parse(cleanJson);
        
        if (!Array.isArray(insights)) return '<div class="loading-pulse">Insights currently being recalibrated...</div>';
        
        return insights.map(i => {
            const priorityClass = `priority-${(i.priority || 'Opportunity').toLowerCase()}`;
            let icon = 'trending-up';
            if (i.priority === 'Critical') icon = 'alert-octagon';
            if (i.priority === 'Warning') icon = 'alert-triangle';
            
            return `
                <div class="insight-card ${priorityClass}">
                    <div class="insight-header">
                        <span class="insight-priority">${i.priority}</span>
                        <i data-lucide="${icon}" class="w-4 h-4"></i>
                    </div>
                    <div class="insight-title">${i.title}</div>
                    <div class="insight-explanation">${i.explanation}</div>
                    <div class="insight-metric-box">
                        <span class="insight-metric-label">Key Metric</span>
                        <span class="insight-metric-value">${i.metric}</span>
                    </div>
                    <div class="insight-action-bar">
                        <i data-lucide="zap"></i>
                        <span>Action: ${i.action}</span>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error("Pulse JSON Parse Error:", e, rawJson);
        return '<div class="loading-pulse text-danger">Insight stream momentarily interrupted. Re-establishing link...</div>';
    }
}

function formatProductName(order) {
    if (order.product && order.product.name) {
        return order.product.name;
    }
    
    // Log for debugging as requested
    console.warn(`[DATA ERROR] Missing product metadata for Order #${order.id}. (Product ID: ${order.product_id})`);
    
    // Fallback UI
    return `<span class="text-danger">Product Data Missing (#${order.product_id})</span>`;
}

// --- Utils ---
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function fetchApi(endpoint, params = {}) {
    const url = new URL(`${window.location.origin}${API_BASE}${endpoint}`);
    
    // 1. Merge global and tab-specific filters
    const global = viewState.globalFilters;
    const finalParams = { ...params };
    
    if (global.startDate) finalParams.start_date = global.startDate;
    if (global.endDate) finalParams.end_date = global.endDate;
    
    // Tab filters
    if (endpoint.includes('/orders')) {
        if (viewState.orders.filters.status) finalParams.search = viewState.orders.filters.status;
    }
    if (endpoint.includes('/products')) {
        if (viewState.products.filters.category) finalParams.category = viewState.products.filters.category;
    }
    if (endpoint.includes('/users')) {
        if (viewState.users.filters.segment) finalParams.segment = viewState.users.filters.segment;
    }

    // 2. Append all params to URL
    Object.keys(finalParams).forEach(key => {
        if (finalParams[key] !== undefined && finalParams[key] !== null && finalParams[key] !== '') {
            url.searchParams.append(key, finalParams[key]);
        }
    });

    
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return await res.json();
}

async function postApi(endpoint, payload) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `API Error: ${res.status}`);
    }
    return await res.json();
}

function getStatusColor(status) {
    switch (status) {
        case 'delivered': return 'success';
        case 'cancelled': return 'danger';
        case 'pending': return 'warning';
        case 'shipped': return 'accent';
        default: return 'secondary';
    }
}

// --- Filtering & Sorting Core ---
function filterAndSort(data, query, sortBy, sortOrder) {
    let filtered = [...data];

    // 1. Search
    if (query) {
        const q = query.toLowerCase();
        filtered = filtered.filter(item => {
            return Object.values(item).some(val => 
                String(val).toLowerCase().includes(q)
            );
        });
    }

    // 2. Sort
    if (sortBy) {
        filtered.sort((a, b) => {
            let valA = a[sortBy];
            let valB = b[sortBy];

            // Handle numeric strings or dates if necessary
            if (typeof valA === 'string' && !isNaN(valA) && !isNaN(parseFloat(valA))) valA = parseFloat(valA);
            if (typeof valB === 'string' && !isNaN(valB) && !isNaN(parseFloat(valB))) valB = parseFloat(valB);

            if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
            if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
            return 0;
        });
    }

    return filtered;
}

function initTableSort(container, category) {
    container.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const sortBy = th.getAttribute('data-sort');
            const state = viewState[category];
            
            if (state.sortBy === sortBy) {
                state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                state.sortBy = sortBy;
                state.sortOrder = 'desc'; // Default to newest/highest if switching
            }
            
            state.page = 1; // Reset to page 1 on sort
            renderSalesContent();
        });
    });
}

function renderTableControls(config) {
    return `
        <div class="table-header-controls">
            <div class="search-wrapper">
                <i data-lucide="search"></i>
                <input type="text" 
                       class="search-input" 
                       id="${config.id}-search" 
                       placeholder="Search ${config.placeholder}..."
                       value="${config.query || ''}">
            </div>
            <div class="table-actions">
                <!-- Additional actions can go here -->
            </div>
        </div>
    `;
}

function renderPagination(totalItems, currentPage, limit, category) {
    const totalPages = Math.ceil(totalItems / limit) || 1;
    if (totalPages <= 1) return '';

    return `
        <div class="pagination-container">
            <div class="pagination-info">
                Page <strong>${currentPage}</strong> of <strong>${totalPages}</strong>
                <span class="text-xs text-secondary ml-2">(${totalItems} total records)</span>
            </div>
            <div class="pagination-controls">
                <button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage('${category}', 1)">
                    <i data-lucide="chevrons-left"></i>
                </button>
                <button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage('${category}', ${currentPage - 1})">
                    <i data-lucide="chevron-left"></i> Previous
                </button>
                <button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="changePage('${category}', ${currentPage + 1})">
                    Next <i data-lucide="chevron-right"></i>
                </button>
                <button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="changePage('${category}', ${totalPages})">
                    <i data-lucide="chevrons-right"></i>
                </button>
            </div>
        </div>
    `;
}

function changePage(category, newPage) {
    viewState[category].page = newPage;
    renderSalesContent();
}

window.changePage = changePage; // Make accessible to inline onclick

// --- KPI Rendering Helpers ---
function renderKPICard(config) {
    const { label, value, delta, subtext, trend, interpretation, drilldownKey } = config;
    
    const interpretationClass = `interpretation-${interpretation.toLowerCase()}`;
    const trendClass = `trend-${trend.toLowerCase()}`;
    const trendIconLabel = trend === 'up' ? 'trending-up' : (trend === 'down' ? 'trending-down' : 'minus');
    
    return `
        <div class="kpi-card hover-zoom" onclick="openKPIDrilldown('${drilldownKey}')" style="cursor: pointer;">
            <div class="kpi-header">
                <div class="kpi-label truncate-safe">${label}</div>
                <div class="kpi-interpretation ${interpretationClass}">${interpretation}</div>
            </div>
            <div class="kpi-value ${trend === 'up' ? 'text-success' : (trend === 'down' ? 'text-danger' : '')}">${value}</div>
            <div class="kpi-trend-container">
                <div class="kpi-trend ${trendClass}">
                    <i data-lucide="${trendIconLabel}"></i>
                    <span>${delta}</span>
                </div>
                <div class="kpi-comparison">${subtext}</div>
            </div>
        </div>
    `;
}

function getInterpretation(delta, isInverted = false) {
    const val = parseFloat(delta);
    if (isNaN(val)) return 'Stable';
    if (val > 5) return isInverted ? 'Critical' : 'Improving';
    if (val < -5) return isInverted ? 'Improving' : 'Declining';
    return 'Stable';
}


// --- Theme Management ---
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark-theme';
    document.body.className = savedTheme;
    updateThemeIcon(savedTheme);

    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTheme);
    }
}

function toggleTheme() {
    const body = document.body;
    const newTheme = body.classList.contains('dark-theme') ? 'light-theme' : 'dark-theme';
    
    body.className = newTheme;
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
    
    // Refresh charts to update their colors for the new theme
    if (currentView === 'dashboard') loadView('dashboard');
    if (currentView === 'sales') loadView('sales');
    if (currentView === 'analytics' || currentView === 'monitoring') loadView(currentView);
}

function updateThemeIcon(theme) {
    const iconBase = document.getElementById('theme-icon');
    if (!iconBase) return;
    
    // Explicitly set the icon based on the current theme
    const newIconName = theme === 'dark-theme' ? 'sun' : 'moon';
    iconBase.setAttribute('data-lucide', newIconName);
    
    // Ensure Lucide actually replaces the element
    lucide.createIcons();
}

function debounce(func, wait) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}
