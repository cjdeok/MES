import pandas as pd
import os

file_path = r"c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\원료구매요청서.xlsx"

def inspect():
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        excel_data = pd.ExcelFile(file_path)
        print(f"Sheet names: {excel_data.sheet_names}")
        
        # 모든 시트의 컬럼 확인
        for sheet_name in excel_data.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            cols = [str(c).strip() for c in df.columns]
            print(f"\n[{sheet_name}] Total Columns: {len(cols)}")
            for i, col in enumerate(cols):
                print(f"{i+1}: {col}")
            print("-" * 50)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
