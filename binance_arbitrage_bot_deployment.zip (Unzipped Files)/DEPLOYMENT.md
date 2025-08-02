# Railway Deployment Guide

## Why Railway?

Railway is ideal for this Binance arbitrage bot because:
- **Automatic deployments** from GitHub commits
- **Better performance** than development platforms 
- **Professional environment variables** management
- **Custom domains** and SSL certificates
- **Scaling capabilities** for production use
- **No geographic restrictions** (can access Binance API from most regions)

## Step-by-Step Deployment

### 1. Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and create a new repository
2. Name it something like `binance-arbitrage-bot`
3. Make it private (recommended for trading bots)
4. Don't initialize with README (we have our files ready)

### 2. Upload Your Code

```bash
# In your local project directory
git init
git add .
git commit -m "Initial commit: Binance Flexible Loan Arbitrage Bot"
git branch -M main
git remote add origin https://github.com/yourusername/binance-arbitrage-bot.git
git push -u origin main
```

### 3. Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Sign up/login with your GitHub account
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `binance-arbitrage-bot` repository
5. Railway will automatically detect it's a Python app

### 4. Configure Environment Variables

In Railway dashboard, go to Variables tab and add:

```
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_secret_here
USE_TESTNET=false
AUTO_START_BOT=false
SKIP_STARTUP_CONNECTION=false
DEFAULT_MAX_LTV=0.75
DEFAULT_MIN_LTV=0.50
UPDATE_INTERVAL=60
```

### 5. Custom Domain (Optional)

- In Railway dashboard, go to Settings → Domains
- Add your custom domain or use the provided Railway URL

## Files Included for Railway

- `railway.json` - Railway configuration
- `Procfile` - Process definition
- `requirements-deploy.txt` - Python dependencies
- `runtime.txt` - Python version specification
- `.gitignore` - Git ignore patterns

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BINANCE_API_KEY` | Your Binance API key | - | Yes |
| `BINANCE_API_SECRET` | Your Binance API secret | - | Yes |
| `USE_TESTNET` | Use Binance testnet | false | No |
| `AUTO_START_BOT` | Auto-start bot on deploy | false | No |
| `SKIP_STARTUP_CONNECTION` | Skip Binance connection on startup | false | No |
| `DEFAULT_MAX_LTV` | Maximum LTV threshold | 0.75 | No |
| `DEFAULT_MIN_LTV` | Minimum LTV threshold | 0.50 | No |
| `UPDATE_INTERVAL` | Update interval (seconds) | 60 | No |
| `PORT` | Server port | Set by Railway | No |

## Post-Deployment

1. **Test the deployment**: Visit your Railway URL
2. **Check logs**: Monitor Railway logs for any issues
3. **Start the bot**: Use the web interface to input credentials and start
4. **Monitor performance**: Watch the dashboard for arbitrage opportunities

## Advantages Over Replit

✅ **No geographic restrictions** - Access real Binance API  
✅ **Better performance** - Dedicated resources  
✅ **Professional deployment** - Production-ready environment  
✅ **Custom domains** - Professional URLs  
✅ **Automatic scaling** - Handles increased load  
✅ **Persistent storage** - Data survives restarts  
✅ **Environment security** - Proper secrets management  

## Security Best Practices

1. **Never commit API keys** to GitHub
2. **Use Railway environment variables** for all secrets
3. **Enable IP restrictions** on your Binance API key
4. **Monitor API usage** regularly
5. **Use read-only API permissions** when possible
6. **Enable 2FA** on all accounts (GitHub, Railway, Binance)

## Troubleshooting

### Common Issues:

1. **Build fails**: Check `requirements-deploy.txt` matches your dependencies
2. **App won't start**: Verify `Procfile` and ensure `main:app` exists
3. **Environment variables**: Double-check all required variables are set
4. **API errors**: Verify Binance API key permissions and restrictions

### Logs Access:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and view logs
railway login
railway logs
```

## Monitoring & Maintenance

1. **Set up alerts** for failed trades or API errors
2. **Monitor Railway metrics** for performance
3. **Regular dependency updates** for security
4. **Backup trade history** periodically
5. **Review API usage** to stay within limits

Your bot will be much more reliable and performant on Railway compared to development platforms!