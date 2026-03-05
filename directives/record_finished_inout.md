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
   - HOLD: 콘솔 알림 후 대기 (사용자 승인 필요)
   - FAIL: 불량 처리 지시 후 중단

2. execution/record_finished_in.py
   → 완제품 재고 증가
   → 생산지시 상태: IN_PROGRESS → COMPLETED

3. execution/generate_stock_report.py
   → 로컬 "완제품 재고현황" CSV 업데이트

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
   → 로컬 "완제품 재고현황" 및 "출하이력" CSV 업데이트

## 엣지 케이스
- 부분 출하 허용: qty < 수주 수량인 경우 잔량 처리 방식 사용자 확인
- 재고 부족 시: 생산지시 가능 여부 조회 후 예상 가용일 안내
