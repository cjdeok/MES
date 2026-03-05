import os
import json
import sqlite3
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# 파일 경로 스키마 정의
BASE_DIR = r'c:\Users\ENS-1000\Documents\Antigravity\MES'
JSON_FILE = os.path.join(BASE_DIR, '.tmp', 'material_master.json')
DB_FILE = os.path.join(BASE_DIR, 'mes_database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/production')
def production():
    return render_template('production.html')

@app.route('/producible')
def producible():
    return render_template('producible.html')

@app.route('/api/producible')
def get_producible():
    """현 재고량 기준 원료별 최대 생산가능 kit수 계산"""
    try:
        import openpyxl, bisect

        # ── 1. BOM.xlsx 파싱 ──────────────────────────────────────
        BOM_FILE = os.path.join(BASE_DIR, '.tmp', 'BOM.xlsx')
        wb = openpyxl.load_workbook(BOM_FILE, read_only=True, data_only=True)
        ws = wb.active

        # 헤더 행: [코드, 품명, 1kit, 2kit, ..., 256kit]
        header = [cell for cell in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
        kit_cols = len(header) - 2  # 256

        # bom[item_code] = [소요량(1kit), 소요량(2kit), ..., 소요량(256kit)]
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

        # ── 2. 현재고 조회 ────────────────────────────────────────
        unit_map = {}
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                master = json.load(f)
            unit_map = {code: info.get('단위', '') for code, info in master.items()}
        except Exception:
            pass

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT item_code,
                   MAX(product_name) as product_name,
                   SUM(CASE WHEN transaction_type = '입고' THEN quantity ELSE -quantity END) as total_stock
            FROM raw_materials
            GROUP BY item_code
        ''')
        stock_rows = {row['item_code']: dict(row) for row in cursor.fetchall()}
        conn.close()

        # ── 3. 원료별 최대 생산가능 kit수 계산 ───────────────────
        results = []
        for code, usages in bom.items():
            stock_info = stock_rows.get(code, {})
            current_stock = stock_info.get('total_stock') or 0
            product_name = stock_info.get('product_name') or bom_name.get(code, '')

            # 소요량 배열 기준 이진탐색: usages[i] <= current_stock 인 최대 i+1
            max_kit = 0
            for i, usage in enumerate(usages):
                if usage is None or usage == 0:
                    # 소요량 0 → 무제한 취급 (kit_cols 전체 가능)
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

        # 코드 순 정렬
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
            
        # 코드 순으로 정렬
        materials = sorted(materials, key=lambda x: x['code'])
        return jsonify({'status': 'success', 'data': materials})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/lots/<item_code>')
def get_lots(item_code):
    """SQLite DB에서 특정 품목 코드에 대한 Lot 번호 목록을 가져옵니다."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 품목 코드에 해당하는 고유한 Lot 번호 조회
        cursor.execute('''
            SELECT DISTINCT lot_no 
            FROM raw_materials 
            WHERE item_code = ?
            ORDER BY lot_no
        ''', (item_code,))
        
        lots = [row['lot_no'] for row in cursor.fetchall() if row['lot_no']]
        conn.close()
        
        return jsonify({'status': 'success', 'data': lots})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/inventory')
def get_inventory():
    """특정 원료코드와 Lot 번호의 이력 및 요약 데이터를 가져옵니다."""
    item_code = request.args.get('item_code')
    lot_no = request.args.get('lot_no')
    
    if not item_code or not lot_no:
        return jsonify({'status': 'error', 'message': 'Missing item_code or lot_no'}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 상세 히스토리 조회
        cursor.execute('''
            SELECT id, product_name, transaction_type, transaction_date, purpose, quantity 
            FROM raw_materials 
            WHERE item_code = ? AND lot_no = ?
            ORDER BY transaction_date ASC, id ASC
        ''', (item_code, lot_no))
        
        history = [dict(row) for row in cursor.fetchall()]
        
        # 원료 상세 정보 조회 (입고일, QC일, 유효기간)
        cursor.execute('''
            SELECT receive_date, qc_date, expire_date
            FROM material_info
            WHERE item_code = ? AND lot_no = ?
            LIMIT 1
        ''', (item_code, lot_no))
        
        detail_row = cursor.fetchone()
        material_details = dict(detail_row) if detail_row else None
        
        # 요약 정보 계산
        total_in = sum(item['quantity'] for item in history if item['transaction_type'] == '입고')
        total_out = sum(item['quantity'] for item in history if item['transaction_type'] == '출고')
        current_stock = total_in - total_out
        
        conn.close()
        
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
    """원료별 총 재고량 요약 (원료코드, 원료명, 단위, 총 재고)"""
    try:
        # material_master.json에서 단위 정보 로드
        unit_map = {}
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                master = json.load(f)
            unit_map = {code: info.get('단위', '') for code, info in master.items()}
        except Exception:
            pass

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT item_code,
                   MAX(product_name) as product_name,
                   SUM(CASE WHEN transaction_type = '입고' THEN quantity ELSE -quantity END) as total_stock
            FROM raw_materials
            GROUP BY item_code
            ORDER BY item_code
        ''')
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # 단위 정보 매핑
        for row in rows:
            row['unit'] = unit_map.get(row['item_code'], '')

        return jsonify({'status': 'success', 'data': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/production/calculate')
def calculate_production():
    """키트 생산 수량에 따른 원료 소요량 및 선입선출 할당 내역 계산"""
    kit_qty = request.args.get('kit_qty', type=int)
    if not kit_qty or kit_qty < 1 or kit_qty > 256:
        return jsonify({'status': 'error', 'message': 'Invalid kit quantity (1-256)'}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # BOM 소요량 조회 (kit_qty에 해당하는 원료 리스트)
        cursor.execute('''
            SELECT material_code, material_name, usage_qty 
            FROM kit_bom 
            WHERE kit_qty = ?
        ''', (kit_qty,))
        bom_items = [dict(row) for row in cursor.fetchall()]

        results = []
        for item in bom_items:
            mat_code = item['material_code']
            mat_name = item['material_name']
            required_qty = item['usage_qty']

            # FIFO 가용 재고 조회 (각 lot 별 잔량 계산, 입고일 빠른 순 정렬)
            cursor.execute('''
                SELECT r.lot_no, 
                       SUM(CASE WHEN r.transaction_type = '입고' THEN r.quantity ELSE -r.quantity END) as current_stock,
                       IFNULL(m.receive_date, '9999-12-31') as rec_date
                FROM raw_materials r
                LEFT JOIN material_info m ON r.item_code = m.item_code AND r.lot_no = m.lot_no
                WHERE r.item_code = ?
                GROUP BY r.item_code, r.lot_no, rec_date
                HAVING current_stock > 0
                ORDER BY rec_date ASC, r.lot_no ASC
            ''', (mat_code,))
            
            available_lots = [dict(row) for row in cursor.fetchall()]

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
            
        conn.close()
        return jsonify({'status': 'success', 'data': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
