"""
Finalitics Platform by KVAGI
Flask Backend Server for Mutual Fund Portfolio Analysis
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Google Gemini API
google_api_key = os.getenv('GOOGLE_API_KEY')
if google_api_key and google_api_key != 'your_google_gemini_api_key_here':
    genai.configure(api_key=google_api_key)
else:
    print("⚠️  Warning: Google API key not configured. AI analysis will be limited.")
    print("   Please add your API key to the .env file.")

class PortfolioAnalyzer:
    """
    The Quantitative Engine - Handles all mathematical calculations
    """
    
    def __init__(self):
        self.risk_free_rate = 0.06  # 6% risk-free rate (adjust as needed)
        self.benchmark_returns = None  # To be loaded/calculated
    
    def calculate_returns(self, prices):
        """Calculate daily returns from price series"""
        if len(prices) < 2:
            return []
        return [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    
    def calculate_cagr(self, start_value, end_value, periods_years):
        """Calculate Compound Annual Growth Rate"""
        if start_value <= 0 or end_value <= 0 or periods_years <= 0:
            return 0
        return (end_value / start_value) ** (1 / periods_years) - 1
    
    def calculate_volatility(self, returns):
        """Calculate annualized volatility (standard deviation)"""
        if len(returns) < 2:
            return 0
        daily_vol = np.std(returns, ddof=1)
        return daily_vol * np.sqrt(252)  # Annualized (252 trading days)
    
    def calculate_max_drawdown(self, prices):
        """Calculate Maximum Drawdown"""
        if len(prices) < 2:
            return 0
        
        peak = prices[0]
        max_dd = 0
        
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def calculate_sharpe_ratio(self, returns, risk_free_rate=None):
        """Calculate Sharpe Ratio"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) < 2:
            return 0
        
        excess_returns = np.mean(returns) * 252 - risk_free_rate  # Annualized
        volatility = self.calculate_volatility(returns)
        
        if volatility == 0:
            return 0
        
        return excess_returns / volatility
    
    def calculate_beta(self, fund_returns, benchmark_returns):
        """Calculate Beta relative to benchmark"""
        if len(fund_returns) != len(benchmark_returns) or len(fund_returns) < 2:
            return 1.0
        
        covariance = np.cov(fund_returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns, ddof=1)
        
        if benchmark_variance == 0:
            return 1.0
        
        return covariance / benchmark_variance
    
    def calculate_alpha(self, fund_returns, benchmark_returns, beta=None, risk_free_rate=None):
        """Calculate Alpha (Jensen's Alpha)"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if beta is None:
            beta = self.calculate_beta(fund_returns, benchmark_returns)
        
        fund_return = np.mean(fund_returns) * 252  # Annualized
        benchmark_return = np.mean(benchmark_returns) * 252  # Annualized
        
        expected_return = risk_free_rate + beta * (benchmark_return - risk_free_rate)
        return fund_return - expected_return
    
    def calculate_r_squared(self, fund_returns, benchmark_returns):
        """Calculate R-Squared"""
        if len(fund_returns) != len(benchmark_returns) or len(fund_returns) < 2:
            return 0
        
        correlation = np.corrcoef(fund_returns, benchmark_returns)[0][1]
        return correlation ** 2 if not np.isnan(correlation) else 0
    
    def calculate_portfolio_overlap(self, funds_holdings):
        """Calculate portfolio overlap and common holdings"""
        if len(funds_holdings) < 2:
            return {"overlap_percentage": 0, "common_holdings": []}
        
        # Get all holdings from all funds
        all_holdings = {}
        total_funds = len(funds_holdings)
        
        for fund_name, holdings in funds_holdings.items():
            for holding in holdings:
                security_name = holding.get('security_name', '')
                if security_name:
                    if security_name not in all_holdings:
                        all_holdings[security_name] = []
                    all_holdings[security_name].append({
                        'fund': fund_name,
                        'weight': holding.get('weighting', 0)
                    })
        
        # Find common holdings (appear in more than one fund)
        common_holdings = []
        total_overlap_weight = 0
        total_portfolio_weight = 0
        
        for security, fund_holdings in all_holdings.items():
            if len(fund_holdings) > 1:  # Common holding
                avg_weight = sum(h['weight'] for h in fund_holdings) / len(fund_holdings)
                common_holdings.append({
                    'security_name': security,
                    'funds_count': len(fund_holdings),
                    'average_weight': avg_weight,
                    'funds': [h['fund'] for h in fund_holdings]
                })
                total_overlap_weight += avg_weight
        
        # Calculate total portfolio weight for overlap percentage
        for fund_holdings in funds_holdings.values():
            total_portfolio_weight += sum(h.get('weighting', 0) for h in fund_holdings)
        
        # Sort common holdings by frequency and weight
        common_holdings.sort(key=lambda x: (x['funds_count'], x['average_weight']), reverse=True)
        
        # Calculate overlap percentage
        overlap_percentage = (total_overlap_weight / (total_portfolio_weight / total_funds * 100)) if total_portfolio_weight > 0 else 0
        
        return {
            "overlap_percentage": min(overlap_percentage, 100),  # Cap at 100%
            "common_holdings": common_holdings[:10]  # Top 10 common holdings
        }
    
    def analyze_portfolio(self, portfolio_data):
        """
        Main analysis function that processes portfolio data and calculates all metrics
        """
        results = {
            "funds": {},
            "portfolio_analysis": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Sample data for demonstration (replace with actual NAV data)
        # In production, you'd fetch this from your data source
        sample_prices = np.random.exponential(100, 100) * np.random.normal(1.05, 0.1, 100)
        sample_benchmark = np.random.exponential(100, 100) * np.random.normal(1.04, 0.08, 100)
        
        benchmark_returns = self.calculate_returns(sample_benchmark)
        
        # Process each fund
        funds_holdings = {}
        for fund_key, fund_data in portfolio_data.items():
            if isinstance(fund_data, dict) and 'holdingList' in fund_data:
                # Calculate fund metrics using sample data
                fund_returns = self.calculate_returns(sample_prices * np.random.normal(1, 0.1, len(sample_prices)))
                
                # Calculate all metrics
                cagr = self.calculate_cagr(sample_prices[0], sample_prices[-1], len(sample_prices)/252)
                volatility = self.calculate_volatility(fund_returns)
                max_drawdown = self.calculate_max_drawdown(sample_prices)
                sharpe_ratio = self.calculate_sharpe_ratio(fund_returns)
                beta = self.calculate_beta(fund_returns, benchmark_returns)
                alpha = self.calculate_alpha(fund_returns, benchmark_returns, beta)
                r_squared = self.calculate_r_squared(fund_returns, benchmark_returns)
                
                results["funds"][fund_key] = {
                    "fund_id": fund_data.get('fund_id', 'Unknown'),
                    "cagr": round(cagr * 100, 2),
                    "volatility": round(volatility * 100, 2),
                    "max_drawdown": round(max_drawdown * 100, 2),
                    "sharpe_ratio": round(sharpe_ratio, 2),
                    "beta": round(beta, 2),
                    "alpha": round(alpha * 100, 2),
                    "r_squared": round(r_squared * 100, 2),
                    "holdings_count": len(fund_data.get('holdingList', []))
                }
                
                # Store holdings for overlap analysis
                funds_holdings[fund_key] = fund_data.get('holdingList', [])
        
        # Portfolio-level analysis
        portfolio_overlap = self.calculate_portfolio_overlap(funds_holdings)
        results["portfolio_analysis"] = {
            "total_funds": len(results["funds"]),
            "portfolio_overlap": portfolio_overlap
        }
        
        return results

class AIAnalyst:
    """
    The AI Analyst - Interprets quantitative results using LLM
    """
    
    def __init__(self):
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if google_api_key and google_api_key != 'your_google_gemini_api_key_here':
            self.model = genai.GenerativeModel('gemini-pro')
            self.api_configured = True
        else:
            self.model = None
            self.api_configured = False
    
    def generate_analysis_report(self, quantitative_data):
        """
        Generate human-readable analysis using the quantitative data
        """
        
        if not self.api_configured:
            return self.generate_fallback_analysis(quantitative_data)
        
        # Create the bot prompt
        prompt = f"""
