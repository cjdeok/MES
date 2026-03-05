# MES Agent 아키텍처 — 원부자재 · 생산지시 · 재고 관리

> 3계층 아키텍처(Directive → Orchestration → Execution)를
> 원부자재 관리 / 생산지시서 / 반제품·완제품 입출고 중심으로 구성한 예시입니다.

---

## 📁 전체 디렉토리 구조

```
mes-agent/
├── directives/
│   ├── create_production_order.md          # 생산지시서 작성 SOP
│   ├── manage_raw_material_inventory.md    # 원부자재 재고 관리 SOP
│   ├── record_semifinished_inout.md        # 반제품 입출고 기록 SOP
│   └── record_finished_inout.md            # 완제품 입출고 기록 SOP
│
├── execution/
│   ├── create_production_order.py          # 생산지시서 생성 및 DB 등록
│   ├── check_material_stock.py             # 원부자재 재고 조회 및 부족분 계산
│   ├── deduct_material_stock.py            # 생산지시 확정 시 원부자재 재고 차감
│   ├── record_semifinished_in.py           # 반제품 입고 등록
│   ├── record_semifinished_out.py          # 반제품 출고 등록 (다음 공정 투입)
│   ├── record_finished_in.py               # 완제품 입고 등록
│   ├── record_finished_out.py              # 완제품 출고 등록 (출하)
│   ├── generate_stock_report.py            # 재고 현황 Google Sheets 출력
│   └── send_alert.py                       # 재고 부족·초과 알림 (Slack)
│
├── .tmp/
│   ├── bom_exploded_{order_no}.json        # BOM 전개 결과 (임시)
│   ├── stock_check_{order_no}.json         # 재고 부족 체크 결과 (임시)
│   └── inout_draft_{date}.json             # 입출고 초안 (임시)
│
└── .env
    # MES_DB_HOST, MES_DB_USER, MES_DB_PASS
    # SLACK_BOT_TOKEN, SLACK_CHANNEL_STOCK
    # GOOGLE_SHEET_ID_STOCK, GOOGLE_SHEET_ID_INOUT
    # ERP_API_ENDPOINT, ERP_API_KEY
```

---

## Layer 1: Directive (지시 계층)

---

### `directives/create_production_order.md`

```markdown
# 생산지시서 작성 SOP

## 목적
영업 수주 또는 생산계획에 따라 생산지시서를 생성하고,
원부자재 재고 충분 여부를 확인한 뒤 지시를 확정한다.

## 입력
- product_code     : 완제품 품목 코드 (예: FG-1001)
- qty              : 생산 수량
- due_date         : 납기일 (YYYY-MM-DD)
- work_center      : 생산 라인 (예: LINE-01)
- order_source     : "sales_order" | "production_plan"
- order_ref_no     : 수주번호 또는 계획번호

## 실행 순서
1. execution/check_material_stock.py
   → BOM 전개 후 필요 원부자재 계산
   → 재고 부족 품목 리스트 생성
   → 출력: .tmp/stock_check_{order_no}.json

2. 재고 부족 품목이 있을 경우:
   → 사용자에게 부족 내역 보고 후 확인 요청
   → "발주 요청 포함하여 지시 생성" 또는 "부족분 확보 후 생성" 선택 받기

3. execution/create_production_order.py
   → 생산지시서 MES DB 등록
   → 지시 상태: DRAFT → CONFIRMED

4. execution/deduct_material_stock.py
   → 확정된 지시 기준으로 원부자재 재고 차감 (할당 처리)
   → 재고 상태: 가용재고 → 할당재고로 이동

5. execution/generate_stock_report.py
   → 차감 후 원부자재 재고 현황 Google Sheets 업데이트

## 출력
- MES DB: 생산지시서 레코드 생성 (status=CONFIRMED)
- 로컬 보고서: .tmp/ 폴더 내 원부자재 할당 내역 반영
- 콘솔 알림: 생산지시 확정 내역 출력

## 엣지 케이스
- BOM 미등록 품목: 사용자에게 BOM 등록 요청 후 중단
- 재고 부족 시 강제 진행 요청: 사용자 명시적 승인 필요 (스크립트 --force 플래그)
- 동일 품목 중복 지시: 기존 지시 번호 조회 후 사용자 확인

## 학습된 제약사항
- BOM 전개 레벨은 최대 5단계 (그 이상은 ERP 직접 조회 필요)
- 재고 차감은 지시 확정 시점 기준 (DRAFT 상태에서는 차감 안 함)
- ERP 연동 시 재고 동기화 딜레이 최대 10분 발생 가능
```

