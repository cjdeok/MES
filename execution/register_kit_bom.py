import pandas as pd
import sqlite3
import os

# 경로 설정
base_dir = r"c:\Users\ENS-1000\Documents\Antigravity\MES"
excel_path = os.path.join(base_dir, ".tmp", "BOM.xlsx")
db_path = os.path.join(base_dir, "mes_database.db")

def register_kit_bom():
    if not os.path.exists(excel_path):
        print(f"BOM.xlsx 파일을 찾을 수 없습니다: {excel_path}")
        return

    print(f"데이터 로드 및 처리 중: {os.path.basename(excel_path)}")
    
    try:
        # 1. 엑셀 데이터 로드
        df = pd.read_excel(excel_path)
        
        # 컬럼 인덱스 0: 원료코드, 1: 원료명, 그 외: 키트 수량(1~256)
        id_vars = [df.columns[0], df.columns[1]]
        value_vars = df.columns[2:]
        
        # 2. Wide format -> Long format 변환 (Melt)
        df_melted = df.melt(id_vars=id_vars, value_vars=value_vars, var_name='kit_qty', value_name='usage_qty')
        
        # 컬럼명 변경
        df_melted.columns = ['material_code', 'material_name', 'kit_qty', 'usage_qty']
        
        # 데이터 정제 (kit_qty 컬럼에서 숫자만 추출: "1kit" -> 1)
        df_melted['kit_qty'] = df_melted['kit_qty'].astype(str).str.extract(r'(\d+)').astype(float)
        df_melted['usage_qty'] = pd.to_numeric(df_melted['usage_qty'], errors='coerce')
        df_melted = df_melted.dropna(subset=['kit_qty', 'usage_qty'])
        df_melted['kit_qty'] = df_melted['kit_qty'].astype(int)
        df_melted = df_melted[df_melted['usage_qty'] > 0]
        
        # 3. 중복 원료 항목 합산 처리 (사용자 요청 사항)
        print("중복 원료 항목 합산 처리 중...")
        # 이름은 첫 번째 발견된 것으로 유지
        name_map = df_melted.groupby('material_code')['material_name'].first().to_dict()
        
        df_aggregated = df_melted.groupby(['material_code', 'kit_qty'], as_index=False)['usage_qty'].sum()
        df_aggregated['material_name'] = df_aggregated['material_code'].map(name_map)
        
        # 컬럼 순서 재조정
        df_aggregated = df_aggregated[['material_code', 'material_name', 'kit_qty', 'usage_qty']]
        
        print(f"처리 완료: 총 {len(df_aggregated)}개 데이터")
        
    except Exception as e:
        print(f"데이터 처리 중 오류 발생: {e}")
        return

    # 4. DB 등록
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 생성
        cursor.execute("DROP TABLE IF EXISTS kit_bom")
        cursor.execute("""
            CREATE TABLE kit_bom (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_code TEXT,
                material_name TEXT,
                kit_qty INTEGER,
                usage_qty REAL
            )
        """)
        
        # 대량 삽입
        df_aggregated.to_sql('kit_bom', conn, if_exists='append', index=False)
        
        # 인덱스 생성 (조회 속도 최적화)
        cursor.execute("CREATE INDEX idx_kit_bom_lookup ON kit_bom (material_code, kit_qty)")
        
        conn.commit()
        print(f"DB 등록 성공: {db_path}")
        
    except Exception as e:
        print(f"DB 등록 오류: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    register_kit_bom()