Role and Goal:
You are an AI financial analyst. Your task is to interpret a JSON file containing pre-calculated financial metrics for a user's mutual fund portfolio. Your goal is to generate a clear, concise, and easy-to-understand report for an average investor.

Input:
{json.dumps(quantitative_data, indent=2)}

Instructions:

Start with a High-Level Summary:
Begin with a brief, two-sentence overview of the portfolio's main characteristics. Mention one key strength and one primary area for improvement based on the provided data.

Analyze Each Fund Individually:
For each fund in the JSON, create a short paragraph.
- Performance vs. Risk: Explain its return (CAGR) in the context of its risk (Standard Deviation and Maximum Drawdown).
- Risk-Adjusted Return: Explain what its Sharpe Ratio means for an investor. A ratio above 1 is generally good.
- Manager Skill: Explain the fund's Alpha and Beta. A positive Alpha suggests the manager has added value. A Beta greater than 1 suggests higher volatility than the market. Use the R-Squared value to comment on how relevant the Alpha and Beta are (a high R-Squared, >70, makes them more meaningful).

Provide a Portfolio-Wide View:
Look at the portfolio_overlap data in the JSON.
State the overall overlap percentage clearly.
If the overlap is high (e.g., >30%), explain that this reduces the benefits of diversification and means the user is paying multiple fees for the same stocks. List the top overlapping stocks provided.

