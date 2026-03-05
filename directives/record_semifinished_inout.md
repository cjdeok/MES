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
   → 로컬 "반제품 재고현황" CSV 업데이트

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