---

### `directives/manage_raw_material_inventory.md`

```markdown
# 원부자재 재고 관리 SOP

## 목적
원부자재(원자재·부자재·부품) 입고/출고/재고 현황을 관리하고
안전재고 이하 품목에 대해 즉시 알림을 발송한다.

## 주요 작업 유형
| 작업 | 트리거 | 관련 스크립트 |
|------|--------|--------------|
| 입고 등록 | 구매 입고 완료 | check_material_stock.py → deduct_material_stock.py |
| 출고 등록 | 생산지시 확정 | deduct_material_stock.py |
| 재고 조회 | 사용자 요청·주기적 실행 | check_material_stock.py → generate_stock_report.py |
| 안전재고 알림 | 재고 조회 후 임계값 비교 | send_alert.py |

## 입력 (입고 시)
- material_code  : 원부자재 코드
- qty            : 입고 수량
- unit           : 단위 (kg / ea / L / m 등)
- lot_no         : 입고 LOT 번호
- supplier_code  : 공급업체 코드
- po_no          : 구매발주 번호

## 재고 알림 기준 (콘솔 출력)
- 안전재고 이하: 가용재고 부족 경고 출력
- 재고 0 (소진): 재고 소진 및 긴급 조치 알림 출력
- 유효기간 30일 이내 (원자재): 품질 검사 필요 리스트에 추가

## 학습된 제약사항
- LOT 추적 필수 품목: 화학원료(CHM-*), 포장재(PKG-*) → lot_no 누락 시 입고 거부
- 단위 환산 필요 품목 코드 목록: /execution/unit_conversion_map.json 참조
- 월말 재고실사 기간(매월 마지막 날) 중 출고 처리는 실사 완료 후 반영
```

---

### `directives/record_semifinished_inout.md`

```markdown
# 반제품 입출고 기록 SOP

## 목적
공정 간 이동하는 반제품(WIP)의 입고(생산 완료)와
출고(다음 공정 투입)를 기록하여 공정 재고를 관리한다.

## 반제품 입고 (생산 완료 → 창고 입고)
### 입력
- semi_product_code : 반제품 코드 (예: WIP-2001)
- production_order_no : 생산지시 번호
- qty_produced      : 생산 수량
- qty_defect        : 불량 수량
- work_center       : 생산 라인

### 실행 순서
1. execution/record_semifinished_in.py
   → 양품 수량 = qty_produced - qty_defect
   → MES DB 반제품 재고 증가
   → 해당 생산지시 진행률 업데이트

2. execution/generate_stock_report.py
   → .tmp/stock_report_semi_{date}.csv 업데이트

## 반제품 출고 (창고 → 다음 공정 투입)
### 입력
- semi_product_code : 반제품 코드
- target_order_no   : 투입 대상 생산지시 번호
- qty               : 투입 수량

### 실행 순서
1. execution/check_material_stock.py --type semifinished
   → 반제품 재고 충분 여부 확인

2. execution/record_semifinished_out.py
   → 반제품 재고 차감
   → 투입 대상 지시에 자재 투입 이력 기록

## 엣지 케이스
- 불량률 10% 초과 시: 사용자에게 확인 요청 후 입고 처리
- 재고 부족으로 출고 불가 시: 대기 중인 생산지시 목록 조회 후 보고
```

---

### `directives/record_finished_inout.md`

