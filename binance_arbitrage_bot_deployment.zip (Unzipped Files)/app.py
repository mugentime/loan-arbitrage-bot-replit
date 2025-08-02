import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from bot_service import BotService
from api_routes import api_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for API endpoints
CORS(app)

# Initialize bot service
bot_service = BotService()
app.bot_service = bot_service  # Make bot_service available to blueprints

# Register API blueprint
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'bot_status': bot_service.get_status(),
        'timestamp': bot_service.get_current_time()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Binance Flexible Loan Arbitrage Bot Web Interface")
    app.run(host='0.0.0.0', port=5000, debug=True)
