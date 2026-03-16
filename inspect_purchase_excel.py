import pandas as pd
import os

file_path = r"c:\Users\ENS-1000\Documents\Antigravity\원료구매요청서 정리\20년 구매 정보 단가.xlsx"

def inspect():
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        excel_data = pd.ExcelFile(file_path)
        print(f"Sheet names: {excel_data.sheet_names}")
        
        sheet_name = 'Sheet1'
        if sheet_name in excel_data.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"\n[{sheet_name}] Columns:")
            print(df.columns.tolist())
            print("\nSample Data (First 3 rows):")
            print(df.head(3).to_string())
            print("\nData Types:")
            print(df.dtypes)
            print("-" * 50)
        else:
            print(f"Sheet {sheet_name} not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