```markdown
# 완제품 입출고 기록 SOP

## 목적
완제품의 생산 입고와 고객 출하 출고를 기록하고
재고 현황을 실시간으로 유지한다.

## 완제품 입고 (최종 공정 완료 → 완제품 창고)
### 입력
- product_code      : 완제품 코드 (예: FG-1001)
- production_order_no : 생산지시 번호
- qty_produced      : 생산 수량
- qty_defect        : 불량 수량
- inspection_result : "PASS" | "HOLD" | "FAIL"

### 실행 순서
1. inspection_result 확인:
   - PASS: 즉시 execution/record_finished_in.py 실행
   - HOLD: Slack #품질팀 알림 후 대기 (사용자 승인 필요)
   - FAIL: 불량 처리 지시 후 중단

2. execution/record_finished_in.py
   → 완제품 재고 증가
   → 생산지시 상태: IN_PROGRESS → COMPLETED

3. execution/generate_stock_report.py
   → Google Sheets "완제품 재고현황" 업데이트

## 완제품 출고 (창고 → 고객 출하)
### 입력
- product_code      : 완제품 코드
- sales_order_no    : 수주 번호
- customer_code     : 고객 코드
- qty               : 출하 수량
- ship_date         : 출하일

### 실행 순서
1. execution/check_material_stock.py --type finished
   → 완제품 재고 충분 여부 확인

2. execution/record_finished_out.py
   → 완제품 재고 차감
   → 출하 이력 기록 (수주번호·고객코드 연계)

3. execution/generate_stock_report.py
   → .tmp/stock_report_finished_{date}.csv 업데이트

## 엣지 케이스
- 부분 출하 허용: qty < 수주 수량인 경우 잔량 처리 방식 사용자 확인
- 재고 부족 시: 생산지시 가능 여부 조회 후 예상 가용일 안내
```

---

## Layer 2: Orchestration (조율 계층 - AI의 역할)

---

### 시나리오 1: "FG-1001 200개 생산지시 넣어줘, 납기는 3월 15일"

```
사용자: "FG-1001 200개 생산지시 넣어줘, 납기는 3월 15일"

AI (Orchestration):

① directives/create_production_order.md 읽기
   → 입력값 세팅:
      product_code = "FG-1001"
      qty          = 200
      due_date     = "2025-03-15"
      work_center  = 확인 필요 → 사용자에게 "어느 라인에서 생산할까요?" 질문

사용자: "LINE-02"

② execution/check_material_stock.py 실행
   → 입력: --product FG-1001 --qty 200
   → BOM 전개 결과:

   ┌─────────────────┬──────┬──────┬──────┬──────────┐
   │ 원부자재 코드    │ 필요량│ 현재고│ 할당재고│ 가용재고  │
   ├─────────────────┼──────┼──────┼──────┼──────────┤
   │ RM-A001 (철판)  │ 400kg│ 520kg│  80kg│  440kg ✅ │
   │ RM-B003 (수지)  │  60L │  45L │   0L │   45L ⚠️ │
   │ PKG-001 (박스)  │ 200ea│ 350ea│  50ea│  300ea ✅ │
   └─────────────────┴──────┴──────┴──────┴──────────┘

   → RM-B003(수지) 부족: 필요 60L, 가용 45L → 15L 부족

③ 사용자에게 부족 내역 보고:
   "RM-B003 수지가 15L 부족합니다.
    현재 가용재고 45L / 필요 60L
    → 구매 요청 포함 후 지시 생성할까요, 아니면 재고 확보 후 생성할까요?"

사용자: "일단 지시 넣고 구매팀에 알려줘"

④ execution/create_production_order.py 실행
   → 생산지시 번호 WO-20250227-0041 생성
   → 상태: CONFIRMED
   → 비고: "RM-B003 15L 부족 / 구매 요청 필요"

⑤ execution/deduct_material_stock.py 실행
   → RM-A001: 가용재고 440kg → 40kg (400kg 할당)
   → RM-B003: 가용재고 45L  → 0L  (45L 할당, 15L 미달 기록)
   → PKG-001: 가용재고 300ea → 100ea (200ea 할당)

⑥ execution/send_alert.py 실행
   → Slack #구매팀: "RM-B003 수지 15L 긴급 발주 요청 (WO-20250227-0041)"

⑦ execution/generate_stock_report.py 실행
   → Google Sheets "원부자재 재고현황" 업데이트

⑧ 사용자에게 결과 보고:
   "생산지시 WO-20250227-0041 확정되었습니다.
    - 원부자재 할당 완료 (RM-B003 15L 부족 → 구매팀 Slack 알림 발송)
    - 재고 현황: [Google Sheets 링크]"
```

