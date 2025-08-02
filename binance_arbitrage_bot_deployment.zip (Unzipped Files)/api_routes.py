from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/bot/start', methods=['POST'])
def start_bot():
    """Start the arbitrage bot"""
    try:
        data = request.get_json() or {}
        
        api_key = data.get('api_key')
        api_secret = data.get('api_secret')
        max_ltv = data.get('max_ltv', 0.75)
        min_ltv = data.get('min_ltv', 0.50)
        auto_rebalance = data.get('auto_rebalance', False)
        
        if not api_key or not api_secret:
            return jsonify({
                'success': False,
                'error': 'API key and secret are required'
            }), 400
        
        bot_service = current_app.bot_service
        success = bot_service.start_bot(
            api_key=api_key,
            api_secret=api_secret,
            max_ltv=max_ltv,
            min_ltv=min_ltv,
            auto_rebalance=auto_rebalance
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Bot started successfully',
                'status': bot_service.get_status()
            })
        else:
            return jsonify({
                'success': False,
                'error': bot_service.error_message or 'Failed to start bot'
            }), 400
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the arbitrage bot"""
    try:
        bot_service = current_app.bot_service
        success = bot_service.stop_bot()
        
        return jsonify({
            'success': success,
            'message': 'Bot stopped successfully' if success else 'Bot was not running',
            'status': bot_service.get_status()
        })
        
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/bot/status', methods=['GET'])
def get_bot_status():
    """Get bot status"""
    try:
        bot_service = current_app.bot_service
        status = bot_service.get_status()
        return jsonify({
            'success': True,
            **status
        })
        
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/flexible-loans/positions', methods=['GET'])
def get_loan_positions():
    """Get current loan positions"""
    try:
        bot_service = current_app.bot_service
        positions = bot_service.get_positions()
        return jsonify({
            'success': True,
            'positions': positions,
            'count': len(positions)
        })
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/flexible-loans/available', methods=['GET'])
def get_available_loans():
    """Get available loan products"""
    try:
        bot_service = current_app.bot_service
        available = bot_service.get_available_loans()
        return jsonify({
            'success': True,
            'available_loans': available,
            'count': len(available)
        })
        
    except Exception as e:
        logger.error(f"Error getting available loans: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/flexible-loans/collaterals', methods=['GET'])
def get_collateral_data():
    """Get collateral data"""
    try:
        bot_service = current_app.bot_service
        positions = bot_service.get_positions()
        collaterals = []
        
        for pos in positions:
            collaterals.append({
                'asset': pos['collateral_coin'],
                'amount': pos['collateral_amount'],
                'value_usd': pos['collateral_amount'],  # Simplified
                'ltv_contribution': pos['ltv_percentage']
            })
        
        return jsonify({
            'success': True,
            'collaterals': collaterals,
            'total_collateral_value': sum(c['value_usd'] for c in collaterals)
        })
        
    except Exception as e:
        logger.error(f"Error getting collateral data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/strategy/analysis', methods=['GET'])
def get_strategy_analysis():
    """Get strategy analysis"""
    try:
        bot_service = current_app.bot_service
        analysis = bot_service.get_strategy_analysis()
        return jsonify({
            'success': True,
            **analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting strategy analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/strategy/execution-status', methods=['GET'])
def get_execution_status():
    """Get strategy execution status"""
    try:
        bot_service = current_app.bot_service
        status = bot_service.get_status()
        return jsonify({
            'success': True,
            'execution_status': 'RUNNING' if status['running'] else 'STOPPED',
            'last_execution': status['last_update'],
            'next_execution': 'In 60 seconds' if status['running'] else 'N/A',
            'auto_rebalance_enabled': status['configuration']['auto_rebalance']
        })
        
    except Exception as e:
        logger.error(f"Error getting execution status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/strategy/trade-history', methods=['GET'])
def get_trade_history():
    """Get trade history"""
    try:
        bot_service = current_app.bot_service
        history = bot_service.get_trade_history()
        return jsonify({
            'success': True,
            'trades': history,
            'count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/strategy/stats', methods=['GET'])
def get_strategy_stats():
    """Get strategy statistics"""
    try:
        bot_service = current_app.bot_service
        analysis = bot_service.get_strategy_analysis()
        return jsonify({
            'success': True,
            'stats': analysis['performance']
        })
        
    except Exception as e:
        logger.error(f"Error getting strategy stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/strategy/opportunities', methods=['GET'])
def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    try:
        bot_service = current_app.bot_service
        analysis = bot_service.get_strategy_analysis()
        return jsonify({
            'success': True,
            'opportunities': analysis['arbitrage_opportunities']['opportunities'],
            'total_opportunities': analysis['arbitrage_opportunities']['total_opportunities'],
            'estimated_profit': analysis['arbitrage_opportunities']['estimated_profit']
        })
        
    except Exception as e:
        logger.error(f"Error getting arbitrage opportunities: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/strategy/manual-arbitrage', methods=['POST'])
def execute_manual_arbitrage():
    """Execute manual arbitrage"""
    try:
        data = request.get_json() or {}
        
        from_loan_id = data.get('from_loan_id')
        to_loan_id = data.get('to_loan_id')
        transfer_amount = data.get('transfer_amount')
        
        if not all([from_loan_id, to_loan_id, transfer_amount]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: from_loan_id, to_loan_id, transfer_amount'
            }), 400
        
        bot_service = current_app.bot_service
        result = bot_service.execute_manual_arbitrage(
            from_loan_id=from_loan_id,
            to_loan_id=to_loan_id,
            transfer_amount=float(transfer_amount),
            expected_profit=data.get('expected_profit', 0)
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error executing manual arbitrage: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/strategy/manual-rebalance', methods=['POST'])
def execute_manual_rebalance():
    """Execute manual rebalance"""
    try:
        data = request.get_json() or {}
        
        loan_id = data.get('loan_id')
        action = data.get('action')
        amount = data.get('amount')
        
        if not all([loan_id, action, amount]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: loan_id, action, amount'
            }), 400
        
        bot_service = current_app.bot_service
        result = bot_service.execute_manual_rebalance(
            loan_id=loan_id,
            action=action,
            amount=float(amount)
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error executing manual rebalance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500