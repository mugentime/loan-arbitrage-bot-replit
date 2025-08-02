import os
from typing import Optional

class Config:
    """Configuration management for the arbitrage bot"""
    
    def __init__(self):
        self.binance_api_key = os.getenv("BINANCE_API_KEY")
        self.binance_api_secret = os.getenv("BINANCE_API_SECRET")
        self.use_testnet = os.getenv("USE_TESTNET", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.auto_start_bot = os.getenv("AUTO_START_BOT", "false").lower() == "true"
        self.skip_startup_connection = os.getenv("SKIP_STARTUP_CONNECTION", "false").lower() == "true"
        self.skip_api_setup = os.getenv("SKIP_API_SETUP", "false").lower() == "true"
        self.auto_load_config = os.getenv("AUTO_LOAD_CONFIG", "true").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file = os.getenv("LOG_FILE", "arbitrage_bot.log")
        
        # Trading parameters
        self.default_max_ltv = float(os.getenv("DEFAULT_MAX_LTV", "0.75"))
        self.default_min_ltv = float(os.getenv("DEFAULT_MIN_LTV", "0.50"))
        self.default_target_ltv = float(os.getenv("DEFAULT_TARGET_LTV", "0.65"))
        
        # Risk management
        self.margin_call_ltv = float(os.getenv("MARGIN_CALL_LTV", "0.85"))
        self.liquidation_ltv = float(os.getenv("LIQUIDATION_LTV", "0.91"))
        
        # Update intervals
        self.update_interval = int(os.getenv("UPDATE_INTERVAL", "60"))  # seconds
        
    def is_configured(self) -> bool:
        """Check if the bot is properly configured"""
        if self.skip_api_setup:
            return True
        return bool(self.binance_api_key and self.binance_api_secret)
    
    def get_api_credentials(self) -> tuple:
        """Get API credentials"""
        return self.binance_api_key, self.binance_api_secret
    
    def update_credentials(self, api_key: str, api_secret: str):
        """Update API credentials"""
        self.binance_api_key = api_key
        self.binance_api_secret = api_secret

# Global config instance
config = Config()
