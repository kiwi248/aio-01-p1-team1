# Codex 작업 인수인계서

마지막 확인일: 2026-08-08 (Asia/Seoul)

## 1. 문서의 목적

이 문서는 다음 목적으로 작성한 프로젝트 통합 인수인계서다.

- Git 충돌 발생 시 변경 이유와 순서를 확인한다.
- 다른 데스크탑이나 Codex 대화창에 현재 상태를 전달한다.
- 코드만 보고 알기 어려운 구현 이유, 보류 사항, 테스트 상태를 남긴다.
- 후속 유지보수 시 Codex가 기존 결정을 정확히 이해하게 한다.

새 Codex 대화를 시작할 때는 다음처럼 요청한다.

> `CODEX_HANDOFF.md`, `git status`, 최근 커밋을 먼저 확인하고 현재 상태를 요약한 다음 작업을 이어가 줘.

## 2. 협업 방식

사용자는 초보 프로그래머이며 코드를 직접 복사하여 붙여넣고 확인하는 방식으로 작업한다.

반드시 다음 방식을 지킨다.

- 코드를 임의로 수정하기 전에 사용자에게 수정 방법을 먼저 안내한다.
- 매번 `파일명 + 시작 줄 + 끝 줄 + 교체 범위`를 정확히 알려준다.
- 안내 전에 실제 파일의 현재 줄 번호를 다시 확인한다.
- 한 번에 너무 많은 파일을 수정하지 않고 단계별로 진행한다.
- 발표할 때 설명하기 어려운 긴 코드보다 짧고 직관적인 코드를 우선한다.
- 사용자가 수정했다고 하면 다음 단계 전에 실제 파일과 Python 문법을 확인한다.
- 기존 코드와 사용자의 변경을 임의로 되돌리지 않는다.

## 3. 프로젝트 구조

- 프로젝트: 공공임대 및 분양 청약 통합 안내 서비스
- 유저 프런트엔드: Streamlit, `FE_User`
- 관리자 프런트엔드: Streamlit, `FE_Admin`
- 백엔드: FastAPI, `BE`
- 인증: Supabase Auth
- DB: Supabase Postgres

주요 파일:

- `FE_User/app.py`: 유저 페이지 등록과 내비게이션
- `FE_User/app_pages/00_login.py`: 로그인
- `FE_User/app_pages/01_signup.py`: 회원가입
- `FE_User/app_pages/04_mypage.py`: 프로필, 비밀번호, 즐겨찾기
- `FE_User/core/auth.py`: Supabase Auth 회원가입/로그인/비밀번호
- `FE_User/core/supabase_client.py`: 프런트엔드 Supabase anon 클라이언트
- `BE/app/schemas/profile_schema.py`: 프로필 입력/응답 검증
- `BE/app/services/profile_service.py`: 프로필 DB 조회/수정
- `BE/sql/profiles.sql`: 추가 프로필 열과 회원가입 트리거

## 4. 작업 이력

### 2026-08-06: 로그인 화면 초기 개선

- 이메일 아이디와 도메인 입력을 분리했다.
- 로그인 버튼과 회원가입 페이지 링크를 정리했다.
- 중앙 배치된 로그인 폼을 구성했다.

관련 커밋:

- `0ec3bd6` - `loginpage working`

### 2026-08-07: 회원가입 및 프로필 DB 확장

- 약관 전체 동의와 필수 약관 동의를 구현했다.
- 회원가입 이메일 아이디와 도메인 입력을 분리했다.
- 휴대번호, 생년월일, 관심 분야 입력을 추가했다.
- 비밀번호 6자 이상, 비밀번호 확인, 휴대번호 숫자/길이, 생년월일 유효성 검사를 추가했다.
- `profiles` 테이블에 `phone`, `birth_date`, `interests` 열을 추가하는 SQL을 작성했다.
- Supabase Auth 사용자 생성 시 metadata를 `profiles`에 넣는 `handle_new_user()` 트리거를 확장했다.

