// Dashboard JavaScript for Binance Flexible Loan Arbitrage Bot

class ArbitrageDashboard {
    constructor() {
        this.apiBase = '/api';
        this.isConnected = false;
        this.botRunning = false;
        this.refreshInterval = null;
        this.performanceChart = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupRefreshInterval();
        this.loadInitialData();
        this.initializeCharts();
    }
    
    setupEventListeners() {
        // Bot control buttons
        document.getElementById('start-bot').addEventListener('click', () => this.startBot());
        document.getElementById('stop-bot').addEventListener('click', () => this.stopBot());
        document.getElementById('refresh-data').addEventListener('click', () => this.refreshAllData());
        
        // Refresh buttons
        document.getElementById('refresh-positions').addEventListener('click', () => this.loadPositions());
        document.getElementById('refresh-opportunities').addEventListener('click', () => this.loadOpportunities());
        document.getElementById('refresh-history').addEventListener('click', () => this.loadTradeHistory());
        
        // Manual action buttons
        document.getElementById('execute-arbitrage').addEventListener('click', () => this.executeManualArbitrage());
        document.getElementById('execute-rebalance').addEventListener('click', () => this.executeManualRebalance());
        
        // Tab change events
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => this.onTabChange(e.target.getAttribute('href')));
        });
    }
    
    setupRefreshInterval() {
        // Refresh data every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (this.botRunning) {
                this.refreshAllData();
            }
        }, 30000);
    }
    
    async loadInitialData() {
        await this.checkBotStatus();
        await this.loadPositions();
        await this.loadOpportunities();
        await this.loadTradeHistory();
    }
    
    async apiRequest(endpoint, method = 'GET', data = null) {
        try {
            const config = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (data) {
                config.body = JSON.stringify(data);
            }
            
            const response = await fetch(`${this.apiBase}${endpoint}`, config);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}`);
            }
            
            return result;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            this.showAlert('danger', `API Error: ${error.message}`);
            throw error;
        }
    }
    
    async startBot() {
        const apiKey = document.getElementById('api-key').value.trim();
        const apiSecret = document.getElementById('api-secret').value.trim();
        const maxLtv = parseFloat(document.getElementById('max-ltv').value);
        const minLtv = parseFloat(document.getElementById('min-ltv').value);
        const autoRebalance = document.getElementById('auto-rebalance').checked;
        
        if (!apiKey || !apiSecret) {
            this.showAlert('warning', 'Please enter your Binance API credentials');
            return;
        }
        
        if (maxLtv <= minLtv) {
            this.showAlert('warning', 'Max LTV must be greater than Min LTV');
            return;
        }
        
        this.setButtonLoading('start-bot', true);
        
        try {
            const result = await this.apiRequest('/bot/start', 'POST', {
                api_key: apiKey,
                api_secret: apiSecret,
                max_ltv: maxLtv,
                min_ltv: minLtv,
                auto_rebalance: autoRebalance
            });
            
            if (result.success) {
                this.showAlert('success', 'Bot started successfully');
                this.updateBotStatus(true);
                this.refreshAllData();
            }
        } catch (error) {
            // Error already handled in apiRequest
        } finally {
            this.setButtonLoading('start-bot', false);
        }
    }
    
    async stopBot() {
        this.setButtonLoading('stop-bot', true);
        
        try {
            const result = await this.apiRequest('/bot/stop', 'POST');
            
            if (result.success) {
                this.showAlert('info', 'Bot stopped successfully');
                this.updateBotStatus(false);
            }
        } catch (error) {
            // Error already handled in apiRequest
        } finally {
            this.setButtonLoading('stop-bot', false);
        }
    }
    
    async checkBotStatus() {
        try {
            const result = await this.apiRequest('/bot/status');
            this.updateBotStatus(result.running);
            this.updateConnectionStatus(result.connected);
            
            // Update configuration display
            if (result.configuration) {
                document.getElementById('max-ltv').value = result.configuration.max_ltv;
                document.getElementById('min-ltv').value = result.configuration.min_ltv || 0.5;
                document.getElementById('auto-rebalance').checked = result.configuration.auto_rebalance;
            }
        } catch (error) {
            this.updateBotStatus(false);
            this.updateConnectionStatus(false);
        }
    }
    
    async loadPositions() {
        try {
            const result = await this.apiRequest('/flexible-loans/positions');
            this.updatePositionsTable(result.positions || []);
            this.updateStatsCards(result.positions || []);
        } catch (error) {
            this.updatePositionsTable([]);
        }
    }
    
    async loadOpportunities() {
        try {
            const result = await this.apiRequest('/strategy/opportunities');
            this.updateOpportunitiesTable(result.opportunities || []);
        } catch (error) {
            this.updateOpportunitiesTable([]);
        }
    }
    
    async loadTradeHistory() {
        try {
            const result = await this.apiRequest('/strategy/trade-history');
            this.updateTradeHistoryTable(result.trades || []);
        } catch (error) {
            this.updateTradeHistoryTable([]);
        }
    }
    
    async loadStrategyAnalysis() {
        try {
            const result = await this.apiRequest('/strategy/analysis');
            this.updateStrategyAnalysis(result);
            this.updatePerformanceChart(result.performance || {});
        } catch (error) {
            console.error('Failed to load strategy analysis:', error);
        }
    }
    
    updateBotStatus(running) {
        this.botRunning = running;
        
        const startBtn = document.getElementById('start-bot');
        const stopBtn = document.getElementById('stop-bot');
        const statusDot = document.getElementById('status-dot');
        const connectionStatus = document.getElementById('connection-status');
        
        if (running) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusDot.classList.add('connected');
            connectionStatus.textContent = 'Bot Running';
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusDot.classList.remove('connected');
            connectionStatus.textContent = 'Bot Stopped';
        }
    }
    
    updateConnectionStatus(connected) {
        this.isConnected = connected;
        const statusDot = document.getElementById('status-dot');
        const connectionStatus = document.getElementById('connection-status');
        
        if (connected) {
            statusDot.classList.add('connected');
            if (!this.botRunning) {
                connectionStatus.textContent = 'Connected';
            }
        } else {
            statusDot.classList.remove('connected');
            if (!this.botRunning) {
                connectionStatus.textContent = 'Disconnected';
            }
        }
    }
    
    updatePositionsTable(positions) {
        const tbody = document.getElementById('positions-table');
        
        if (positions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted">
                        <i class="fas fa-info-circle me-1"></i>No active positions found
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = positions.map(pos => `
            <tr>
                <td><code>${pos.loan_id}</code></td>
                <td>${pos.loan_coin}/${pos.collateral_coin}</td>
                <td>${this.formatCurrency(pos.total_debt)} ${pos.loan_coin}</td>
                <td>${this.formatCurrency(pos.collateral_amount)} ${pos.collateral_coin}</td>
                <td>${pos.ltv_percentage.toFixed(2)}%</td>
                <td><span class="risk-${pos.risk_level.toLowerCase()}">${pos.risk_level}</span></td>
                <td>${(pos.hourly_rate * 100).toFixed(4)}%</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="dashboard.openRebalanceModal('${pos.loan_id}')">
                        <i class="fas fa-balance-scale"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    updateOpportunitiesTable(opportunities) {
        const tbody = document.getElementById('opportunities-table');
        
        if (opportunities.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted">
                        <i class="fas fa-info-circle me-1"></i>No opportunities found
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = opportunities.map(opp => `
            <tr>
                <td><span class="badge bg-primary">${opp.type}</span></td>
                <td>${opp.from_coin || opp.from_loan_id}</td>
                <td>${opp.to_coin || opp.to_loan_id}</td>
                <td>${(opp.rate_spread * 100).toFixed(4)}%</td>
                <td>${this.formatCurrency(opp.transfer_amount)}</td>
                <td>${this.formatCurrency(opp.expected_profit)}</td>
                <td><span class="badge bg-${opp.confidence === 'HIGH' ? 'success' : 'warning'}">${opp.confidence}</span></td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="dashboard.openArbitrageModal('${opp.from_loan_id}', '${opp.to_loan_id}', ${opp.transfer_amount}, ${opp.expected_profit})">
                        <i class="fas fa-play"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    updateTradeHistoryTable(trades) {
        const tbody = document.getElementById('history-table');
        
        if (trades.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="fas fa-info-circle me-1"></i>No trade history available
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = trades.map(trade => `
            <tr>
                <td><code>${trade.id}</code></td>
                <td><span class="badge bg-info">${trade.type}</span></td>
                <td>${new Date(trade.timestamp).toLocaleString()}</td>
                <td>${this.formatCurrency(trade.amount)}</td>
                <td class="${trade.profit >= 0 ? 'text-success' : 'text-danger'}">
                    ${trade.profit >= 0 ? '+' : ''}${this.formatCurrency(trade.profit)}
                </td>
                <td><span class="badge bg-${trade.status === 'SIMULATED' ? 'warning' : 'success'}">${trade.status}</span></td>
            </tr>
        `).join('');
    }
    
    updateStatsCards(positions) {
        const activePositions = positions.length;
        const totalDebt = positions.reduce((sum, pos) => sum + pos.total_debt, 0);
        const totalCollateral = positions.reduce((sum, pos) => sum + pos.collateral_amount, 0);
        const averageLtv = positions.length > 0 
            ? positions.reduce((sum, pos) => sum + pos.ltv_percentage, 0) / positions.length 
            : 0;
        
        document.getElementById('active-positions').textContent = activePositions;
        document.getElementById('total-debt').textContent = this.formatCurrency(totalDebt);
        document.getElementById('total-collateral').textContent = this.formatCurrency(totalCollateral);
        document.getElementById('average-ltv').textContent = `${averageLtv.toFixed(2)}%`;
    }
    
    updateStrategyAnalysis(analysis) {
        const ltvRecommendations = document.getElementById('ltv-recommendations');
        
        if (analysis.ltv_management && analysis.ltv_management.rebalance_recommendations) {
            const recommendations = analysis.ltv_management.rebalance_recommendations;
            
            if (recommendations.length === 0) {
                ltvRecommendations.innerHTML = '<p class="text-success"><i class="fas fa-check-circle me-1"></i>All positions are optimally balanced</p>';
            } else {
                ltvRecommendations.innerHTML = `
                    <div class="list-group">
                        ${recommendations.map(rec => `
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>${rec.loan_id}</strong><br>
                                        <small class="text-muted">${rec.reason}</small>
                                    </div>
                                    <div class="text-end">
                                        <span class="badge bg-${rec.priority.toLowerCase() === 'critical' ? 'danger' : 'warning'}">${rec.priority}</span><br>
                                        <small>${rec.action} ${this.formatCurrency(rec.amount)}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        }
    }
    
    initializeCharts() {
        const ctx = document.getElementById('performance-chart');
        if (ctx) {
            this.performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Profit/Loss',
                        data: [],
                        borderColor: '#02c076',
                        backgroundColor: 'rgba(2, 192, 118, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }
    
    updatePerformanceChart(performance) {
        if (!this.performanceChart || !performance) return;
        
        // Simple chart update with cumulative profit
        const now = new Date().toLocaleTimeString();
        const labels = this.performanceChart.data.labels;
        const data = this.performanceChart.data.datasets[0].data;
        
        labels.push(now);
        data.push(performance.total_profit || 0);
        
        // Keep only last 20 data points
        if (labels.length > 20) {
            labels.shift();
            data.shift();
        }
        
        this.performanceChart.update();
    }
    
    openArbitrageModal(fromLoanId, toLoanId, amount, expectedProfit) {
        document.getElementById('arb-from-loan-id').value = fromLoanId;
        document.getElementById('arb-to-loan-id').value = toLoanId;
        document.getElementById('arb-from-display').value = fromLoanId;
        document.getElementById('arb-to-display').value = toLoanId;
        document.getElementById('arb-amount').value = amount;
        document.getElementById('arb-expected-profit').value = expectedProfit;
        
        const modal = new bootstrap.Modal(document.getElementById('manual-arbitrage-modal'));
        modal.show();
    }
    
    openRebalanceModal(loanId) {
        document.getElementById('rebal-loan-id').value = loanId;
        document.getElementById('rebal-loan-display').value = loanId;
        
        const modal = new bootstrap.Modal(document.getElementById('manual-rebalance-modal'));
        modal.show();
    }
    
    async executeManualArbitrage() {
        const fromLoanId = document.getElementById('arb-from-loan-id').value;
        const toLoanId = document.getElementById('arb-to-loan-id').value;
        const amount = parseFloat(document.getElementById('arb-amount').value);
        const expectedProfit = parseFloat(document.getElementById('arb-expected-profit').value);
        
        if (!fromLoanId || !toLoanId || !amount) {
            this.showAlert('warning', 'Please fill in all required fields');
            return;
        }
        
        try {
            const result = await this.apiRequest('/strategy/manual-arbitrage', 'POST', {
                from_loan_id: fromLoanId,
                to_loan_id: toLoanId,
                transfer_amount: amount,
                expected_profit: expectedProfit,
                current_spread: 0.02,
                action_type: 'MANUAL'
            });
            
            if (result.success) {
                this.showAlert('success', result.message);
                bootstrap.Modal.getInstance(document.getElementById('manual-arbitrage-modal')).hide();
                this.loadTradeHistory();
            }
        } catch (error) {
            // Error already handled in apiRequest
        }
    }
    
    async executeManualRebalance() {
        const loanId = document.getElementById('rebal-loan-id').value;
        const action = document.getElementById('rebal-action').value;
        const amount = parseFloat(document.getElementById('rebal-amount').value);
        
        if (!loanId || !action || !amount) {
            this.showAlert('warning', 'Please fill in all required fields');
            return;
        }
        
        try {
            const result = await this.apiRequest('/strategy/manual-rebalance', 'POST', {
                loan_id: loanId,
                action: action,
                amount: amount
            });
            
            if (result.success) {
                this.showAlert('success', result.message);
                bootstrap.Modal.getInstance(document.getElementById('manual-rebalance-modal')).hide();
                this.loadPositions();
            }
        } catch (error) {
            // Error already handled in apiRequest
        }
    }
    
    async refreshAllData() {
        await this.checkBotStatus();
        await this.loadPositions();
        await this.loadOpportunities();
        await this.loadTradeHistory();
        
        // Load strategy analysis if on strategy tab
        const activeTab = document.querySelector('.nav-link.active');
        if (activeTab && activeTab.getAttribute('href') === '#strategy') {
            await this.loadStrategyAnalysis();
        }
    }
    
    onTabChange(tabId) {
        switch(tabId) {
            case '#strategy':
                this.loadStrategyAnalysis();
                break;
            case '#opportunities':
                this.loadOpportunities();
                break;
            case '#history':
                this.loadTradeHistory();
                break;
        }
    }
    
    setButtonLoading(buttonId, loading) {
        const button = document.getElementById(buttonId);
        const originalText = button.innerHTML;
        
        if (loading) {
            button.disabled = true;
            button.innerHTML = '<span class="spinner me-1"></span>Loading...';
        } else {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
    
    showAlert(type, message) {
        const alertsContainer = document.getElementById('alerts-container');
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" id="${alertId}" role="alert">
                <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertsContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 5000);
    }
    
    getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            danger: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 8
        }).format(amount);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ArbitrageDashboard();
});
