#!/usr/bin/env python3
"""
Test the CSV conversion function with Fundtester.csv
"""
import pandas as pd
import json

def convert_csv_to_portfolio_format(df):
    """
    Convert CSV format to portfolio JSON format
    Expected CSV columns: Fund ID, Fund Name, Security Name, Weighting, Type
    """
    try:
        # Clean column names (remove BOM and extra spaces) - FIRST
        df.columns = df.columns.str.strip().str.replace('\ufeff', '').str.replace('ï»¿', '')
        
        # Now work with the cleaned columns
        actual_columns = list(df.columns)
        print(f"Cleaned CSV columns: {actual_columns}")
        
        # Try to find the correct column mappings
        fund_id_col = None
        security_name_col = None
        weighting_col = None
        type_col = None
        
        for col in actual_columns:
            col_lower = col.lower().strip()
            if 'fund' in col_lower and 'id' in col_lower:
                fund_id_col = col
            elif 'security' in col_lower and 'name' in col_lower:
                security_name_col = col
            elif 'weighting' in col_lower:
                weighting_col = col
            elif 'type' in col_lower:
                type_col = col
        
        # Check if we found all required columns
        if not all([fund_id_col, security_name_col, weighting_col, type_col]):
            print(f"Could not find required columns:")
            print(f"  Fund ID column: {fund_id_col}")
            print(f"  Security Name column: {security_name_col}")
            print(f"  Weighting column: {weighting_col}")
            print(f"  Type column: {type_col}")
            return {}
        
        print(f"Found columns:")
        print(f"  Fund ID: '{fund_id_col}'")
        print(f"  Security Name: '{security_name_col}'")
        print(f"  Weighting: '{weighting_col}'")
        print(f"  Type: '{type_col}'")
        
        # Create standardized column mapping
        column_mapping = {
            fund_id_col: 'fund_id',
            security_name_col: 'security_name',
            weighting_col: 'weighting',
            type_col: 'type'
        }
        
        # Clean and convert data
        df = df.rename(columns=column_mapping)
        
        # Clean weighting values (remove %, handle nan)
        df['weighting'] = df['weighting'].astype(str).str.replace('%', '').str.replace('nan', '0')
        df['weighting'] = pd.to_numeric(df['weighting'], errors='coerce').fillna(0)
        
        # Filter out rows with 0 or invalid weightings
        df = df[df['weighting'] > 0]
        
        # Group by fund_id and convert to required format
        portfolio_data = {}
        fund_counter = 0
        
        for fund_id, fund_group in df.groupby('fund_id'):
            holdings = []
            for _, row in fund_group.iterrows():
                holdings.append({
                    "security_name": str(row['security_name']).strip(),
                    "weighting": float(row['weighting']),
                    "type": str(row.get('type', 'equity')).lower()
                })
            
            if holdings:  # Only add if there are valid holdings
                portfolio_data[f"fund_{fund_counter}"] = {
                    "fund_id": str(fund_id),
                    "holdingList": holdings
                }
                fund_counter += 1
        
        print(f"Successfully converted CSV to portfolio format: {len(portfolio_data)} funds")
        return portfolio_data
        
    except Exception as e:
        print(f"Error converting CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    # Test with Fundtester.csv
    try:
        # Try different encodings
        try:
            df = pd.read_csv('Fundtester.csv', encoding='utf-8-sig')
            print("✅ Successfully read CSV with utf-8-sig encoding")
        except UnicodeDecodeError:
            df = pd.read_csv('Fundtester.csv', encoding='latin-1')
            print("✅ Successfully read CSV with latin-1 encoding")
        
        print(f"CSV shape: {df.shape}")
        print(f"Raw columns: {list(df.columns)}")
        
        # Clean column names first
        df.columns = df.columns.str.strip().str.replace('\ufeff', '').str.replace('ï»¿', '')
        print(f"Cleaned columns: {list(df.columns)}")
        print(f"First few rows:")
        print(df.head())
        
        # Convert to portfolio format
        portfolio_data = convert_csv_to_portfolio_format(df)
        
        if portfolio_data:
            print(f"\n✅ Conversion successful!")
            print(f"Number of funds: {len(portfolio_data)}")
            
            # Show summary of each fund
            for fund_key, fund_info in portfolio_data.items():
                holdings_count = len(fund_info['holdingList'])
                total_weight = sum(h['weighting'] for h in fund_info['holdingList'])
                print(f"  {fund_key}: {fund_info['fund_id']} ({holdings_count} holdings, {total_weight:.2f}% total)")
            
            # Save to test file
            with open('test_portfolio_output.json', 'w', encoding='utf-8') as f:
                json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Test output saved to test_portfolio_output.json")
            
        else:
            print("❌ Conversion failed!")
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