Conclude with Actionable Recommendations:
Provide a short, numbered list of 2-3 simple, actionable recommendations.
Each recommendation must be directly tied to a weakness identified in your analysis.

Format your response in HTML with proper headings, paragraphs, and lists for web display.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"<p>Error generating AI analysis: {str(e)}</p><p>Please check your API configuration.</p>"
    
    def generate_fallback_analysis(self, quantitative_data):
        """
        Generate a basic analysis when AI is not available
        """
        funds = quantitative_data.get('funds', {})
        portfolio_analysis = quantitative_data.get('portfolio_analysis', {})
        
        html = "<h3>Portfolio Analysis Summary</h3>"
        html += f"<p><strong>Total Funds Analyzed:</strong> {portfolio_analysis.get('total_funds', 0)}</p>"
        
        overlap_data = portfolio_analysis.get('portfolio_overlap', {})
        overlap_pct = overlap_data.get('overlap_percentage', 0)
        html += f"<p><strong>Portfolio Overlap:</strong> {overlap_pct:.1f}%</p>"
        
        if overlap_pct > 30:
            html += "<p>⚠️ <strong>High Overlap Warning:</strong> Your portfolio has significant overlap between funds, which may reduce diversification benefits.</p>"
        
        html += "<h4>Fund Performance Summary</h4>"
        for fund_key, fund_data in funds.items():
            html += f"<div style='margin: 15px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>"
            html += f"<h5>{fund_key.upper()}</h5>"
            html += f"<p><strong>CAGR:</strong> {fund_data.get('cagr', 0)}% | "
            html += f"<strong>Sharpe Ratio:</strong> {fund_data.get('sharpe_ratio', 0)} | "
            html += f"<strong>Volatility:</strong> {fund_data.get('volatility', 0)}%</p>"
            
            sharpe = fund_data.get('sharpe_ratio', 0)
            if sharpe > 1:
                html += "<p>✅ Good risk-adjusted returns</p>"
            elif sharpe > 0.5:
                html += "<p>⚠️ Moderate risk-adjusted returns</p>"
            else:
                html += "<p>❌ Poor risk-adjusted returns</p>"
            html += "</div>"
        
        html += "<h4>Recommendations</h4>"
        html += "<ol>"
        if overlap_pct > 30:
            html += "<li>Consider reducing portfolio overlap by replacing similar funds with those from different sectors or investment styles.</li>"
        
        low_sharpe_funds = [k for k, v in funds.items() if v.get('sharpe_ratio', 0) < 0.5]
        if low_sharpe_funds:
            html += f"<li>Review funds with low Sharpe ratios: {', '.join(low_sharpe_funds)}. Consider alternatives with better risk-adjusted returns.</li>"
        
        html += "<li>Regularly review and rebalance your portfolio to maintain optimal diversification.</li>"
        html += "</ol>"
        
        html += "<p><em>Note: For detailed AI-powered analysis, please configure your Google Gemini API key in the .env file.</em></p>"
        
        return html

