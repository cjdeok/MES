import os
import io
import json
import openpyxl
from collections import defaultdict
from flask import Flask, render_template, jsonify, request
from jinja2 import ChoiceLoader, FileSystemLoader
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

app = Flask(__name__)

# 파일 경로 스키마 정의 (Vercel Serverless 호환되도록 동적 경로 사용)
# Vercel에서는 /var/task 등 동적 디렉토리에서 실행되므로 __file__ 기반 절대경로 추출이 필수
if os.environ.get('VERCEL'):
    # Vercel 환경: api 폴더에서 실행될 경우 프로젝트 루트 지정 등 필요 시 조정
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 템플릿 검색 경로 설정 (루트 및 web/templates 동시 탐색)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(BASE_DIR),
    FileSystemLoader(os.path.join(BASE_DIR, 'web', 'templates'))
])

# 서버리스에서는 /tmp 디렉토리만 쓰기가 가능하지만, 여기선 단순 읽기 목적이므로 프로젝트 내 파일 참조
JSON_FILE = os.path.join(BASE_DIR, 'data', 'material_master.json')
THRESHOLD_FILE = os.path.join(BASE_DIR, 'data', 'inventory_thresholds.json')

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise Exception("Supabase 환경 변수가 설정되지 않았습니다.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        import traceback
        trace_str = traceback.format_exc()
        html_files = []
        if os.path.exists(BASE_DIR):
            html_files = [f for f in os.listdir(BASE_DIR) if f.endswith('.html')]
        return f"Error: {str(e)}<br>BASE_DIR: {BASE_DIR}<br>Files in BASE_DIR: {html_files}<br><pre>{trace_str}</pre>", 500

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/production')
def production():
    return render_template('production.html')

@app.route('/producible')
def producible():
    return render_template('producible.html')

@app.route('/material-info')
def material_info():
    return render_template('material_info.html')

@app.route('/upload-usage')
def upload_usage():
    return render_template('upload_usage.html')

@app.route('/finished-product')
def finished_product():
    return render_template('finished_product.html')

@app.route('/api/producible')
def get_producible():
    """현 재고량 기준 원료별 최대 생산가능 kit수 계산"""
    try:
        import bisect

        # ── 1. BOM.xlsx 파싱 ──────────────────────────────────────
        BOM_FILE = os.path.join(BASE_DIR, 'data', 'BOM.xlsx')
        wb = openpyxl.load_workbook(BOM_FILE, read_only=True, data_only=True)
        ws = wb.active

        header = [cell for cell in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
        kit_cols = len(header) - 2  # 256

        bom = {}
        bom_name = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            code = row[0]
            if not code:
                continue
            name = row[1] or ''
            usages = [row[2 + i] or 0 for i in range(kit_cols)]
            bom[code] = usages
            bom_name[code] = name
        wb.close()

        # ── 2. 단위 매핑 ────────────────────────────────────────
        unit_map = {}
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                master = json.load(f)
            unit_map = {code: info.get('단위', '') for code, info in master.items()}
        except Exception:
            pass

        # ── 3. DB 현재고 조회 (Supabase) ─────────────────────────
        sb = get_supabase_client()
        # 모든 raw_materials 가져오기
        res = sb.table('raw_materials').select('item_code, product_name, transaction_type, quantity').execute()
        
        stock_map = defaultdict(lambda: {'product_name': '', 'total_stock': 0.0})
        for r in res.data:
            code = r['item_code']
            qty = r['quantity'] or 0
            if r['transaction_type'] == '입고':
                stock_map[code]['total_stock'] += qty
            else:
                stock_map[code]['total_stock'] -= qty
            if r.get('product_name'):
                stock_map[code]['product_name'] = r['product_name']

        # ── 4. 계산 ───────────────────
        results = []
        for code, usages in bom.items():
            stock_info = stock_map.get(code, {})
            current_stock = stock_info.get('total_stock', 0)
            product_name = stock_info.get('product_name') or bom_name.get(code, '')

            max_kit = 0
            for i, usage in enumerate(usages):
                if usage is None or usage == 0:
                    max_kit = kit_cols
                elif current_stock >= usage:
                    max_kit = i + 1
                else:
                    break

            results.append({
                'item_code': code,
                'product_name': product_name,
                'current_stock': round(current_stock, 4),
                'unit': unit_map.get(code, ''),
                'max_kit': max_kit,
            })

        results.sort(key=lambda x: x['item_code'])
        return jsonify({'status': 'success', 'data': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/materials')
def get_materials():
    """material_master.json에서 원료 코드와 이름을 가져옵니다."""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        materials = []
        for code, details in data.items():
            materials.append({
                'code': code,
                'name': details.get('제품명', 'Unknown')
            })
            
        materials = sorted(materials, key=lambda x: x['code'])
        return jsonify({'status': 'success', 'data': materials})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/lots/<item_code>')
def get_lots(item_code):
    try:
        sb = get_supabase_client()
        res = sb.table('raw_materials').select('lot_no').eq('item_code', item_code).execute()
        lots = list(set([r['lot_no'] for r in res.data if r.get('lot_no')]))
        lots.sort()
        return jsonify({'status': 'success', 'data': lots})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/inventory')
def get_inventory():
    item_code = request.args.get('item_code')
    lot_no = request.args.get('lot_no')
    
    if not item_code or not lot_no:
        return jsonify({'status': 'error', 'message': 'Missing item_code or lot_no'}), 400
        
    try:
        sb = get_supabase_client()
        # 이력 조회
        res_hist = sb.table('raw_materials').select('id, product_name, transaction_type, transaction_date, purpose, quantity').eq('item_code', item_code).eq('lot_no', lot_no).order('transaction_date').order('id').execute()
        history = res_hist.data
        
        # 원료 상세 조회
        res_info = sb.table('material_info').select('receive_date, qc_date, expire_date').eq('item_code', item_code).eq('lot_no', lot_no).limit(1).execute()
        material_details = res_info.data[0] if res_info.data else None
        
        total_in = sum(item['quantity'] for item in history if item['transaction_type'] == '입고')
        total_out = sum(item['quantity'] for item in history if item['transaction_type'] == '출고')
        current_stock = total_in - total_out
        
        summary = {
            'total_in': total_in,
            'total_out': total_out,
            'current_stock': current_stock
        }
        
        return jsonify({
            'status': 'success', 
            'summary': summary,
            'history': history,
            'material_details': material_details
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stock/summary')
def get_stock_summary():
    try:
        unit_map = {}
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                master = json.load(f)
            unit_map = {code: info.get('단위', '') for code, info in master.items()}
        except Exception:
            pass

        sb = get_supabase_client()
        res = sb.table('raw_materials').select('item_code, product_name, transaction_type, quantity').execute()
        
        stats = defaultdict(lambda: {'product_name': '', 'total_in': 0.0, 'total_out': 0.0})
        for r in res.data:
            code = r['item_code']
            qty = r['quantity'] or 0
            if r['transaction_type'] == '입고':
                stats[code]['total_in'] += qty
            else:
                stats[code]['total_out'] += qty
            if r.get('product_name'):
                stats[code]['product_name'] = r['product_name']

        rows = []
        for code, data in stats.items():
            rows.append({
                'item_code': code,
                'product_name': data['product_name'],
                'total_stock': data['total_in'] - data['total_out'],
                'unit': unit_map.get(code, '')
            })
            
        rows.sort(key=lambda x: x['item_code'])
        return jsonify({'status': 'success', 'data': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/material-info')
def get_material_info():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            master = json.load(f)

        thresholds = {}
        try:
            with open(THRESHOLD_FILE, 'r', encoding='utf-8') as f:
                thresholds = json.load(f)
        except Exception:
            pass

        sb = get_supabase_client()
        res = sb.table('raw_materials').select('item_code, transaction_type, quantity').execute()
        
        stock_map = defaultdict(float)
        for r in res.data:
            qty = r['quantity'] or 0
            if r['transaction_type'] == '입고':
                stock_map[r['item_code']] += qty
            else:
                stock_map[r['item_code']] -= qty

        result = []
        for code, info in master.items():
            safe = thresholds.get(code, {}).get('safe_stock_level', None)
            current = stock_map.get(code, 0.0)

            result.append({
                'item_code': code,
                'product_name': info.get('제품명', ''),
                'cat_no': info.get('Cat_No', ''),
                'package_unit': info.get('포장단위', ''),
                'unit': info.get('단위', ''),
                'manufacturer': info.get('제조사', ''),
                'storage_temp': info.get('보관온도', ''),
                'storage_location': info.get('보관장소', ''),
                'unit_price': info.get('단가', None),
                'safe_stock': safe,
                'current_stock': round(current, 4)
            })

        result.sort(key=lambda x: x['item_code'])
        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/production/calculate')
def calculate_production():
    kit_qty = request.args.get('kit_qty', type=int)
    if not kit_qty or kit_qty < 1 or kit_qty > 256:
        return jsonify({'status': 'error', 'message': 'Invalid kit quantity (1-256)'}), 400
        
    try:
        sb = get_supabase_client()
        # 1. BOM 소요량 조회
        res_bom = sb.table('kit_bom').select('material_code, material_name, usage_qty').eq('kit_qty', kit_qty).execute()
        bom_items = res_bom.data

        # 2. 모든 material_info (rec_date, expire_date용)
        res_info = sb.table('material_info').select('item_code, lot_no, receive_date, expire_date').execute()
        info_map = {}
        for r in res_info.data:
            info_map[(r['item_code'], r['lot_no'])] = {
                'receive_date': r['receive_date'],
                'expire_date': r['expire_date']
            }

        # 3. 모든 raw_materials 재고 조회 (각 lot 별 잔량 계산)
        codes = [item['material_code'] for item in bom_items]
        res_raw = sb.table('raw_materials').select('item_code, lot_no, transaction_type, quantity').in_('item_code', codes).execute()
        
        lot_stocks = defaultdict(float)
        lot_in_qty = defaultdict(float)
        for r in res_raw.data:
            key = (r['item_code'], r['lot_no'])
            if r['transaction_type'] == '입고':
                lot_stocks[key] += (r['quantity'] or 0)
                lot_in_qty[key] += (r['quantity'] or 0)
            else:
                lot_stocks[key] -= (r['quantity'] or 0)

        results = []
        for item in bom_items:
            mat_code = item['material_code']
            mat_name = item['material_name']
            required_qty = item['usage_qty']

            # 가용 재고 목록 생성
            available_lots = []
            for (itm_cd, lot_no), stock in lot_stocks.items():
                if itm_cd == mat_code and stock > 0:
                    info = info_map.get((itm_cd, lot_no), {})
                    rec_date = info.get('receive_date') or '9999-12-31'
                    exp_date = info.get('expire_date') or '9999-12-31'
                    
                    # 입고량 넷 대비 잔량이 적으면 이미 사용중인(뜯은) 원료로 간주
                    total_in = lot_in_qty.get((itm_cd, lot_no), 0)
                    is_in_use = 0 if stock < total_in else 1
                    
                    available_lots.append({
                        'lot_no': lot_no,
                        'current_stock': stock,
                        'rec_date': rec_date,
                        'exp_date': exp_date,
                        'is_in_use': is_in_use
                    })
            
            # 최우선: 사용중인(0) 로트 -> 유효기간 빠른 순 -> 입고일 빠른 순 정렬
            available_lots.sort(key=lambda x: (x['is_in_use'], x['exp_date'], x['rec_date'], x['lot_no']))

            allocated_lots = []
            remaining_to_allocate = required_qty
            
            for lot in available_lots:
                if remaining_to_allocate <= 0:
                    break
                    
                alloc_qty = min(remaining_to_allocate, lot['current_stock'])
                allocated_lots.append({
                    'lot_no': lot['lot_no'],
                    'receive_date': lot['rec_date'] if lot['rec_date'] != '9999-12-31' else '정보 없음',
                    'available_stock': lot['current_stock'],
                    'allocated_qty': round(alloc_qty, 4)
                })
                
                remaining_to_allocate -= alloc_qty
                
            shortage_qty = round(max(0, remaining_to_allocate), 4)
            
            results.append({
                'material_code': mat_code,
                'material_name': mat_name,
                'required_qty': round(required_qty, 4),
                'allocated_lots': allocated_lots,
                'shortage_qty': shortage_qty,
                'status': 'success' if shortage_qty == 0 else 'shortage'
            })
            
        return jsonify({'status': 'success', 'data': results})
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"ERROR in get_finished_product_statistics: {err_msg}")
        return jsonify({'status': 'error', 'message': str(e), 'trace': err_msg}), 500

@app.route('/api/usage/upload', methods=['POST'])
def upload_usage_api():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '파일이 첨부되지 않았습니다.'}), 400

    file = request.files['file']
    if not file.filename or not file.filename.endswith('.xlsx'):
        return jsonify({'status': 'error', 'message': '.xlsx 파일만 업로드 가능합니다.'}), 400

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file.read()), read_only=True, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(min_row=2, values_only=True))
        wb.close()

        if not rows:
            return jsonify({'status': 'error', 'message': '데이터가 없습니다. 2행부터 데이터를 입력해 주세요.'}), 400

        sb = get_supabase_client()
        success_count = 0
        errors = []
        
        insert_data = []

        for idx, row in enumerate(rows, start=2):
            try:
                item_code = str(row[0] or '').strip()
                product_name = str(row[1] or '').strip()
                lot_no = str(row[2] or '').strip()
                transaction_date = str(row[3] or '').strip()
                purpose = str(row[4] or '').strip()
                quantity = row[5]

                if not item_code or quantity is None:
                    errors.append(f'{idx}행: 원료코드 또는 사용량이 비어 있습니다.')
                    continue

                quantity = float(quantity)
                if quantity <= 0:
                    errors.append(f'{idx}행: 사용량은 0보다 커야 합니다. (값: {quantity})')
                    continue
                
                insert_data.append({
                    'product_name': product_name,
                    'item_code': item_code,
                    'lot_no': lot_no,
                    'transaction_type': '출고',
                    'transaction_date': transaction_date,
                    'purpose': purpose,
                    'quantity': quantity
                })
            except Exception as e:
                errors.append(f'{idx}행 파싱 오류: {str(e)}')
                
        if insert_data:
            try:
                # 500개씩 batch insert
                for i in range(0, len(insert_data), 500):
                    batch = insert_data[i:i+500]
                    sb.table('raw_materials').insert(batch).execute()
                    success_count += len(batch)
            except Exception as e:
                errors.append(f'DB 저장 중 오류: {str(e)}')

        return jsonify({
            'status': 'success',
            'success_count': success_count,
            'error_count': len(errors),
            'errors': errors
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'파일 처리 중 오류: {str(e)}'}), 500

@app.route('/api/usage/recent')
def get_recent_usage():
    try:
        sb = get_supabase_client()
        res = sb.table('raw_materials').select('id, item_code, product_name, lot_no, transaction_date, purpose, quantity').eq('transaction_type', '출고').order('id', desc=True).limit(50).execute()
        return jsonify({'status': 'success', 'data': res.data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/finished-product/inventory')
def get_finished_product_inventory():
    try:
        sb = get_supabase_client()
        res = sb.table('finished_products').select('*').execute()
        
        # product_code, product_name, lot_no 복합키
        stats = defaultdict(lambda: {'mfg_date': None, 'total_in': 0.0, 'total_out': 0.0})
        
        for r in res.data:
            key = (r['product_code'], r['product_name'], r['lot_no'])
            if r['transaction_type'] == '완제품입고':
                stats[key]['total_in'] += (r['quantity_kit'] or 0)
                if not stats[key]['mfg_date'] or r['transaction_date'] < stats[key]['mfg_date']:
                    stats[key]['mfg_date'] = r['transaction_date']
            elif r['transaction_type'] == '완제품 출고':
                stats[key]['total_out'] += (r['quantity_kit'] or 0)
                
        rows = []
        for (p_code, p_name, l_no), s in stats.items():
            current_stock = s['total_in'] - s['total_out']
            # 현재고가 1개 이상일 때만 표시한다는 정책 적용
            if current_stock >= 1:
                rows.append({
                    'product_code': p_code,
                    'product_name': p_name,
                    'lot_no': l_no,
                    'manufacture_date': s['mfg_date'],
                    'total_in': s['total_in'],
                    'total_out': s['total_out'],
                    'current_stock': current_stock
                })
                
        rows.sort(key=lambda x: (x['manufacture_date'] or '', x['product_code'] or '', x['lot_no'] or ''))            
        return jsonify({'status': 'success', 'data': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/finished-product/lot/<path:lot_no>')
def get_finished_product_lot_details(lot_no):
    try:
        sb = get_supabase_client()
        res = sb.table('finished_products').select('transaction_type, transaction_date, quantity_kit, destination, qc_info, remark').eq('lot_no', lot_no).order('transaction_date').order('id').execute()
        return jsonify({'status': 'success', 'data': res.data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/finished-product/statistics')
def get_finished_product_statistics():
    year = request.args.get('year')
    product_code = request.args.get('product_code')
    
    try:
        sb = get_supabase_client()
        res = sb.table('finished_products').select('lot_no, product_code, transaction_type, transaction_date, quantity_kit').execute()
        
        mfg_dates = {}
        for r in res.data:
            if r['transaction_type'] == '완제품입고':
                key = (r['lot_no'], r['product_code'])
                if key not in mfg_dates or r['transaction_date'] < mfg_dates[key]:
                    mfg_dates[key] = r['transaction_date']
                    
        total_in = 0.0
        total_out = 0.0
        
        for r in res.data:
            key = (r['lot_no'], r['product_code'])
            mfg_date = mfg_dates.get(key)
            if not mfg_date:
                continue
                
            mfg_year = mfg_date[:4] if mfg_date else None
            
            if year and year != 'all' and mfg_year != year:
                continue
            if product_code and product_code != 'all' and r['product_code'] != product_code:
                continue
                
            if r['transaction_type'] == '완제품입고':
                total_in += (r['quantity_kit'] or 0)
            elif r['transaction_type'] == '완제품 출고':
                total_out += (r['quantity_kit'] or 0)
                
        stats = {
            'total_in': total_in,
            'total_out': total_out
        }
        return jsonify({'status': 'success', 'data': stats})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
