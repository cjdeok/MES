# 로그인 기능 구현 계획

사용자 아이콘(헤더 우측 'U' 표시)에 실제 로그인 기능을 연동하여, 인증된 사용자만 시스템을 이용하거나 사용자별 프로필을 관리할 수 있도록 합니다.

## User Review Required

> [!IMPORTANT]
> **인증 방식 결정**: 현재 Supabase를 DB로 사용 중이므로, Supabase Auth(이메일/비밀번호)를 사용하는 방향으로 제안합니다. 별도의 관리자 계정 생성이 필요한지 확인 부탁드립니다.

> [!TIP]
> **보안**: 초기 단계에서는 모든 페이지에 접근 제한을 걸기보다, 로그인 상태에 따라 헤더의 UI가 변경되고 특정 기능(데이터 수정/삭제 등)에 권한을 체크하는 방식으로 시작하는 것이 좋습니다.

## Proposed Changes

### 1. 인증 인프라 및 백엔드 설정

#### [MODIFY] [app.py](file:///c:/Users/ENS-1000/Documents/Antigravity/MES/web/app.py)
- Flask `session` 설정을 위한 `SECRET_KEY` 추가 (환경 변수 활용).
- Supabase Auth를 이용한 로그인/로그아웃 API 엔드포인트 구현:
  - `POST /api/auth/login`: 이메일과 비밀번호를 받아 Supabase 인증 후 세션 저장.
  - `POST /api/auth/logout`: Flask 세션 클리어.
  - `GET /api/auth/me`: 세션 정보를 기반으로 현재 사용자 정보 반환.
- `context_processor`를 추가하여 모든 템플릿에서 `current_user` 변수에 접근 가능하도록 설정.

---

### 2. 프론트엔드 UI/UX 구현

#### [MODIFY] [base.html](file:///c:/Users/ENS-1000/Documents/Antigravity/MES/web/templates/base.html)
- **헤더 사용자 영역 수정**:
  - 로그인 전: 'U' 아이콘 클릭 시 로그인 모달 표시.
  - 로그인 후: 사용자 이니셜 또는 프로필 아이콘 표시 + 클릭 시 드롭다운(내 정보, 로그아웃) 표시.
- **로그인 모달 추가**: Kinetic Light 디자인 시스템(Tailwind CSS)을 적용한 깔끔한 로그인 폼 구현.
  - 이메일, 비밀번호 입력 필드 및 로그인 버튼.
  - 에러 메시지 표시 영역.

#### [NEW] [auth.js](file:///c:/Users/ENS-1000/Documents/Antigravity/MES/web/static/js/auth.js)
- 로그인 모달 오픈/클로즈 제어.
- AJAX를 이용한 로그인 요청 처리 및 페이지 새로고침/UI 업데이트 로직.

---

### 3. 환경 설정

#### [MODIFY] [.env](file:///c:/Users/ENS-1000/Documents/Antigravity/MES/.env)
- `FLASK_SECRET_KEY` 추가 (세션 암호화용).

## Open Questions

- **회원가입 기능**: 사용자가 직접 가입할 수 있게 할까요, 아니면 관리자가 Supabase 콘솔에서 생성한 계정으로만 로그인하게 할까요?
- **소셜 로그인**: 구글이나 카카오 등 소셜 로그인 연동이 필요한가요? (초기에는 이메일/비밀번호 방식을 권장합니다.)

## Verification Plan

### Automated Tests
- `pytest`를 사용하여 `/api/auth/login` 및 `logout` 엔드포인트의 정상 작동 여부 확인 (Mocking Supabase).

### Manual Verification
1. 브라우저에서 'U' 아이콘 클릭 시 로그인 모달이 정상적으로 뜨는지 확인.
2. 잘못된 정보 입력 시 에러 메시지가 출력되는지 확인.
3. 로그인 성공 후 헤더의 'U'가 사용자 정보로 바뀌는지 확인.
4. 로그아웃 버튼 클릭 시 정상적으로 로그아웃되고 초기 상태로 돌아가는지 확인.
