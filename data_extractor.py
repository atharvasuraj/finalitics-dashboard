"""
Data Extraction Script for Mutual Fund Holdings
Based on the methodology from FinalSubmissionFin.ipynb
"""

import requests
import json
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
import random

class MutualFundDataExtractor:
    """
    Extract mutual fund data from Morningstar India
    """
    
    def __init__(self):
        self.base_url = "https://www.morningstar.in"
        self.api_base = "https://www.morningstar.in/api/detailedportfolio/v3/"
        self.session = requests.Session()
        
        # Headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_fund_house_names(self, html_snippet=None):
        """Extract fund house names from Morningstar footer"""
        if html_snippet is None:
            # Default HTML snippet from the notebook
            html_snippet = """
            <a title='List of mutual funds for ADITYABIRLA' href='/funds/adityabirla.aspx' target="_top" class="FooterMF">ADITYABIRLA</a>
            <a title='List of mutual funds for AXIS' href='/funds/axis.aspx' target="_top" class="FooterMF">AXIS</a>
            <a title='List of mutual funds for HDFC' href='/funds/hdfc.aspx' target="_top" class="FooterMF">HDFC</a>
            <a title='List of mutual funds for ICICI' href='/funds/icici.aspx' target="_top" class="FooterMF">ICICI</a>
            <a title='List of mutual funds for SBI' href='/funds/sbi.aspx' target="_top" class="FooterMF">SBI</a>
            """
        
        soup = BeautifulSoup(html_snippet, 'html.parser')
        fund_house_links = soup.find_all('a', href=lambda href: href and '/funds/' in href)
        
        fund_house_names = []
        for link in fund_house_links:
            name = link.get_text()
            if name:
                fund_house_names.append(name.strip())
        
        return fund_house_names
    
    def extract_fund_ids_from_index_page(self, index_page_url):
        """Extract fund IDs from a fund house index page"""
        try:
            response = self.session.get(index_page_url, timeout=10)
            response.raise_for_status()
            
            # Pattern to match fund IDs in URLs
            fund_id_pattern = re.compile(r'/funds/(\w+)/')
            
            fund_ids = []
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                match = fund_id_pattern.search(href)
                if match:
                    fund_id = match.group(1)
                    if fund_id.lower().startswith('f') and len(fund_id) > 5:
                        fund_ids.append(fund_id)
            
            unique_fund_ids = list(set(fund_ids))
            print(f"Found {len(unique_fund_ids)} unique fund IDs from {index_page_url}")
            return unique_fund_ids
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {index_page_url}: {e}")
            return []
    
    def build_detailed_portfolio_url(self, fund_id, fund_name="fund"):
        """Build URL for detailed portfolio page"""
        encoded_fund_name = quote(fund_name)
        return f"{self.base_url}/funds/{fund_id}/{encoded_fund_name}/detailed-portfolio.aspx"
    
    def extract_access_token(self, html_content):
        """Extract access token from HTML meta tag"""
        soup = BeautifulSoup(html_content, 'html.parser')
        access_token_meta = soup.find('meta', attrs={'name': 'accessToken'})
        if access_token_meta and 'content' in access_token_meta.attrs:
            return access_token_meta['content']
        return None
    
    def fetch_fund_data(self, fund_id, fund_name="fund"):
        """Fetch detailed fund data using the API"""
        try:
            # Step 1: Get access token from detailed portfolio page
            portfolio_url = self.build_detailed_portfolio_url(fund_id, fund_name)
            token_response = self.session.get(portfolio_url, timeout=10)
            token_response.raise_for_status()
            
            access_token = self.extract_access_token(token_response.text)
            if not access_token:
                print(f"Could not extract access token for {fund_id}")
                return None
            
            # Step 2: Use token to fetch data from API
            api_url = f"{self.api_base}{fund_id}?accesstoken={access_token}"
            data_response = self.session.get(api_url, timeout=10)
            
            if data_response.status_code == 200:
                try:
                    data = data_response.json()
                    print(f"Successfully fetched data for {fund_id}")
                    return data
                except json.JSONDecodeError:
                    print(f"Could not decode JSON for {fund_id}")
                    return None
            else:
                print(f"API returned status {data_response.status_code} for {fund_id}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {fund_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {fund_id}: {e}")
            return None
    
    def process_fund_data(self, fund_data, fund_id):
        """Process raw fund data into standardized format"""
        if not fund_data:
            return None
        
        try:
            holdings = []
            
            # Extract equity holdings
            if 'equityHoldingPage' in fund_data and 'holdingList' in fund_data['equityHoldingPage']:
                equity_holdings = fund_data['equityHoldingPage']['holdingList']
                for holding in equity_holdings:
                    holdings.append({
                        "security_name": holding.get('securityName', ''),
                        "weighting": holding.get('weighting', 0),
                        "type": "equity"
                    })
            
            # Extract bond holdings
            if 'bondHoldingPage' in fund_data and 'holdingList' in fund_data['bondHoldingPage']:
                bond_holdings = fund_data['bondHoldingPage']['holdingList']
                for holding in bond_holdings:
                    holdings.append({
                        "security_name": holding.get('securityName', ''),
                        "weighting": holding.get('weighting', 0),
                        "type": "bond"
                    })
            
            return {
                "fund_id": fund_data.get('secId', fund_id),
                "holdingList": holdings
            }
            
        except Exception as e:
            print(f"Error processing fund data for {fund_id}: {e}")
            return None
    
    def extract_portfolio_data(self, num_funds=10, fund_houses=None):
        """
        Extract portfolio data for a specified number of funds
        
        Args:
            num_funds: Number of funds to extract (default: 10)
            fund_houses: List of fund house names to extract from (optional)
        
        Returns:
            Dictionary with processed fund data
        """
        if fund_houses is None:
            fund_houses = ['hdfc', 'icici', 'sbi', 'axis', 'adityabirla']
        
        all_fund_ids = []
        
        # Collect fund IDs from specified fund houses
        for fund_house in fund_houses:
            index_url = f"{self.base_url}/funds/{fund_house.lower()}.aspx"
            fund_ids = self.extract_fund_ids_from_index_page(index_url)
            all_fund_ids.extend(fund_ids)
            
            if len(all_fund_ids) >= num_funds * 2:  # Get extra IDs for filtering
                break
            
            time.sleep(1)  # Be polite to the server
        
        # Randomly select funds to analyze
        if len(all_fund_ids) > num_funds:
            selected_fund_ids = random.sample(all_fund_ids, num_funds)
        else:
            selected_fund_ids = all_fund_ids
        
        print(f"Selected {len(selected_fund_ids)} funds for analysis")
        
        # Extract data for selected funds
        portfolio_data = {}
        for i, fund_id in enumerate(selected_fund_ids):
            print(f"\nProcessing fund {i+1}/{len(selected_fund_ids)}: {fund_id}")
            
            raw_data = self.fetch_fund_data(fund_id)
            processed_data = self.process_fund_data(raw_data, fund_id)
            
            if processed_data:
                portfolio_data[f"fund_{i}"] = processed_data
            
            time.sleep(2)  # Be polite to the server
        
        return portfolio_data
    
    def save_portfolio_data(self, portfolio_data, filename="extracted_portfolio.json"):
        """Save portfolio data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
            print(f"Portfolio data saved to {filename}")
        except Exception as e:
            print(f"Error saving portfolio data: {e}")

def main():
    """Main function to demonstrate usage"""
    extractor = MutualFundDataExtractor()
    
    print("🚀 Starting Mutual Fund Data Extraction...")
    print("This may take several minutes depending on the number of funds...")
    
    # Extract data for 10 funds from major fund houses
    portfolio_data = extractor.extract_portfolio_data(
        num_funds=10,
        fund_houses=['hdfc', 'icici', 'sbi', 'axis', 'adityabirla']
    )
    
    if portfolio_data:
        print(f"\n✅ Successfully extracted data for {len(portfolio_data)} funds")
        
        # Save to file
        extractor.save_portfolio_data(portfolio_data, "extracted_portfolio.json")
        
        # Display summary
        print("\n📊 Portfolio Summary:")
        for fund_key, fund_data in portfolio_data.items():
            holdings_count = len(fund_data.get('holdingList', []))
            print(f"  {fund_key}: {fund_data['fund_id']} ({holdings_count} holdings)")
    else:
        print("❌ No data extracted. Please check your internet connection and try again.")

if __name__ == "__main__":
    main()