---

### 시나리오 2: "반제품 WIP-2001 오늘 1공정 완료분 150개 입고 처리해줘"

```
사용자: "반제품 WIP-2001 오늘 1공정 완료분 150개 입고해줘, 불량 3개 나왔어"

AI (Orchestration):

① directives/record_semifinished_inout.md 읽기
   → 작업 유형: 반제품 입고
   → 입력값:
      semi_product_code    = "WIP-2001"
      qty_produced         = 150
      qty_defect           = 3
      양품 수량             = 147개

② 불량률 확인: 3/150 = 2% → 10% 미만, 정상 처리

③ execution/record_semifinished_in.py 실행
   → 반력: WIP-2001 재고 +147개
   → 연결 생산지시 진행률 업데이트
   → 입고 이력 기록:
      일시: 2025-02-27 14:32
      입고 147ea / 불량 3ea / 불량률 2%

④ execution/generate_stock_report.py 실행
   → Google Sheets "반제품 재고현황" 업데이트

⑤ 사용자에게 결과 보고:
   "WIP-2001 반제품 입고 완료:
    - 양품 입고: 147개 / 불량: 3개 (2%)
    - 현재 WIP-2001 재고: 312개
    - 반제품 재고현황: [Google Sheets 링크]"
```

---

### 시나리오 3: "오늘 완제품 FG-1001 출하 처리해줘, A사 수주 SO-2025-088, 100개"

```
사용자: "FG-1001 A사 SO-2025-088 100개 오늘 출하 처리해줘"

AI (Orchestration):

① directives/record_finished_inout.md 읽기
   → 작업 유형: 완제품 출고

② execution/check_material_stock.py --type finished 실행
   → FG-1001 현재 재고: 230개 → 100개 출하 가능 ✅

③ execution/record_finished_out.py 실행
   → 입력:
      product_code   = "FG-1001"
      sales_order_no = "SO-2025-088"
      customer_code  = "CUST-A"
      qty            = 100
      ship_date      = "2025-02-27"
   → FG-1001 재고 230 → 130개
   → 출하 이력 등록

④ execution/generate_stock_report.py 실행
   → Google Sheets "완제품 재고현황" + "출하이력" 탭 업데이트

⑤ 사용자에게 결과 보고:
   "SO-2025-088 출하 처리 완료:
    - FG-1001 100개 / A사 출하 (2025-02-27)
    - 잔여 재고: 130개
    - 출하이력: [Google Sheets 링크]"
```

---

### 시나리오 4: "지금 원부자재 재고 상태 어때?"

```
AI (Orchestration):

① execution/check_material_stock.py --all 실행
② execution/generate_stock_report.py 실행

결과 요약:
"현재 원부자재 재고 현황 (2025-02-27 기준):

 ✅ 정상:  RM-A001 철판 440kg / PKG-001 박스 300ea 외 12종
 ⚠️ 부족:  RM-B003 수지 0L (안전재고 20L 이하)
           RM-C005 도료 8L (안전재고 10L 이하)
 🔴 소진:  없음

전체 재고현황: [Google Sheets 링크]

구매 요청이 필요한 품목 2종에 대해 발주 알림을 보낼까요?"
```

---

## Layer 3: Execution (실행 계층)

---

### `execution/check_material_stock.py`

