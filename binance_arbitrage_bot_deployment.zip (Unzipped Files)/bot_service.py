import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from binance.client import Client
from binance.exceptions import BinanceAPIException
from config import config

logger = logging.getLogger(__name__)

class BotService:
    """Service class to manage the arbitrage bot"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.positions: List[Dict] = []
        self.available_loans: List[Dict] = []
        self.trade_history: List[Dict] = []
        self.last_update: Optional[datetime] = None
        self.error_message: Optional[str] = None
        
        # Bot configuration
        self.max_ltv = config.default_max_ltv
        self.min_ltv = config.default_min_ltv
        self.target_ltv = config.default_target_ltv
        self.auto_rebalance = False
        
        # Statistics
        self.stats = {
            'total_profit': 0.0,
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'average_profit_per_trade': 0.0,
            'start_time': None,
            'uptime': 0
        }
        
        if config.auto_load_config and config.is_configured() and not config.skip_startup_connection:
            try:
                if config.binance_api_key and config.binance_api_secret:
                    self.initialize_client(config.binance_api_key, config.binance_api_secret)
                    if config.auto_start_bot:
                        self.start_bot()
            except Exception as e:
                logger.error(f"Failed to auto-initialize bot: {e}")
    
    def initialize_client(self, api_key: str, api_secret: str) -> bool:
        """Initialize Binance client"""
        try:
            # Try different endpoints to bypass regional restrictions
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret,
                testnet=config.use_testnet,
                requests_params={'timeout': 10}
            )
            
            # Try testnet first if geographic issues
            if not config.use_testnet:
                try:
                    # Test main API
                    account = self.client.get_account()
                    logger.info(f"Successfully connected to Binance - Account: {account.get('accountType')}")
                except Exception as e:
                    if "restricted location" in str(e).lower():
                        logger.warning("Main API restricted, trying testnet...")
                        self.client = Client(
                            api_key=api_key,
                            api_secret=api_secret,
                            testnet=True,
                            requests_params={'timeout': 10}
                        )
                        account = self.client.get_account()
                        logger.info(f"Connected to Binance Testnet - Account: {account.get('accountType')}")
                    else:
                        raise e
            else:
                account = self.client.get_account()
                logger.info(f"Connected to Binance Testnet - Account: {account.get('accountType')}")
            
            # Update config
            config.update_credentials(api_key, api_secret)
            
            self.error_message = None
            return True
            
        except BinanceAPIException as e:
            if "restricted location" in str(e.message).lower():
                # Geographic restriction - switch to demo mode
                self.error_message = f"Geographic restriction detected. Running in demo mode."
                logger.warning(f"Binance API restricted: {e.message}. Switching to demo mode.")
                self._setup_demo_mode()
                return True
            else:
                self.error_message = f"Binance API Error: {e.message}"
                logger.error(self.error_message)
                return False
        except Exception as e:
            self.error_message = f"Connection Error: {str(e)}"
            logger.error(self.error_message)
            return False
    
    def start_bot(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                  max_ltv: Optional[float] = None, min_ltv: Optional[float] = None, 
                  auto_rebalance: bool = False) -> bool:
        """Start the arbitrage bot"""
        if self.running:
            return False
        
        # Initialize client if credentials provided
        if api_key and api_secret:
            if not self.initialize_client(api_key, api_secret):
                return False
        elif not self.client:
            self.error_message = "No API credentials configured"
            return False
        
        # Update bot configuration
        if max_ltv is not None:
            self.max_ltv = max_ltv
        if min_ltv is not None:
            self.min_ltv = min_ltv
        self.auto_rebalance = auto_rebalance
        
        # Start bot thread
        self.running = True
        self.stats['start_time'] = datetime.now()
        self.thread = threading.Thread(target=self._bot_loop, daemon=True)
        self.thread.start()
        
        logger.info("Arbitrage bot started successfully")
        return True
    
    def stop_bot(self) -> bool:
        """Stop the arbitrage bot"""
        if not self.running:
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Arbitrage bot stopped")
        return True
    
    def _bot_loop(self):
        """Main bot loop"""
        while self.running:
            try:
                # Update positions
                self._update_positions()
                
                # Update available loans
                self._update_available_loans()
                
                # Analyze arbitrage opportunities
                opportunities = self._analyze_arbitrage_opportunities()
                
                # Auto-rebalance if enabled
                if self.auto_rebalance:
                    self._auto_rebalance()
                
                # Update statistics
                self._update_stats()
                
                self.last_update = datetime.now()
                
            except Exception as e:
                logger.error(f"Bot loop error: {e}")
                self.error_message = str(e)
            
            # Sleep until next update
            time.sleep(config.update_interval)
    
    def _update_positions(self):
        """Update flexible loan positions"""
        if not self.client:
            return
        
        try:
            # Try the correct method for flexible loans
            try:
                response = self.client.margin_v2_get_loan_flexible_ongoing_orders()
                if response and 'rows' in response:
                    self.positions = self._process_positions(response['rows'])
                else:
                    self.positions = []
            except AttributeError:
                # Fallback method
                response = self.client.get_simple_earn_flexible_product_position()
                if response and 'rows' in response:
                    collateral_positions = [pos for pos in response['rows'] 
                                          if float(pos.get('collateralAmount', 0)) > 0]
                    self.positions = self._process_positions(collateral_positions)
                else:
                    self.positions = []
                    
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            self.positions = []
    
    def _process_positions(self, raw_positions: List[Dict]) -> List[Dict]:
        """Process raw position data"""
        processed = []
        
        for pos in raw_positions:
            try:
                loan_coin = pos.get('loanCoin', pos.get('asset', ''))
                collateral_coin = pos.get('collateralCoin', pos.get('asset', ''))
                total_debt = float(pos.get('totalDebt', pos.get('totalAmount', 0)))
                collateral_amount = float(pos.get('collateralAmount', 0))
                current_ltv = float(pos.get('currentLTV', 0))
                
                # Calculate risk metrics
                ltv_percentage = current_ltv * 100 if current_ltv < 1 else current_ltv
                margin_call_buffer = config.margin_call_ltv * 100 - ltv_percentage
                liquidation_buffer = config.liquidation_ltv * 100 - ltv_percentage
                
                # Determine risk level
                if margin_call_buffer < 3:
                    risk_level = "CRITICAL"
                elif margin_call_buffer < 8:
                    risk_level = "HIGH"
                elif margin_call_buffer < 15:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"
                
                processed_pos = {
                    'loan_id': pos.get('loanId', f"{loan_coin}_{collateral_coin}"),
                    'loan_coin': loan_coin,
                    'collateral_coin': collateral_coin,
                    'total_debt': total_debt,
                    'collateral_amount': collateral_amount,
                    'current_ltv': current_ltv,
                    'ltv_percentage': ltv_percentage,
                    'margin_call_buffer': margin_call_buffer,
                    'liquidation_buffer': liquidation_buffer,
                    'risk_level': risk_level,
                    'hourly_rate': float(pos.get('hourlyInterestRate', 0)),
                    'last_updated': datetime.now().isoformat()
                }
                
                processed.append(processed_pos)
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Error processing position: {e}")
                continue
        
        return processed
    
    def _update_available_loans(self):
        """Update available loan assets"""
        if not self.client:
            return
        
        try:
            # Get flexible loan products
            response = self.client.get_simple_earn_flexible_product_list()
            if response and 'rows' in response:
                self.available_loans = []
                for product in response['rows']:
                    self.available_loans.append({
                        'asset': product.get('asset'),
                        'min_amount': float(product.get('minPurchaseAmount', 0)),
                        'max_amount': float(product.get('maxPurchaseAmount', 0)),
                        'annual_rate': float(product.get('latestAnnualPercentageRate', 0)),
                        'hourly_rate': float(product.get('latestAnnualPercentageRate', 0)) / (365 * 24),
                        'status': product.get('status')
                    })
        except Exception as e:
            logger.error(f"Error updating available loans: {e}")
            self.available_loans = []
    
    def _analyze_arbitrage_opportunities(self) -> List[Dict]:
        """Analyze arbitrage opportunities"""
        opportunities = []
        
        if len(self.positions) < 2:
            return opportunities
        
        # Compare interest rates between positions
        for i, pos1 in enumerate(self.positions):
            for pos2 in self.positions[i+1:]:
                rate1 = pos1.get('hourly_interest', pos1.get('hourly_rate', 0))
                rate2 = pos2.get('hourly_interest', pos2.get('hourly_rate', 0))
                rate_diff = rate2 - rate1
                if abs(rate_diff) > 0.1:  # Minimum profitable spread
                    opportunities.append({
                        'type': 'RATE_ARBITRAGE',
                        'from_loan_id': pos1['loan_id'],
                        'to_loan_id': pos2['loan_id'],
                        'from_coin': pos1['loan_coin'],
                        'to_coin': pos2['loan_coin'],
                        'rate_spread': rate_diff,
                        'transfer_amount': min(pos1.get('loan_amount', 0), pos2.get('collateral_amount', 0)),
                        'expected_profit': rate_diff * min(pos1.get('loan_amount', 0), pos2.get('collateral_amount', 0)) * 24,
                        'confidence': 'HIGH' if abs(rate_diff) > 0.5 else 'MEDIUM'
                    })
        
        return opportunities
    
    def _auto_rebalance(self):
        """Perform automatic rebalancing"""
        for pos in self.positions:
            if pos['risk_level'] == 'CRITICAL':
                logger.warning(f"Critical position detected: {pos['loan_id']} - {pos['ltv_percentage']:.2f}% LTV")
                # In a real implementation, you would execute rebalancing here
    
    def _update_stats(self):
        """Update bot statistics"""
        if self.stats['start_time']:
            self.stats['uptime'] = (datetime.now() - self.stats['start_time']).total_seconds()
        
        if self.stats['total_trades'] > 0:
            self.stats['average_profit_per_trade'] = self.stats['total_profit'] / self.stats['total_trades']
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        return {
            'running': self.running,
            'connected': self.client is not None,
            'error_message': self.error_message,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'positions_count': len(self.positions),
            'configuration': {
                'max_ltv': self.max_ltv,
                'min_ltv': self.min_ltv,
                'auto_rebalance': self.auto_rebalance,
                'use_testnet': config.use_testnet
            }
        }
    
    def get_positions(self) -> List[Dict]:
        """Get current loan positions"""
        return self.positions
    
    def get_available_loans(self) -> List[Dict]:
        """Get available loan products"""
        return self.available_loans
    
    def get_strategy_analysis(self) -> Dict[str, Any]:
        """Get strategy analysis"""
        opportunities = self._analyze_arbitrage_opportunities()
        
        # Generate LTV recommendations
        recommendations = []
        for pos in self.positions:
            if pos['ltv_percentage'] > self.max_ltv * 100:
                recommendations.append({
                    'loan_id': pos['loan_id'],
                    'action': 'REDUCE',
                    'amount': pos['total_debt'] * 0.1,  # Reduce by 10%
                    'reason': 'LTV too high',
                    'priority': pos['risk_level']
                })
            elif pos['ltv_percentage'] < self.min_ltv * 100:
                recommendations.append({
                    'loan_id': pos['loan_id'],
                    'action': 'INCREASE',
                    'amount': pos['collateral_amount'] * 0.1,  # Increase by 10%
                    'reason': 'Can leverage more',
                    'priority': 'LOW'
                })
        
        return {
            'arbitrage_opportunities': {
                'opportunities': opportunities,
                'total_opportunities': len(opportunities),
                'estimated_profit': sum(opp.get('expected_profit', 0) for opp in opportunities)
            },
            'ltv_management': {
                'average_ltv': sum(pos['ltv_percentage'] for pos in self.positions) / len(self.positions) if self.positions else 0,
                'positions_at_risk': len([pos for pos in self.positions if pos['risk_level'] in ['HIGH', 'CRITICAL']]),
                'rebalance_recommendations': recommendations
            },
            'performance': self.stats
        }
    
    def get_trade_history(self) -> List[Dict]:
        """Get trade history"""
        return self.trade_history
    
    def execute_manual_arbitrage(self, from_loan_id: str, to_loan_id: str, 
                                transfer_amount: float, **kwargs) -> Dict[str, Any]:
        """Execute manual arbitrage (simulation)"""
        # In a real implementation, this would execute actual trades
        trade = {
            'id': f"trade_{int(time.time())}",
            'type': 'MANUAL_ARBITRAGE',
            'from_loan_id': from_loan_id,
            'to_loan_id': to_loan_id,
            'amount': transfer_amount,
            'status': 'SIMULATED',  # Would be 'EXECUTED' in real implementation
            'timestamp': datetime.now().isoformat(),
            'profit': kwargs.get('expected_profit', 0),
            'fees': transfer_amount * 0.001  # Simulated fee
        }
        
        self.trade_history.append(trade)
        self.stats['total_trades'] += 1
        self.stats['successful_trades'] += 1
        self.stats['total_profit'] += trade['profit']
        
        return {
            'success': True,
            'trade_id': trade['id'],
            'message': 'Manual arbitrage executed successfully (simulated)',
            'details': trade
        }
    
    def execute_manual_rebalance(self, loan_id: str, action: str, amount: float) -> Dict[str, Any]:
        """Execute manual rebalance (simulation)"""
        # In a real implementation, this would execute actual rebalancing
        rebalance = {
            'id': f"rebalance_{int(time.time())}",
            'loan_id': loan_id,
            'action': action,
            'amount': amount,
            'status': 'SIMULATED',
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'rebalance_id': rebalance['id'],
            'message': f'Manual rebalance executed successfully (simulated): {action} {amount}',
            'details': rebalance
        }
    
    def get_current_time(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()
    
    def _setup_demo_mode(self):
        """Set up demo mode with simulated data"""
        self.client = None  # Set to None to indicate demo mode
        
        # Generate sample data for demo
        self.positions = [
            {
                'loan_id': 'demo_loan_1',
                'collateral_coin': 'BTC',
                'collateral_amount': 0.5,
                'loan_coin': 'USDT',
                'loan_amount': 15000,
                'total_debt': 15000,
                'ltv_percentage': 68.5,
                'interest_rate': 0.0001,
                'hourly_interest': 1.5,
                'risk_level': 'MEDIUM',
                'status': 'ACTIVE'
            },
            {
                'loan_id': 'demo_loan_2',
                'collateral_coin': 'ETH',
                'collateral_amount': 8.0,
                'loan_coin': 'USDT',
                'loan_amount': 12000,
                'total_debt': 12000,
                'ltv_percentage': 72.3,
                'interest_rate': 0.00008,
                'hourly_interest': 0.96,
                'risk_level': 'HIGH',
                'status': 'ACTIVE'
            }
        ]
        
        self.available_loans = [
            {
                'asset': 'USDT',
                'hourly_rate': 0.0001,
                'available_amount': 50000,
                'min_amount': 100,
                'max_amount': 100000
            },
            {
                'asset': 'BUSD',
                'hourly_rate': 0.00009,
                'available_amount': 30000,
                'min_amount': 100,
                'max_amount': 50000
            }
        ]
        
        # Add some sample trade history
        self.trade_history = [
            {
                'id': 'demo_trade_1',
                'type': 'arbitrage',
                'from_loan': 'demo_loan_1',
                'to_loan': 'demo_loan_2',
                'amount': 1000,
                'profit': 15.50,
                'timestamp': (datetime.now()).isoformat(),
                'status': 'COMPLETED'
            }
        ]
        
        # Update stats
        self.stats['total_trades'] = 1
        self.stats['successful_trades'] = 1
        self.stats['total_profit'] = 15.50
        
        logger.info("Demo mode activated with sample data")
