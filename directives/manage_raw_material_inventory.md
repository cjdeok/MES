# 원부자재 재고 관리 SOP

## 목적
원부자재(원자재·부자재·부품) 입고/출고/재고 현황을 관리하고
안전재고 이하 품목에 대해 콘솔 알림을 발송한다.

## 주요 작업 유형
| 작업 | 트리거 | 관련 스크립트 |
|------|--------|--------------|
| 입고 등록 | 구매 입고 완료 | check_material_stock.py → deduct_material_stock.py |
| 출고 등록 | 생산지시 확정 | deduct_material_stock.py |
| 재고 조회 | 사용자 요청·주기적 실행 | check_material_stock.py → generate_stock_report.py (CSV 저장) |
| 안전재고 알림 | 재고 조회 후 임계값 비교 | 콘솔 알림 출력 |

## 입력 (입고 시)
- material_code  : 원부자재 코드
- qty            : 입고 수량
- unit           : 단위 (kg / ea / L / m 등)
- lot_no         : 입고 LOT 번호
- supplier_code  : 공급업체 코드
- po_no          : 구매발주 번호

## 재고 알림 기준 (콘솔 출력)
- 안전재고 이하: 가용재고 부족 경고 출력
- 재고 0 (소진): 재고 소진 알림 출력
- 유효기간 30일 이내 (원자재): 품질 검토 알림 출력

## 학습된 제약사항
- LOT 추적 필수 품목: 화학원료(CHM-*), 포장재(PKG-*) → lot_no 누락 시 입고 거부
- 단위 환산 필요 품목 코드 목록: /execution/unit_conversion_map.json 참조
- 월말 재고실사 기간(매월 마지막 날) 중 출고 처리는 실사 완료 후 반영