```python
"""
BOM 전개 후 원부자재/반제품/완제품 재고 충분 여부를 계산합니다.
출력: .tmp/stock_check_{order_no}.json

사용법:
  python check_material_stock.py --product FG-1001 --qty 200
  python check_material_stock.py --type semifinished --code WIP-2001
  python check_material_stock.py --all
"""

import os, json, argparse
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    host   = os.getenv("MES_DB_HOST"),
    user   = os.getenv("MES_DB_USER"),
    passwd = os.getenv("MES_DB_PASS"),
    db     = "mes_db",
    charset= "utf8mb4"
)

def get_bom(product_code: str, qty: int, level: int = 0) -> list[dict]:
    """BOM 재귀 전개 (최대 5레벨)"""
    if level >= 5:
        return []

    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT material_code, material_name, qty_per, unit
            FROM bom
            WHERE product_code = %s AND is_active = 1
        """, (product_code,))
        rows = cur.fetchall()
    conn.close()

    materials = []
    for row in rows:
        needed_qty = row["qty_per"] * qty
        materials.append({
            "material_code": row["material_code"],
            "material_name": row["material_name"],
            "needed_qty":    needed_qty,
            "unit":          row["unit"],
            "level":         level
        })
        # 하위 BOM 재귀 전개
        sub = get_bom(row["material_code"], needed_qty, level + 1)
        materials.extend(sub)

    return materials

def get_current_stock(material_code: str) -> dict:
    """현재 재고, 할당재고, 가용재고 조회"""
    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT current_qty, allocated_qty,
                   (current_qty - allocated_qty) AS available_qty,
                   safety_stock
            FROM material_stock
            WHERE material_code = %s
        """, (material_code,))
        row = cur.fetchone()
    conn.close()
    return row or {"current_qty": 0, "allocated_qty": 0, "available_qty": 0, "safety_stock": 0}

def check_product_materials(product_code: str, qty: int) -> dict:
    """완제품 생산 시 원부자재 충분 여부 확인"""
    bom_items = get_bom(product_code, qty)

    results = []
    has_shortage = False

    for item in bom_items:
        stock  = get_current_stock(item["material_code"])
        available = stock["available_qty"]
        shortage  = max(0, item["needed_qty"] - available)

        if shortage > 0:
            has_shortage = True

        results.append({
            **item,
            "current_qty":   stock["current_qty"],
            "allocated_qty": stock["allocated_qty"],
            "available_qty": available,
            "shortage":      shortage,
            "is_ok":         shortage == 0
        })

    return {"product_code": product_code, "qty": qty,
            "has_shortage": has_shortage, "materials": results}

def check_all_stocks() -> list[dict]:
    """전체 원부자재 안전재고 이하 품목 조회"""
    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT material_code, material_name,
                   current_qty, allocated_qty,
                   (current_qty - allocated_qty) AS available_qty,
                   safety_stock, unit
            FROM material_stock
            WHERE is_active = 1
            ORDER BY (current_qty - allocated_qty) ASC
        """)
        rows = cur.fetchall()
    conn.close()
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", help="완제품 코드")
    parser.add_argument("--qty",     type=int, default=1)
    parser.add_argument("--type",    choices=["raw", "semifinished", "finished"], default="raw")
    parser.add_argument("--code",    help="반제품/완제품 코드 (단건 조회)")
    parser.add_argument("--all",     action="store_true", help="전체 재고 조회")
    parser.add_argument("--order_no",help="생산지시 번호 (출력 파일명용)")
    args = parser.parse_args()

    os.makedirs(".tmp", exist_ok=True)

    if args.all:
        result = check_all_stocks()
        output_path = ".tmp/stock_check_all.json"
    elif args.product:
        result = check_product_materials(args.product, args.qty)
        order_no = args.order_no or "draft"
        output_path = f".tmp/stock_check_{order_no}.json"
    else:
        # 단건 재고 조회
        result = get_current_stock(args.code)
        output_path = f".tmp/stock_check_{args.code}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"재고 확인 완료: {output_path}")

    # 부족 품목 콘솔 출력
    if isinstance(result, dict) and result.get("has_shortage"):
        print("\n⚠️ 부족 품목:")
        for m in result["materials"]:
            if not m["is_ok"]:
                print(f"  {m['material_code']} {m['material_name']}: "
                      f"필요 {m['needed_qty']}{m['unit']} / 가용 {m['available_qty']}{m['unit']} "
                      f"(부족 {m['shortage']}{m['unit']})")

if __name__ == "__main__":
    main()
```

