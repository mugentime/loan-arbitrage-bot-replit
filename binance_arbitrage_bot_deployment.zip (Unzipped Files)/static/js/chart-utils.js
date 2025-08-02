// Chart utilities for Binance Flexible Loan Arbitrage Bot

class ChartUtils {
    static createPerformanceChart(canvasId, data = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Cumulative Profit',
                    data: data.profits || [],
                    borderColor: '#02c076',
                    backgroundColor: 'rgba(2, 192, 118, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Daily Profit',
                    data: data.dailyProfits || [],
                    borderColor: '#f0b90b',
                    backgroundColor: 'rgba(240, 185, 11, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Profit (USD)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#f0b90b',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }
    
    static createLTVDistributionChart(canvasId, positions = []) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        // Group positions by LTV ranges
        const ltvRanges = {
            'Low (0-50%)': 0,
            'Medium (50-70%)': 0,
            'High (70-85%)': 0,
            'Critical (85%+)': 0
        };
        
        positions.forEach(pos => {
            const ltv = pos.ltv_percentage;
            if (ltv < 50) ltvRanges['Low (0-50%)']++;
            else if (ltv < 70) ltvRanges['Medium (50-70%)']++;
            else if (ltv < 85) ltvRanges['High (70-85%)']++;
            else ltvRanges['Critical (85%+)']++;
        });
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(ltvRanges),
                datasets: [{
                    data: Object.values(ltvRanges),
                    backgroundColor: [
                        '#02c076',  // Low - Green
                        '#f0b90b',  // Medium - Yellow
                        '#ff6b35',  // High - Orange
                        '#f84960'   // Critical - Red
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} positions (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    static createArbitrageOpportunitiesChart(canvasId, opportunities = []) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        // Prepare data for scatter plot
        const scatterData = opportunities.map((opp, index) => ({
            x: opp.rate_spread * 100, // Convert to percentage
            y: opp.expected_profit,
            r: Math.sqrt(opp.transfer_amount) / 10, // Size based on amount
            label: `${opp.from_coin} → ${opp.to_coin}`
        }));
        
        return new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Arbitrage Opportunities',
                    data: scatterData,
                    backgroundColor: 'rgba(240, 185, 11, 0.6)',
                    borderColor: '#f0b90b',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Rate Spread (%)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Expected Profit (USD)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return context[0].raw.label;
                            },
                            label: function(context) {
                                const point = context.raw;
                                return [
                                    `Spread: ${point.x.toFixed(4)}%`,
                                    `Profit: $${point.y.toFixed(2)}`,
                                    `Amount: $${(point.r * 10) ** 2}`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }
    
    static createRiskHeatmap(canvasId, positions = []) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        // Create risk matrix data
        const riskData = positions.map(pos => ({
            x: pos.ltv_percentage,
            y: pos.margin_call_buffer,
            v: this.getRiskScore(pos.risk_level),
            label: `${pos.loan_coin}/${pos.collateral_coin}`
        }));
        
        return new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Risk Assessment',
                    data: riskData,
                    backgroundColor: function(context) {
                        const value = context.parsed.v;
                        if (value >= 3) return 'rgba(248, 73, 96, 0.8)';  // Critical - Red
                        if (value >= 2) return 'rgba(255, 107, 53, 0.8)'; // High - Orange
                        if (value >= 1) return 'rgba(252, 213, 53, 0.8)'; // Medium - Yellow
                        return 'rgba(2, 192, 118, 0.8)';                   // Low - Green
                    },
                    borderColor: '#fff',
                    borderWidth: 2,
                    pointRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'LTV (%)'
                        },
                        min: 0,
                        max: 100,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Margin Call Buffer (%)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return context[0].raw.label;
                            },
                            label: function(context) {
                                const point = context.raw;
                                const riskLevel = ChartUtils.getRiskLevelFromScore(point.v);
                                return [
                                    `LTV: ${point.x.toFixed(2)}%`,
                                    `Buffer: ${point.y.toFixed(2)}%`,
                                    `Risk: ${riskLevel}`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }
    
    static getRiskScore(riskLevel) {
        const scores = {
            'LOW': 0,
            'MEDIUM': 1,
            'HIGH': 2,
            'CRITICAL': 3
        };
        return scores[riskLevel] || 0;
    }
    
    static getRiskLevelFromScore(score) {
        const levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
        return levels[score] || 'LOW';
    }
    
    static updateChartData(chart, newData) {
        if (!chart || !newData) return;
        
        chart.data = newData;
        chart.update('none'); // No animation for real-time updates
    }
    
    static addDataPoint(chart, label, dataPoint) {
        if (!chart) return;
        
        chart.data.labels.push(label);
        chart.data.datasets.forEach((dataset, index) => {
            if (Array.isArray(dataPoint)) {
                dataset.data.push(dataPoint[index] || 0);
            } else {
                dataset.data.push(dataPoint);
            }
        });
        
        // Keep only last N points for performance
        const maxPoints = 50;
        if (chart.data.labels.length > maxPoints) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }
        
        chart.update('none');
    }
    
    static createEmptyChart(canvasId, type = 'line', message = 'No data available') {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: type,
            data: {
                labels: [message],
                datasets: [{
                    label: 'No Data',
                    data: [0],
                    backgroundColor: 'rgba(108, 117, 125, 0.1)',
                    borderColor: '#6c757d',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// Export for use in other scripts
window.ChartUtils = ChartUtils;