관심 분야 목록:

- 입찰공고
- 분양주택
- 임대주택
- 토지분양
- 상가공장
- 장기전세
- 보상이주
- 채용공고
- 주택관리

관련 커밋:

- `5c9a03d` - `0807pm`
- `2f6edbf` - `0807`
- `dc15c30` - `0807-1`

주의: `BE/sql/profiles.sql`이 실제 Supabase SQL Editor에서 실행되었는지 새 환경에서 확인한다.

### 2026-08-08: 마이페이지 및 로그인 실패 안내

마이페이지에서 다음 정보를 수정하도록 확장했다.

- ID: 로그인 이메일을 표시하고 `disabled=True`로 수정 불가
- 성함: `profiles.nickname` 수정, 중복 허용
- 휴대번호: `profiles.phone` 수정, 다른 사용자와 중복 불가
- 관심 분야: `profiles.interests` 수정
- 비밀번호: Supabase Auth에서 변경

관심 분야는 9개 체크박스를 `st.columns(3)`에 3행 x 3열로 배치했다.

백엔드 변경:

- `ProfileUpdate`, `ProfilePublic`에 `phone`, `interests`를 추가했다.
- 휴대번호는 `010-1234-5678` 형식을 검증한다.
- `profile_update()`가 `nickname`, `phone`, `interests`를 함께 저장한다.
- 다른 사용자의 휴대번호와 같으면 `409`와 `이미 사용 중인 휴대번호입니다.`를 반환한다.
- 성함 중복 검사는 요구사항에서 제외했다.

비밀번호 변경:

- 로그인 성공 시 Supabase `access_token`, `refresh_token`을 Streamlit `session_state`에 보관한다.
- 변경 시 토큰으로 Supabase 세션을 복원한 후 `supabase.auth.update_user()`를 호출한다.
- 비밀번호 원문은 파일, `profiles`, `session_state`에 영구 저장하지 않는다.
- 로그아웃 시 로그인 정보와 토큰을 빈 값으로 초기화한다.
- 새 비밀번호는 6자 이상이어야 하며 확인과 일치해야 한다.

로그인 실패 안내:

- Supabase의 `Invalid login credentials`를 그대로 노출하지 않는다.
- `로그인 정보를 다시 확인해 주세요. (401)`로 표시한다.
- 자체 코드 `AUTH-001` 대신 기존 API와 같은 HTTP 상태 코드를 사용한다.
- `login_area.error()`로 로그인 폼과 오류창 너비를 맞춴다.

관련 커밋:

- `d8ab012` - `0808`
- `31cd58a` - `0808-1`

## 5. 현재 구현 결정

### 프로필

- ID는 로그인 이메일이며 마이페이지에서 수정할 수 없다.
- 성함은 중복을 허용한다.
- 휴대번호는 다른 사용자와 중복을 허용하지 않는다.
- 성함, 휴대번호, 관심 분야, 비밀번호 중 필요한 항목만 변경할 수 있어야 한다.
- 비밀번호 칸이 비어 있으면 비밀번호는 변경하지 않는다.
- 아무것도 바꾸지 않았으면 `변경된 내용이 없습니다.`를 표시한다.

### 완료 안내

사용자의 최종 요구는 수정 항목을 나열하지 않고, 어떤 항목을 변경하든 다음 한 문구만 `st.info()`로 표시하는 것이다.

```text
수정이 완료되었습니다.
```

현재 `04_mypage.py`는 아직 `messages`를 만들어 `프로필을 수정했습니다.` 등으로 표시하고 있다. 후속 작업에서 위 단일 문구로 단순화하고, 관심 분야만 수정했을 때도 안내가 표시되는지 확인한다.

### 회원탈퇴

회원탈퇴는 구현하지 않았으며 팀 논의 전까지 보류한다.

논의할 사항:

- 현재 비밀번호 재확인 여부
- 즉시 완전 삭제와 소프트 삭제 중 선택
- 복구 정책
- Supabase Storage 소유 파일 처리

Auth 사용자 삭제는 service role 권한으로 백엔드에서 수행해야 한다. `profiles.id`, `favorites.user_id`는 `auth.users(id) ON DELETE CASCADE`로 설정되어 있다.

## 6. 알려진 보안 보완점

- 프로필 API가 URL의 `user_id`를 기준으로 조회/수정한다.
- 백엔드는 요청의 Supabase access token으로 요청자와 `user_id`가 같은지 아직 검증하지 않는다.
- 운영 전에 Bearer token 전달과 백엔드 사용자 검증을 권장한다.
- `SUPABASE_SERVICE_ROLE_KEY`는 백엔드에만 두고 프런트엔드에 노출하지 않는다.
- 현재 휴대번호 중복 검사는 마이페이지 백엔드 로직에 있다. DB unique 제약과 회원가입 단계의 정책은 팀 확인이 필요하다.

## 7. 테스트 체크리스트

### 회원가입

- [ ] 필수 약관 미동의 시 가입 차단
- [ ] 휴대번호, 생년월일, 관심 분야 저장
- [ ] 회원가입 후 `profiles` 트리거 생성

### 로그인

- [ ] 정상 로그인
- [ ] 잘못된 이메일/비밀번호 시 `로그인 정보를 다시 확인해 주세요. (401)`
- [ ] 오류창이 로그인 폼과 같은 너비로 표시

### 마이페이지

- [ ] 성함만 수정
- [ ] 휴대번호만 수정
- [ ] 관심 분야만 수정하고 `수정이 완료되었습니다.` 확인
- [ ] 비밀번호만 수정
- [ ] 여러 항목 함께 수정
- [ ] 변경 내용이 없을 때 경고
- [ ] 다른 사용자와 휴대번호가 같을 때 `409`
- [ ] 비밀번호 6자 미만/확인 불일치
- [ ] 비밀번호 변경 후 새 비밀번호로 재로그인

## 8. 환경 설정

### FE_User

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
```

### BE

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

실제 URL, key, 비밀번호, access token, refresh token은 문서에 기록하지 않는다.

## 9. 실행 명령

백엔드:

```bash
cd BE
uvicorn app.main:app --reload
```

유저 프런트엔드:

```bash
cd FE_User
source .venv/bin/activate
streamlit run app.py
```

## 10. 다음 작업 우선순위

1. `git status --short`와 실제 파일을 확인한다.
2. 마이페이지 완료 안내를 `수정이 완료되었습니다.` 하나로 단순화한다.
3. 관심 분야만 변경했을 때도 안내가 표시되는지 확인한다.
4. 로그인 실패 문구 `(401)`과 오류창 너비를 실행 화면에서 확인한다.
5. 마이페이지 항목별 수정을 실제 Supabase 환경에서 테스트한다.
6. 회원탈퇴는 팀 논의 전까지 구현하지 않는다.

## 11. Git 및 문서 관리

- 이 문서는 다른 데스크탑에서도 사용해야 하므로 Git에 커밋한다.
- 비밀값은 절대 기록하지 않는다.
- 작업 종료 시 완료/미완료/보류 상태를 갱신한다.
- Git diff를 그대로 복사하지 않고 변경 이유와 주의사항을 중심으로 기록한다.
- 새 환경에서 문서와 코드가 다르면 실제 코드와 Git 기록을 우선하고 문서를 갱신한다.

## 12. 로그인 HTML 미리보기

`.codex/visualizations/2026/08/07/login-layout-preview.html`은 2026-08-07 로그인 화면 배치를 확인하기 위해 만든 정적 HTML 시안이다.

- 실제 Streamlit 앱에서 사용하지 않는다.
- 현재 기능과 연결되지 않는다.
- 과거 UI 기록이 필요하면 보관하고, 불필요하면 삭제해도 앱 기능에 영향이 없다.