---

### `execution/deduct_material_stock.py`

```python
"""
생산지시 확정 시 원부자재 재고를 가용재고 → 할당재고로 이동합니다.
(실제 차감은 반제품/완제품 입고 시 처리)

사용법:
  python deduct_material_stock.py --order_no WO-20250227-0041
"""

import os, json, argparse
import pymysql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    host=os.getenv("MES_DB_HOST"), user=os.getenv("MES_DB_USER"),
    passwd=os.getenv("MES_DB_PASS"), db="mes_db", charset="utf8mb4"
)

def allocate_materials(order_no: str, force: bool = False):
    """BOM 기준으로 원부자재 할당 처리"""
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # 생산지시 기준 필요 자재 조회
            cur.execute("""
                SELECT b.material_code, b.qty_per * po.qty AS needed_qty, b.unit
                FROM production_orders po
                JOIN bom b ON b.product_code = po.product_code
                WHERE po.order_no = %s AND po.status = 'CONFIRMED'
            """, (order_no,))
            materials = cur.fetchall()

            results = []
            for mat in materials:
                # 가용재고 확인
                cur.execute("""
                    SELECT current_qty, allocated_qty
                    FROM material_stock
                    WHERE material_code = %s
                    FOR UPDATE
                """, (mat["material_code"],))
                stock = cur.fetchone()
                available = stock["current_qty"] - stock["allocated_qty"]
                actual_alloc = min(available, mat["needed_qty"])  # 가용분까지만 할당

                # 할당재고 증가
                cur.execute("""
                    UPDATE material_stock
                    SET allocated_qty = allocated_qty + %s,
                        updated_at    = %s
                    WHERE material_code = %s
                """, (actual_alloc, datetime.now(), mat["material_code"]))

                # 이력 기록
                cur.execute("""
                    INSERT INTO material_transactions
                    (material_code, trans_type, qty, order_no, note, created_at)
                    VALUES (%s, 'ALLOCATE', %s, %s, '생산지시 자재할당', %s)
                """, (mat["material_code"], actual_alloc, order_no, datetime.now()))

                shortage = mat["needed_qty"] - actual_alloc
                results.append({
                    "material_code": mat["material_code"],
                    "needed": mat["needed_qty"],
                    "allocated": actual_alloc,
                    "shortage": shortage
                })
                print(f"  {mat['material_code']}: 할당 {actual_alloc}{mat['unit']}"
                      + (f" / 부족 {shortage}{mat['unit']} ⚠️" if shortage > 0 else " ✅"))

        conn.commit()
        print(f"\n할당 완료: {order_no}")
        return results

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--order_no", required=True)
    parser.add_argument("--force", action="store_true", help="재고 부족 시에도 강제 진행")
    args = parser.parse_args()
    allocate_materials(args.order_no, args.force)

if __name__ == "__main__":
    main()
```

---

### `execution/record_semifinished_in.py`

