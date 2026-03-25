import codecs

app_path = r"c:\Users\ENS-1000\Documents\Antigravity\MES\web\app.py"

with codecs.open(app_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace existing generate_bom signature
text = text.replace("@app.route('/api/generate_bom', methods=['POST'])", "@app.route('/api/generate_bom_allocated', methods=['POST'])")
text = text.replace("def generate_bom():", "def generate_bom_allocated():")

original_api = """
@app.route('/api/generate_bom', methods=['POST'])
def generate_bom():
    data = request.json
    target_qty = float(data.get('target_qty', 256))
    requested_file = data.get('formula_file', 'BCE01_BOM_fomula_1.csv')
    
    if target_qty <= 0:
        return jsonify({"error": "유효한 목표 생산량을 입력해주세요."}), 400
        
    try:
        safe_filename = os.path.basename(requested_file)
        target_path = os.path.join(find_data_file('bom_formulas'), safe_filename)
        
        if not os.path.exists(target_path):
            return jsonify({"error": f"파일 '{safe_filename}'을(를) 찾을 수 없습니다."}), 404
            
        df = None
        try:
            df = pd.read_csv(target_path, encoding='utf-8')
        except:
            df = pd.read_csv(target_path, encoding='cp949')
            
        if 'Level' in df.columns:
            df['Level'] = df['Level'].ffill()
            
        def evaluate_formula(formula_str, target_val):
            def excel_if(cond, t, f): return t if cond else f
            def roundup(n, digits=0):
                factor = 10**digits
                return math.ceil(n * factor) / factor

            allowed_names = {
                "target_qty": float(target_val), 
                "target_gty": float(target_val),
                "target": float(target_val),
                "round": round, "ROUND": round,
                "ROUNDUP": roundup, "ceil": math.ceil,
                "int": int, "float": float, "abs": abs, "ABS": abs,
                "IF": excel_if, "IFF": excel_if,
                "req": 1.0, "ratio": 1.0
            }
            try:
                f_str = str(formula_str).strip()
                if f_str.lower() == 'nan' or not f_str: return 0.0
                f_str = re.sub(r'\\bif\\s*\\(', 'IFF(', f_str, flags=re.IGNORECASE)
                return float(eval(f_str, {"__builtins__": {}}, allowed_names))
            except Exception as e:
                return 0.0

        result = {
            "level0": {"제품명": f"전개 소스: {safe_filename}", "목표수량": target_qty},
            "level1": [], "level2": [], "level3": []
        }
        
        for _, r in df.iterrows():
            lvl_raw = r.get('Level')
            if pd.isna(lvl_raw): continue
            lvl = str(int(lvl_raw)) if isinstance(lvl_raw, (int, float)) else str(lvl_raw).strip()
            
            name1 = str(r.get('명칭 / 구성품', '')).strip()
            name2 = str(r.get('생산LOT', '')).strip()
            final_name = name2 if name2 and len(name2) > len(name1) and name2.lower() != 'nan' else name1
            
            formula = str(r.get('수식 (Formula)', '')).strip()
            unit = str(r.get('단위', '')).strip()
            parent = str(r.get('상위 LOT 연결', '')).strip()
            
            if not final_name or final_name.lower() in ['nan', '']: continue
            
            calculated_val = evaluate_formula(formula, target_qty)
            
            item_dict = {
                "상위Lot": parent if parent.lower() != 'nan' else '',
                "명칭 / 구성품": final_name,
                "생산Lot": name2 if name2.lower() != 'nan' else '',
                "계산된_소요량": round(calculated_val, 3),
                "단위": unit if unit.lower() != 'nan' else '',
                "레벨": lvl,
            }
            
            if lvl == '1': result["level1"].append(item_dict)
            elif lvl == '2': result["level2"].append(item_dict)
            elif lvl == '3': result["level3"].append(item_dict)
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

"""

# Insert original before the new one
insertion_point = text.find("@app.route('/api/generate_bom_allocated', methods=['POST'])")
if insertion_point != -1:
    text = text[:insertion_point] + original_api + text[insertion_point:]
    
with codecs.open(app_path, "w", encoding="utf-8") as f:
    f.write(text)
    
print("app.py updated")