# Initialize components
analyzer = PortfolioAnalyzer()
ai_analyst = AIAnalyst()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process portfolio data"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the file based on its type
            if filename.endswith('.json'):
                with open(filepath, 'r') as f:
                    portfolio_data = json.load(f)
            elif filename.endswith('.csv'):
                # Convert CSV to expected format (implement based on your CSV structure)
                df = pd.read_csv(filepath)
                portfolio_data = df.to_dict('records')
            else:
                return jsonify({'error': 'Unsupported file format. Please upload JSON or CSV files.'}), 400
            
            # Analyze the portfolio
            quantitative_results = analyzer.analyze_portfolio(portfolio_data)
            
            # Generate AI analysis
            ai_analysis = ai_analyst.generate_analysis_report(quantitative_results)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'quantitative_data': quantitative_results,
                'ai_analysis': ai_analysis
            })
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/sample-data')
def get_sample_data():
    """Generate sample portfolio data for demonstration"""
    # Create sample portfolio data
    sample_data = {
        "fund_0": {
            "fund_id": "f00000qsdn",
            "holdingList": [
                {"security_name": "Reliance Industries Ltd", "weighting": 8.5, "type": "equity"},
                {"security_name": "HDFC Bank Ltd", "weighting": 7.2, "type": "equity"},
                {"security_name": "Infosys Ltd", "weighting": 6.8, "type": "equity"},
                {"security_name": "TCS Ltd", "weighting": 6.1, "type": "equity"},
                {"security_name": "ITC Ltd", "weighting": 5.9, "type": "equity"}
            ]
        },
        "fund_1": {
            "fund_id": "f00000rsln",
            "holdingList": [
                {"security_name": "HDFC Bank Ltd", "weighting": 9.1, "type": "equity"},
                {"security_name": "ICICI Bank Ltd", "weighting": 7.8, "type": "equity"},
                {"security_name": "Reliance Industries Ltd", "weighting": 7.3, "type": "equity"},
                {"security_name": "Bajaj Finance Ltd", "weighting": 6.5, "type": "equity"},
                {"security_name": "Asian Paints Ltd", "weighting": 5.2, "type": "equity"}
            ]
        },
        "fund_2": {
            "fund_id": "f00000tsop",
            "holdingList": [
                {"security_name": "Microsoft Corp", "weighting": 4.2, "type": "equity"},
                {"security_name": "Apple Inc", "weighting": 3.8, "type": "equity"},
                {"security_name": "Amazon Inc", "weighting": 3.5, "type": "equity"},
                {"security_name": "Alphabet Inc", "weighting": 3.1, "type": "equity"},
                {"security_name": "HDFC Bank Ltd", "weighting": 2.8, "type": "equity"}
            ]
        }
    }
    
    # Analyze the sample data
    quantitative_results = analyzer.analyze_portfolio(sample_data)
    ai_analysis = ai_analyst.generate_analysis_report(quantitative_results)
    
    return jsonify({
        'quantitative_data': quantitative_results,
        'ai_analysis': ai_analysis
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Starting Finalitics Platform by KVAGI...")
    print("⚠️  Warning: Google API key not configured. AI analysis will be limited." if not os.getenv('GOOGLE_API_KEY') or os.getenv('GOOGLE_API_KEY') == 'your_google_gemini_api_key_here' else "✅ Google API key configured.")
    print("📱 Open your browser and go to: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5001)