```python
"""
반제품 입고를 MES DB에 등록합니다.
사용법:
  python record_semifinished_in.py \
    --code WIP-2001 --order_no WO-20250227-0041 \
    --qty_produced 150 --qty_defect 3 --work_center LINE-01
"""

import os, argparse
import pymysql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    host=os.getenv("MES_DB_HOST"), user=os.getenv("MES_DB_USER"),
    passwd=os.getenv("MES_DB_PASS"), db="mes_db", charset="utf8mb4"
)

def record_in(code, order_no, qty_produced, qty_defect, work_center):
    qty_good = qty_produced - qty_defect
    defect_rate = round(qty_defect / qty_produced * 100, 2) if qty_produced > 0 else 0

    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            # 반제품 재고 증가
            cur.execute("""
                INSERT INTO semifinished_stock (material_code, current_qty, updated_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    current_qty = current_qty + %s,
                    updated_at  = %s
            """, (code, qty_good, datetime.now(), qty_good, datetime.now()))

            # 입고 이력
            cur.execute("""
                INSERT INTO semifinished_transactions
                (material_code, trans_type, qty_good, qty_defect,
                 defect_rate, order_no, work_center, created_at)
                VALUES (%s, 'IN', %s, %s, %s, %s, %s, %s)
            """, (code, qty_good, qty_defect, defect_rate,
                  order_no, work_center, datetime.now()))

            # 생산지시 진행 이력 업데이트
            cur.execute("""
                UPDATE production_orders
                SET qty_completed = qty_completed + %s, updated_at = %s
                WHERE order_no = %s
            """, (qty_good, datetime.now(), order_no))

        conn.commit()
        print(f"반제품 입고 완료: {code} 양품 {qty_good}ea / 불량 {qty_defect}ea ({defect_rate}%)")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code",         required=True)
    parser.add_argument("--order_no",     required=True)
    parser.add_argument("--qty_produced", required=True, type=int)
    parser.add_argument("--qty_defect",   required=True, type=int)
    parser.add_argument("--work_center",  required=True)
    args = parser.parse_args()
    record_in(args.code, args.order_no, args.qty_produced, args.qty_defect, args.work_center)

if __name__ == "__main__":
    main()
```

---

### `execution/generate_stock_report.py`

```python
"""
원부자재 / 반제품 / 완제품 재고 현황을 Google Sheets에 업데이트합니다.
시트 구성:
  - 원부자재 재고현황
  - 반제품 재고현황
  - 완제품 재고현황
  - 출하이력

사용법:
  python generate_stock_report.py --type all
  python generate_stock_report.py --type raw
  python generate_stock_report.py --type finished --include_history
"""

import os, argparse
import pymysql
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES      = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID    = os.getenv("GOOGLE_SHEET_ID_STOCK")
CREDS_PATH  = "credentials.json"

DB = dict(
    host=os.getenv("MES_DB_HOST"), user=os.getenv("MES_DB_USER"),
    passwd=os.getenv("MES_DB_PASS"), db="mes_db", charset="utf8mb4"
)

def get_sheet(tab_name: str):
    creds  = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).worksheet(tab_name)

def update_raw_materials():
    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT material_code, material_name, unit,
                   current_qty, allocated_qty,
                   (current_qty - allocated_qty) AS available_qty,
                   safety_stock,
                   CASE
                     WHEN (current_qty - allocated_qty) = 0 THEN '🔴 소진'
                     WHEN (current_qty - allocated_qty) <= safety_stock THEN '⚠️ 부족'
                     ELSE '✅ 정상'
                   END AS status
            FROM material_stock
            WHERE is_active = 1
            ORDER BY status DESC, material_code
        """)
        rows = cur.fetchall()
    conn.close()

    sheet = get_sheet("원부자재 재고현황")
    sheet.clear()
    headers = ["품목코드", "품목명", "단위", "현재고", "할당재고", "가용재고", "안전재고", "상태", "업데이트일시"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    data = [headers] + [[
        r["material_code"], r["material_name"], r["unit"],
        r["current_qty"], r["allocated_qty"], r["available_qty"],
        r["safety_stock"], r["status"], now_str
    ] for r in rows]

    sheet.update("A1", data)
    print(f"원부자재 재고현황 업데이트 완료: {len(rows)}건")

def update_finished_goods(include_history: bool = False):
    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT product_code, product_name, current_qty, unit, updated_at
            FROM finished_stock
            WHERE is_active = 1
            ORDER BY product_code
        """)
        rows = cur.fetchall()
    conn.close()

    sheet = get_sheet("완제품 재고현황")
    sheet.clear()
    headers = ["품목코드", "품목명", "현재고", "단위", "최종갱신"]
    data = [headers] + [[
        r["product_code"], r["product_name"], r["current_qty"],
        r["unit"], str(r["updated_at"])
    ] for r in rows]
    sheet.update("A1", data)
    print(f"완제품 재고현황 업데이트 완료: {len(rows)}건")

    if include_history:
        _update_shipping_history()

def _update_shipping_history():
    conn = pymysql.connect(**DB)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT ft.product_code, fs.product_name, ft.qty,
                   ft.sales_order_no, ft.customer_code, ft.ship_date, ft.created_at
            FROM finished_transactions ft
            JOIN finished_stock fs ON fs.product_code = ft.product_code
            WHERE ft.trans_type = 'OUT'
            ORDER BY ft.ship_date DESC
            LIMIT 500
        """)
        rows = cur.fetchall()
    conn.close()

    sheet = get_sheet("출하이력")
    sheet.clear()
    headers = ["품목코드", "품목명", "출하수량", "수주번호", "고객코드", "출하일", "등록일시"]
    data = [headers] + [[
        r["product_code"], r["product_name"], r["qty"],
        r["sales_order_no"], r["customer_code"],
        str(r["ship_date"]), str(r["created_at"])
    ] for r in rows]
    sheet.update("A1", data)
    print(f"출하이력 업데이트 완료: {len(rows)}건")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["all", "raw", "semifinished", "finished"], default="all")
    parser.add_argument("--include_history", action="store_true")
    args = parser.parse_args()

    if args.type in ("all", "raw"):
        update_raw_materials()
    if args.type in ("all", "finished"):
        update_finished_goods(include_history=args.include_history)

if __name__ == "__main__":
    main()
```

