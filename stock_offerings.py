"""
Stock Offerings Module for Finalitics Platform
Analyzes NIFTY 100 stocks and creates basket offerings
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
import requests
from typing import Dict, List, Tuple
import time

class StockAnalyzer:
    """
    Analyzes individual stocks and creates basket offerings
    """
    
    def __init__(self):
        self.nifty100_df = None
        self.stock_data = {}
        self.load_nifty100_list()
        # Cache for stock data to avoid repeated API calls
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour cache
    
    def load_nifty100_list(self):
        """Load NIFTY 100 stock list from CSV"""
        try:
            csv_path = os.path.join(os.path.dirname(__file__), 'ind_nifty100list.csv')
            self.nifty100_df = pd.read_csv(csv_path)
            print(f"✅ Loaded {len(self.nifty100_df)} NIFTY 100 stocks")
        except Exception as e:
            print(f"❌ Error loading NIFTY 100 list: {e}")
            self.nifty100_df = pd.DataFrame()
    
    def get_stock_data(self, symbol: str, period: str = "1y") -> Dict:
        """
        Get stock data from Yahoo Finance with caching
        """
        cache_key = f"{symbol}_{period}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_expiry:
                return cached_data
        
        try:
            # Add .NS suffix for NSE stocks
            yahoo_symbol = f"{symbol}.NS"
            stock = yf.Ticker(yahoo_symbol)
            
            # Get historical data
            hist = stock.history(period=period)
            info = stock.info
            
            if hist.empty:
                return None
            
            # Calculate advanced metrics
            returns = hist['Close'].pct_change().dropna()
            annual_return = self.calculate_annual_return(hist['Close'])
            volatility = self.calculate_volatility(returns)
            pe_ratio = info.get('trailingPE', None)
            market_cap = info.get('marketCap', None)
            
            # Calculate additional metrics
            sharpe_ratio = self.calculate_sharpe_ratio(returns)
            max_drawdown = self.calculate_max_drawdown(hist['Close'])
            beta = self.calculate_beta(returns)
            
            stock_data = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'current_price': float(hist['Close'].iloc[-1]),
                'annual_return': annual_return,
                'volatility': volatility,
                'pe_ratio': pe_ratio,
                'market_cap': market_cap,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'beta': beta,
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'price_to_book': info.get('priceToBook', None),
                'last_updated': datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache[cache_key] = (stock_data, current_time)
            
            return stock_data
            
        except Exception as e:
            print(f"❌ Error getting data for {symbol}: {e}")
            return None
    
    def calculate_annual_return(self, prices: pd.Series) -> float:
        """Calculate annualized return"""
        if len(prices) < 2:
            return 0.0
        
        start_price = prices.iloc[0]
        end_price = prices.iloc[-1]
        days = len(prices)
        
        if start_price <= 0:
            return 0.0
        
        # Calculate CAGR
        annual_return = ((end_price / start_price) ** (252 / days)) - 1
        return annual_return * 100  # Convert to percentage
    
    def calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility"""
        if len(returns) < 2:
            return 0.0
        
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        return volatility * 100  # Convert to percentage
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.06) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        excess_return = returns.mean() * 252 - risk_free_rate
        volatility = returns.std() * np.sqrt(252)
        
        if volatility == 0:
            return 0.0
        
        return excess_return / volatility
    
    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(prices) < 2:
            return 0.0
        
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        return abs(drawdown.min()) * 100  # Convert to percentage
    
    def calculate_beta(self, returns: pd.Series) -> float:
        """Calculate beta (simplified - using market assumption)"""
        if len(returns) < 2:
            return 1.0
        
        # Simplified beta calculation
        # In reality, you'd need market index returns
        market_volatility = 0.20  # Assumed market volatility
        stock_volatility = returns.std() * np.sqrt(252)
        
        return stock_volatility / market_volatility
    
    def analyze_all_stocks(self, max_stocks: int = 60) -> List[Dict]:
        """
        Analyze all NIFTY 100 stocks (limited to max_stocks for performance)
        """
        if self.nifty100_df.empty:
            return []
        
        stocks_analyzed = []
        
        # Take stocks for analysis
        stocks_to_analyze = self.nifty100_df.head(max_stocks)
        
        print(f"📊 Analyzing {len(stocks_to_analyze)} stocks...")
        
        for _, row in stocks_to_analyze.iterrows():
            symbol = row['Symbol']
            print(f"🔍 Analyzing {symbol}...")
            
            stock_data = self.get_stock_data(symbol)
            if stock_data:
                # Add industry from CSV
                stock_data['csv_industry'] = row.get('Industry', 'Unknown')
                stocks_analyzed.append(stock_data)
            
            # Small delay to avoid hitting API limits
            time.sleep(0.1)
        
        print(f"✅ Successfully analyzed {len(stocks_analyzed)} stocks")
        return stocks_analyzed
    
    def create_basket_offerings(self, stocks_data: List[Dict]) -> Dict:
        """
        Create different basket offerings based on stock analysis
        """
        if not stocks_data:
            return {}
        
        # Filter out stocks with missing data
        valid_stocks = [s for s in stocks_data if s.get('annual_return') is not None 
                       and s.get('volatility') is not None and s.get('pe_ratio') is not None]
        
        if not valid_stocks:
            return {}
        
        baskets = {}
        
        # 1. High Growth Momentum (Top performers by return)
        high_growth = sorted(valid_stocks, key=lambda x: x['annual_return'], reverse=True)[:12]
        baskets['High Growth Momentum'] = {
            'description': 'Top performing stocks with exceptional growth potential',
            'strategy': 'Growth-focused portfolio for aggressive investors seeking high returns',
            'risk_level': 'High',
            'min_investment': '₹10,000',
            'stocks': high_growth,
            'avg_return': round(np.mean([s['annual_return'] for s in high_growth]), 2),
            'avg_volatility': round(np.mean([s['volatility'] for s in high_growth]), 2),
            'avg_pe': round(np.mean([s['pe_ratio'] for s in high_growth if s['pe_ratio']]), 2),
            'avg_sharpe': round(np.mean([s['sharpe_ratio'] for s in high_growth if s['sharpe_ratio']]), 2)
        }
        
        # 2. Value Hunters (Low PE stocks with decent returns)
        value_stocks = [s for s in valid_stocks if s['pe_ratio'] and s['pe_ratio'] < 25 and s['annual_return'] > 0]
        value_stocks = sorted(value_stocks, key=lambda x: x['pe_ratio'])[:12]
        baskets['Value Hunters'] = {
            'description': 'Undervalued stocks with attractive valuations and solid fundamentals',
            'strategy': 'Value investing approach for conservative long-term growth',
            'risk_level': 'Medium',
            'min_investment': '₹15,000',
            'stocks': value_stocks,
            'avg_return': round(np.mean([s['annual_return'] for s in value_stocks]), 2),
            'avg_volatility': round(np.mean([s['volatility'] for s in value_stocks]), 2),
            'avg_pe': round(np.mean([s['pe_ratio'] for s in value_stocks]), 2),
            'avg_sharpe': round(np.mean([s['sharpe_ratio'] for s in value_stocks if s['sharpe_ratio']]), 2)
        }
        
        # 3. Balanced Titans (Good risk-adjusted returns)
        balanced_stocks = [s for s in valid_stocks if s['volatility'] < 30 and s['annual_return'] > 5]
        balanced_stocks = sorted(balanced_stocks, key=lambda x: x['sharpe_ratio'] if x['sharpe_ratio'] else 0, reverse=True)[:12]
        baskets['Balanced Titans'] = {
            'description': 'Well-balanced stocks with optimal risk-return profile',
            'strategy': 'Balanced approach for moderate risk tolerance with steady growth',
            'risk_level': 'Medium',
            'min_investment': '₹12,000',
            'stocks': balanced_stocks,
            'avg_return': round(np.mean([s['annual_return'] for s in balanced_stocks]), 2),
            'avg_volatility': round(np.mean([s['volatility'] for s in balanced_stocks]), 2),
            'avg_pe': round(np.mean([s['pe_ratio'] for s in balanced_stocks if s['pe_ratio']]), 2),
            'avg_sharpe': round(np.mean([s['sharpe_ratio'] for s in balanced_stocks if s['sharpe_ratio']]), 2)
        }
        
        # 4. Dividend Aristocrats (Stable, low volatility, dividend-paying stocks)
        dividend_stocks = [s for s in valid_stocks if s['volatility'] < 20 and s['dividend_yield'] > 0]
        dividend_stocks = sorted(dividend_stocks, key=lambda x: x['dividend_yield'], reverse=True)[:12]
        baskets['Dividend Aristocrats'] = {
            'description': 'Stable, dividend-paying stocks for income-focused investors',
            'strategy': 'Conservative approach focusing on regular income and capital preservation',
            'risk_level': 'Low',
            'min_investment': '₹20,000',
            'stocks': dividend_stocks,
            'avg_return': round(np.mean([s['annual_return'] for s in dividend_stocks]), 2),
            'avg_volatility': round(np.mean([s['volatility'] for s in dividend_stocks]), 2),
            'avg_pe': round(np.mean([s['pe_ratio'] for s in dividend_stocks if s['pe_ratio']]), 2),
            'avg_dividend_yield': round(np.mean([s['dividend_yield'] for s in dividend_stocks]), 2)
        }
        
        # 5. Sector Champions (Top stock from each major sector)
        sector_leaders = {}
        for stock in valid_stocks:
            sector = stock.get('csv_industry', 'Unknown')
            if sector != 'Unknown':
                if sector not in sector_leaders or stock['annual_return'] > sector_leaders[sector]['annual_return']:
                    sector_leaders[sector] = stock
        
        baskets['Sector Champions'] = {
            'description': 'Leading stock from each major sector for diversified exposure',
            'strategy': 'Diversified sector representation to minimize sector-specific risks',
            'risk_level': 'Medium',
            'min_investment': '₹25,000',
            'stocks': list(sector_leaders.values())[:15],  # Limit to 15 sectors
            'avg_return': round(np.mean([s['annual_return'] for s in sector_leaders.values()]), 2),
            'avg_volatility': round(np.mean([s['volatility'] for s in sector_leaders.values()]), 2),
            'avg_pe': round(np.mean([s['pe_ratio'] for s in sector_leaders.values() if s['pe_ratio']]), 2),
            'sectors_covered': len(sector_leaders)
        }
        
        # 6. Blue Chip Stability (Large cap, stable stocks)
        blue_chip_stocks = [s for s in valid_stocks if s['market_cap'] and s['market_cap'] > 50000000000]  # 50B+ market cap
        blue_chip_stocks = sorted(blue_chip_stocks, key=lambda x: x['market_cap'], reverse=True)[:12]
        baskets['Blue Chip Stability'] = {
            'description': 'Large-cap stable companies with proven track records',
            'strategy': 'Conservative approach with established market leaders',
            'risk_level': 'Low',
            'min_investment': '₹30,000',
            'stocks': blue_chip_stocks,
            'avg_return': round(np.mean([s['annual_return'] for s in blue_chip_stocks]), 2),
            'avg_volatility': round(np.mean([s['volatility'] for s in blue_chip_stocks]), 2),
            'avg_market_cap': round(np.mean([s['market_cap'] for s in blue_chip_stocks if s['market_cap']]) / 1000000000, 2)
        }
        
        return baskets
    
    def get_stock_offerings(self) -> Dict:
        """
        Main method to get all stock offerings
        """
        print("🚀 Starting comprehensive stock analysis...")
        stocks_data = self.analyze_all_stocks(max_stocks=50)  # Analyze more stocks
        
        if not stocks_data:
            return {
                'error': 'Unable to fetch stock data. Please check your internet connection.',
                'baskets': {},
                'total_stocks_analyzed': 0
            }
        
        baskets = self.create_basket_offerings(stocks_data)
        
        return {
            'baskets': baskets,
            'total_stocks_analyzed': len(stocks_data),
            'last_updated': datetime.now().isoformat(),
            'data_source': 'Yahoo Finance',
            'market_summary': {
                'total_market_cap': sum([s['market_cap'] for s in stocks_data if s['market_cap']]),
                'avg_pe_ratio': np.mean([s['pe_ratio'] for s in stocks_data if s['pe_ratio']]),
                'avg_dividend_yield': np.mean([s['dividend_yield'] for s in stocks_data if s['dividend_yield']]),
                'sectors_analyzed': len(set([s['csv_industry'] for s in stocks_data if s['csv_industry'] != 'Unknown']))
            }
        }
