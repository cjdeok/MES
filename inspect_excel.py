import pandas as pd

path = r'c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\생산팀 계측기 검교정 일자(26.01).xlsx'
df = pd.read_excel(path, header=None)

print("--- Data Inspection ---")
for i, row in df.head(15).iterrows():
    # NaN이 아닌 값만 모아서 출력
    vals = [f"Col{j}: {v}" for j, v in enumerate(row) if pd.notna(v)]
    print(f"Row {i}: {vals}")
