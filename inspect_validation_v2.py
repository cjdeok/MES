import openpyxl
import json

file_path = r"c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\연간밸리데이션 계획 (2026).xlsx"
wb = openpyxl.load_workbook(file_path, data_only=True)
ws = wb.active

data = []
for row in ws.iter_rows(values_only=True):
    # 빈 행 제외
    if all(v is None for v in row):
        continue
    data.append([str(v) if v is not None else "" for v in row])

for i, row in enumerate(data[:15]):
    print(f"Row {i}: {row}")
