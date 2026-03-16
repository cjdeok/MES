-- purchase_info 테이블 생성 SQL
CREATE TABLE IF NOT EXISTS purchase_info (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    작성일자 DATE,
    no TEXT,
    문서번호 TEXT,
    발주번호 TEXT,
    작성자 TEXT,
    요청팀 TEXT,
    구분 TEXT,
    코드번호 TEXT,
    순번 TEXT,
    품명1 TEXT,
    품명2 TEXT,
    cat_no TEXT,
    제조사 TEXT,
    구매처 TEXT,
    납기일 TEXT,
    규격 TEXT,
    단위 TEXT,
    수량 REAL,
    단가 REAL,
    금액 REAL,
    포장단위 TEXT,
    관리단위 TEXT,
    실단가 REAL,
    실입고량 REAL,
    담당자 TEXT,
    연락처 TEXT,
    email TEXT,
    지불방법 TEXT
);

-- 인덱스 추가 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_purchase_info_date ON purchase_info(작성일자);
CREATE INDEX IF NOT EXISTS idx_purchase_info_code ON purchase_info(코드번호);
CREATE INDEX IF NOT EXISTS idx_purchase_info_vendor ON purchase_info(구매처);
