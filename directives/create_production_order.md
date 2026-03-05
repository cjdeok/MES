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
   → 차감 후 원부자재 재고 현황 로컬 CSV 업데이트

## 출력
- MES DB: 생산지시서 레코드 생성 (status=CONFIRMED)
- 로컬 보고서: .tmp/ 폴더 내 파일 확인
- 콘솔 알림: 생산지시 확정 내역 출력

## 엣지 케이스
- BOM 미등록 품목: 사용자에게 BOM 등록 요청 후 중단
- 재고 부족 시 강제 진행 요청: 사용자 명시적 승인 필요 (스크립트 --force 플래그)
- 동일 품목 중복 지시: 기존 지시 번호 조회 후 사용자 확인

## 학습된 제약사항
- BOM 전개 레벨은 최대 5단계 (그 이상은 ERP 직접 조회 필요)
- 재고 차감은 지시 확정 시점 기준 (DRAFT 상태에서는 차감 안 함)
- ERP 연동 시 재고 동기화 딜레이 최대 10분 발생 가능