---

## 🔄 Self-Annealing 실제 예시

### 상황: BOM 전개 시 순환 참조 발생

```
[오류]
execution/check_material_stock.py 실행 중 오류:
  RecursionError: maximum recursion depth exceeded
  → WIP-3002의 BOM이 WIP-2001을 참조하고,
    WIP-2001의 BOM이 다시 WIP-3002를 참조 (순환)

[AI Self-Annealing 과정]

① 오류 분석
   - BOM 순환 참조: WIP-2001 ↔ WIP-3002
   - 현재 코드에 순환 감지 로직 없음

② 스크립트 수정
   - get_bom() 함수에 visited: set 파라미터 추가
   - 이미 방문한 material_code 재방문 시 조기 종료

③ 테스트
   - 동일 BOM으로 재실행 → 순환 감지 후 경고 출력, 정상 종료 ✅

④ directive 업데이트 (directives/create_production_order.md)
   추가: "BOM 순환 참조 발생 시 스크립트가 자동 감지하여 경고 출력.
         해당 품목 BOM 설계 오류이므로 생산기술팀 BOM 수정 요청 필요."
```

---

## 📊 전체 흐름 요약

```
[생산지시 작성]
 사용자 → AI → BOM 전개 & 재고 확인 → 부족 시 사용자 확인
             → 생산지시 DB 등록 → 원부자재 할당 → Sheets 업데이트

[반제품 입고]
 생산 완료 → AI → 양품/불량 수량 확인 → 반제품 재고 증가
                → 생산지시 진행률 업데이트 → Sheets 업데이트

[반제품 출고]
 다음 공정 투입 → AI → 반제품 재고 확인 → 출고 처리 → Sheets 업데이트

[완제품 입고]
 최종 공정 완료 → AI → 검사 결과 확인 → 완제품 재고 증가
                     → 생산지시 COMPLETED → Sheets 업데이트

[완제품 출고 (출하)]
 수주 출하 → AI → 완제품 재고 확인 → 출고 처리
                → 출하이력 기록 → Sheets 업데이트
```

---

## ✅ 핵심 원칙 적용 확인

| 원칙                      | 적용 내용                                                             |
| ------------------------- | --------------------------------------------------------------------- |
| **AI는 의사결정만** | 재고 부족 시 사용자 확인 요청, 스크립트 실행 순서 결정                |
| **결정론적 코드**   | BOM 전개, 재고 차감, DB 등록 모두 Python 스크립트 처리                |
| **Self-Annealing**  | BOM 순환 참조, ERP 타임아웃 등 오류 → 자동 복구 + directive 업데이트 |
| **로컬은 임시**     | `.tmp/`에 BOM 전개·재고 체크 결과 저장, 최종은 Google Sheets       |
| **Directive 개선**  | API 제약, BOM 레벨 한계, 월말 실사 예외 등 지속 반영                  |
