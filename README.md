# 공공임대 및 분양 청약 통합 안내 서비스

공공임대·분양 청약 정보를 한곳에 모아 보여주는 안내 서비스의 MVP(프로토타입)입니다.
AI 기능은 아직 포함되어 있지 않습니다.

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [주요 기능](#2-주요-기능)
3. [기술 스택](#3-기술-스택)
4. [시작하기 (Getting Started)](#4-시작하기-getting-started)

---

## 1. 프로젝트 소개

관리자는 청약 공고를 등록·관리하고, 유저는 공고를 조회·검색하며 마음에 드는 공고를 즐겨찾기에 담아 mypage에서 관리할 수 있는 서비스입니다.

- 백엔드 API 서버(`BE`) 하나에, 관리자용 화면(`FE_Admin`)과 유저용 화면(`FE_User`) 두 개의 Streamlit 프런트엔드가 붙는 구조입니다.
- 데이터는 Supabase(PostgreSQL)에 저장하며, 유저 회원가입·로그인은 Supabase Auth(현재는 이메일 방식, 추후 Kakao/Google OAuth 추가 예정)에 맡깁니다.
- 관리자 계정은 자체 회원가입 없이 중앙에서 미리 발급합니다.

### 폴더 구조

```text
aio-01-p1-team1/
├─ BE/          # FastAPI 백엔드 (Supabase 연동)
├─ FE_Admin/    # 관리자용 Streamlit 화면
└─ FE_User/     # 유저용 Streamlit 화면
```

## 2. 주요 기능

### 관리자 페이지 (FE_Admin)

- 관리자 로그인 (계정은 중앙에서 미리 발급)
- 청약정보 등록
- 청약정보 전체 조회 / 조건검색(대상, 위치, 금액, 자격조건)
- 청약정보 삭제
- 유저가 즐겨찾기한 청약정보를 즐겨찾기 많은 순으로 조회
- 어떤 유저가 어떤 청약정보를 즐겨찾기했는지 조회

### 유저 페이지 (FE_User)

- 회원가입 / 로그인 (Supabase Auth, 현재는 이메일 방식)
- 청약정보 조회 / 조건검색(최신순, 대상, 위치, 금액, 자격조건)
- mypage에서 닉네임 수정
- mypage에서 청약정보 즐겨찾기 생성 / 조회 / 삭제

## 3. 기술 스택

| 구분 | 기술 |
| --- | --- |
| 백엔드 | Python, FastAPI, Pydantic, Uvicorn |
| 프런트엔드 | Streamlit, httpx |
| 데이터베이스 / 인증 | Supabase (PostgreSQL, Supabase Auth) |
| 데이터 연동 | supabase-py |

## 4. 시작하기 (Getting Started)

### 사전 준비

- Python 3.11 이상
- Supabase 프로젝트 (URL, Service Role Key, Anon Key)

### 4-1. 데이터베이스 준비

Supabase SQL Editor에서 [`BE/sql/schema.sql`](BE/sql/schema.sql)을 실행해 테이블(`profiles`, `admins`, `listings`, `favorites`)과 트리거를 생성합니다.

### 4-2. 백엔드(BE) 설치 및 실행

```bash
cd BE
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`BE/.env` 파일에 Supabase 접속 정보를 채웁니다.

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

관리자 계정을 생성합니다. (관리자는 별도 회원가입 API가 없어 스크립트로 직접 생성합니다)

```bash
python scripts/create_admin.py <아이디> <비밀번호>
```

서버를 실행합니다.

```bash
uvicorn app.main:app --reload
```

- API 문서: http://127.0.0.1:8000/docs

### 4-3. 관리자 프런트엔드(FE_Admin) 설치 및 실행

```bash
cd FE_Admin
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

BE 서버(`http://127.0.0.1:8000`)가 먼저 실행되어 있어야 합니다.

> **관리자 로그인 유지에 대한 안내**
>
> 관리자 로그인 상태는 브라우저 Session Storage에 저장했다가 새로고침 후 되살립니다.
> 탭을 닫으면 사라지며, 비밀번호는 저장하지 않습니다.
>
> 이 방식은 **화면 상태를 되살리는 편의 기능이며 실제 관리자 인증 수단이 아닙니다.**
> 저장된 값은 사용자가 브라우저 개발자 도구에서 바꿀 수 있어, 비밀번호 없이도
> 관리자 화면을 열 수 있습니다. 현재 `/admin/*` API에도 인증이 없습니다.
>
> 외부 배포 환경에서는 백엔드 관리자 API에 **만료되는 서명 토큰 인증과 서버 검증**을
> 먼저 적용해야 합니다.

### 4-4. 유저 프런트엔드(FE_User) 설치 및 실행

```bash
cd FE_User
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`FE_User/.env` 파일에 Supabase 접속 정보를 채웁니다. 프런트엔드에서 회원가입/로그인에 직접 사용하므로 **anon(publishable) key**만 넣습니다. (Service Role Key는 절대 프런트엔드에 넣지 않습니다)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
```

```bash
streamlit run app.py
```

BE 서버(`http://127.0.0.1:8000`)가 먼저 실행되어 있어야 합니다.

> Supabase 프로젝트의 Authentication → Providers → Email 설정에서 "Confirm email"이 켜져 있으면, 회원가입 후 이메일 인증을 완료해야 로그인할 수 있습니다.
