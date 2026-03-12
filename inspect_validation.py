import openpyxl
import json

file_path = r"c:\Users\ENS-1000\Documents\Antigravity\MES\.tmp\연간밸리데이션 계획 (2026).xlsx"
wb = openpyxl.load_workbook(file_path, data_only=True)
ws = wb.active

data = []
for row in ws.iter_rows(values_only=True):
    data.append(row)

print(json.dumps(data[:10], ensure_ascii=False))
