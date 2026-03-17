-- =============================================
-- Supabase에서 실행할 테이블 생성 SQL
-- Supabase Dashboard -> SQL Editor -> New Query 로 실행하세요
-- =============================================

-- 1. 원자재 트랜잭션
CREATE TABLE IF NOT EXISTS raw_materials (
    id SERIAL PRIMARY KEY,
    product_name TEXT,
    item_code TEXT,
    lot_no TEXT,
    transaction_type TEXT,
    transaction_date TEXT,
    purpose TEXT,
    quantity REAL
);

-- 2. 원료 정보
CREATE TABLE IF NOT EXISTS material_info (
    id SERIAL PRIMARY KEY,
    item_code TEXT,
    product_name TEXT,
    cat_no TEXT,
    lot_no TEXT,
    purchase_qty REAL,
    manufacturer TEXT,
    vendor TEXT,
    receive_date TEXT,
    qc_date TEXT,
    expire_date TEXT,
    po_no TEXT
);

-- 3. Kit BOM (제품 구성)
CREATE TABLE IF NOT EXISTS kit_bom (
    id SERIAL PRIMARY KEY,
    material_code TEXT,
    material_name TEXT,
    kit_qty INTEGER,
    usage_qty REAL
);

-- 4. 완제품 입출고
CREATE TABLE IF NOT EXISTS finished_products (
    id SERIAL PRIMARY KEY,
    product_code TEXT,
    product_name TEXT,
    lot_no TEXT,
    transaction_type TEXT,
    transaction_date TEXT,
    expire_date TEXT,
    quantity_kit REAL,
    destination TEXT,
    qc_info TEXT,
    remark TEXT
);
-- 5. 설비 관리 (보정 버전)
DROP TABLE IF EXISTS facilities;
CREATE TABLE facilities (
    id SERIAL PRIMARY KEY,
    management_team TEXT,
    location TEXT,
    status TEXT,
    facility_no TEXT,
    facility_name TEXT,
    equipment_class TEXT,
    facility_grade TEXT,
    calibration TEXT,
    validation TEXT,
    department TEXT,
    manager_primary TEXT,
    manager_secondary TEXT,
    specification TEXT,
    manufacturer TEXT,
    serial_no TEXT,
    supplier TEXT,
    as_contact TEXT,
    purchase_date TEXT,
    purchase_price BIGINT,
    useful_life INTEGER
);