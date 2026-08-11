# 공공임대 및 분양 청약 통합 안내 서비스 — 프로젝트 계획서 (Plan)

5인 팀 프로젝트. 작성 시점 기준 구현된 내용을 반영한 as-built 문서다.

---

## 1. 프로젝트 개요

### 1-1. 주제

공공임대·분양 청약 정보를 한곳에 모아 조회·검색하고, 관심 있는 공고를 즐겨찾기로 관리할 수 있는 안내 서비스. 관리자는 공고를 등록·관리하고 서비스 운영 현황(즐겨찾기 통계, 실시간 로그)을 모니터링한다.

### 1-2. 사용자와 시나리오

- **유저**: 이메일로 회원가입/로그인(Supabase Auth) → 청약정보를 조건검색 → 마음에 드는 공고를 mypage에 즐겨찾기 → 회원정보(연락처, 관심분야, 비밀번호) 관리
- **관리자**: 중앙에서 미리 발급된 계정으로 로그인 → 청약정보 등록·수정·삭제(이미지 포함) → 어떤 유저가 무엇을 즐겨찾기했는지, 즐겨찾기 순위 조회 → 서비스 로그를 실시간/이력으로 모니터링

### 1-3. 전체 구조

```
                 ┌──────────────────┐
                 │   FE_Admin       │  Streamlit, 관리자 전용
                 │  (Streamlit)     │
                 └────────┬─────────┘
                          │ HTTPS (REST)
┌──────────────────┐      │      ┌──────────────────┐
│   FE_User        │──────┼──────│  BE (FastAPI)     │
│  (Streamlit)     │      │      │                    │
└─────────┬─────────┘      │      └─────────┬─────────┘
          │                │                │
          │ Supabase Auth  │                │ Supabase (PostgreSQL)
          │ (회원가입/로그인 직접 호출)          │ + Supabase Storage(이미지)
          ▼                                 ▼
                     ┌────────────────────────────┐
                     │          Supabase           │
                     └────────────────────────────┘
```

- 회원가입/로그인/비밀번호 변경은 FE_User가 **BE를 거치지 않고 Supabase Auth에 직접** 요청한다. BE는 그 외 모든 데이터(청약정보, 즐겨찾기, 프로필, 로그)를 담당한다.
- 관리자 인증은 자체 `admins` 테이블 + 해시 비밀번호로 별도 관리한다 (Supabase Auth 미사용).

---

## 2. 데이터베이스 설계

### 2-1. ERD

```
┌─────────────────────────────┐
│   auth.users (Supabase 관리) │  ← 팀이 직접 만들지 않음
└──────────────┬───────────────┘
               │ 1:1 (트리거로 자동 생성)
               ▼
┌─────────────────────────────┐        ┌─────────────────┐
│          profiles_손영민     │        │      admins      │
├─────────────────────────────┤        ├─────────────────┤
│ id UUID PK (FK→auth.users)  │        │ id BIGINT PK     │
│ nickname                     │        │ username UNIQUE  │
│ phone                        │        │ password (hash)  │
│ birth_date                   │        │ created_at        │
│ interests JSONB              │        └─────────────────┘
│ created_at                   │          (관리자 인증, 독립)
└──────────────┬───────────────┘
               │ 1
               │
               │ N
┌──────────────┴───────────────┐         ┌─────────────────────────────┐
│          favorites_김인혜     │───────▶│           listings_장상옥    │
├───────────────────────────────┤   N:1  ├──────────────────────────────┤
│ id BIGINT PK                  │        │ id BIGINT PK                 │
│ user_id UUID (FK→auth.users)  │        │ title, housing_name          │
│ listing_id BIGINT (FK)        │        │ area_sqm, recruitment_count  │
│ created_at                    │        │ location, deposit,           │
│ UNIQUE(user_id, listing_id)   │        │ monthly_rent                 │
└────────────────────────────────┘        │ application_start/end_date  │
                                          │ description, image_url,     │
                                          │ source_url, created_at       │
                                          └──────────────────────────────┘

┌─────────────────────────────┐        ┌─────────────────────────────┐
│             logs_윤기화      │        │       chat_summaries_권오현  │
├─────────────────────────────┤        ├─────────────────────────────┤
│ id BIGINT PK                 │        │ id UUID PK                   │
│ time, level, screen           │        │ user_id, title, summary      │
│ message, latency_ms           │        │ message_count, model         │
│ created_at                    │        │ created_at                   │
└─────────────────────────────┘        └─────────────────────────────┘
  (warning/error만 저장,                    (AI 채팅 요약 — 테이블만 준비,
   listings/favorites와 무관한 독립 이력)      기능 구현은 예정)
```

### 2-2. 테이블별 SQL

Supabase SQL Editor에서 아래 순서대로 실행한다 (`BE/sql/` 아래 각 파일과 대응).

**① `schema.sql` — profiles, admins, listings, favorites**

```sql
-- ============================================
-- 1. profiles (유저 추가정보 - auth.users와 1:1)
--    회원가입/로그인은 Supabase Auth(auth.users)가 처리합니다.
-- ============================================
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nickname    VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, nickname)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'nickname');
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================
-- 2. admins (관리자 - 직접 관리, 회원가입 API 없음)
-- ============================================
CREATE TABLE IF NOT EXISTS admins (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username    VARCHAR(50) NOT NULL UNIQUE,
    password    TEXT NOT NULL,              -- 반드시 해시해서 저장 (scripts/create_admin.py 참고)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- 3. listings (청약정보)
--    한 행은 같은 공고 안의 '주택 1개 + 신청유형(면적) 1개'를 의미합니다.
-- ============================================
CREATE TABLE IF NOT EXISTS listings (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title                  VARCHAR(255) NOT NULL,
    housing_name           VARCHAR(255) NOT NULL,
    area_sqm               NUMERIC(10,2) NOT NULL,
    recruitment_count      INTEGER NOT NULL,
    location               VARCHAR(50) NOT NULL,
    deposit                BIGINT NOT NULL,
    monthly_rent           BIGINT NOT NULL,
    application_start_date DATE NOT NULL,
    application_end_date   DATE NOT NULL,
    description            TEXT NOT NULL,
    image_url              TEXT,
    source_url             TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_listings_area_sqm           CHECK (area_sqm > 0),
    CONSTRAINT ck_listings_recruitment_count  CHECK (recruitment_count > 0),
    CONSTRAINT ck_listings_deposit            CHECK (deposit >= 0),
    CONSTRAINT ck_listings_monthly_rent       CHECK (monthly_rent >= 0),
    CONSTRAINT ck_listings_application_period CHECK (application_end_date >= application_start_date)
);

-- ============================================
-- 4. favorites (즐겨찾기 - user_id는 auth.users를 참조하는 UUID)
-- ============================================
CREATE TABLE IF NOT EXISTS favorites (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    listing_id  BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_favorites UNIQUE (user_id, listing_id)
);

-- 검색/정렬 성능용 인덱스
CREATE INDEX IF NOT EXISTS idx_listings_location               ON listings(location);
CREATE INDEX IF NOT EXISTS idx_listings_deposit                ON listings(deposit);
CREATE INDEX IF NOT EXISTS idx_listings_monthly_rent           ON listings(monthly_rent);
CREATE INDEX IF NOT EXISTS idx_listings_application_start_date ON listings(application_start_date DESC);
CREATE INDEX IF NOT EXISTS idx_listings_application_end_date   ON listings(application_end_date);
CREATE INDEX IF NOT EXISTS idx_favorites_listing_id  ON favorites(listing_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user_id     ON favorites(user_id);
```

**② `profiles.sql` — 회원 추가정보(연락처/생년월일/관심분야) 확장**

```sql
ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS phone VARCHAR(13),
    ADD COLUMN IF NOT EXISTS birth_date DATE,
    ADD COLUMN IF NOT EXISTS interests JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, nickname, phone, birth_date, interests)
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data->>'nickname',
        NEW.raw_user_meta_data->>'phone',
        NULLIF(NEW.raw_user_meta_data->>'birth_date', '')::DATE,
        COALESCE(NEW.raw_user_meta_data->'interests', '[]'::jsonb)
    );
    RETURN NEW;
END;
$$;
```

**③ `alter_listings.sql` — listings 구조를 최종 형태로 변경** (type/price/eligibility 등 초기 컬럼 → housing_name/area_sqm/deposit/monthly_rent 등으로 개편, `BE/sql/alter_listings.sql`에 트랜잭션·데이터 0건 검사 포함 전체 내용 있음)

**④ `logs.sql` — 실시간 로그 이력 (실시간 로그 시각화 담당)**

```sql
CREATE TABLE IF NOT EXISTS logs (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    time        TIMESTAMPTZ NOT NULL,       -- 로그가 생성된 시각
    level       VARCHAR(10) NOT NULL CHECK (level IN ('warning', 'error')),
    screen      VARCHAR(50) NOT NULL,
    message     TEXT NOT NULL,
    latency_ms  INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()   -- DB에 저장된 시각
);

CREATE INDEX IF NOT EXISTS idx_logs_time  ON logs(time DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
```

> info 로그는 발생량이 많고 다시 볼 필요가 적어 DB에 저장하지 않고 백엔드 메모리(`deque`)에만 둔다. warning/error만 이 테이블에 영구 저장한다.

**⑤ `chat_summaries` — AI 채팅 요약 (테이블만 준비, 기능 미구현 예정)**

| 컬럼            | 타입        |
| --------------- | ----------- |
| `id`            | uuid PK     |
| `user_id`       | uuid        |
| `title`         | varchar     |
| `summary`       | text        |
| `message_count` | int4        |
| `model`         | varchar     |
| `created_at`    | timestamptz |

RLS 정책(`authenticated` 역할이 `auth.uid() = user_id`인 행만 조회/삽입)까지 만들어져 있으나, 이 채팅 기능은 아직 BE/FE 코드로 구현되지 않은 **차기 개발 예정 항목**이다.

---

## 3. API 설계 (BE, FastAPI)

모든 응답은 공통 포맷을 따른다: `{"success": bool, "message": str, "data": ...}`

### Admin (`/admin`, 관리자 전용)

| Method | Path                                  | 설명                                        |
| ------ | ------------------------------------- | ------------------------------------------- |
| POST   | `/admin/login`                        | 관리자 로그인                               |
| POST   | `/admin/listings/create`              | 청약정보 등록                               |
| POST   | `/admin/listings/images`              | 청약정보 이미지 업로드 (Supabase Storage)   |
| PUT    | `/admin/listings/update/{listing_id}` | 청약정보 수정 (이미지 교체/삭제 포함)       |
| DELETE | `/admin/listings/{listing_id}/image`  | 이미지만 삭제                               |
| DELETE | `/admin/listings/delete/{listing_id}` | 청약정보 삭제 (Storage 이미지도 함께 정리)  |
| GET    | `/admin/favorites/ranking`            | 즐겨찾기 많은 순 조회                       |
| GET    | `/admin/favorites/detail`             | 어떤 유저가 어떤 공고를 즐겨찾기했는지 조회 |

### Listing (`/listings`, 공개)

| Method | Path                         | 설명                                                     |
| ------ | ---------------------------- | -------------------------------------------------------- |
| GET    | `/listings/getall`           | 전체 조회                                                |
| GET    | `/listings/page`             | 페이지 단위 조회 (`page`, `page_size`)                   |
| GET    | `/listings/search`           | 조건검색 (`location`, `max_deposit`, `max_monthly_rent`) |
| GET    | `/listings/get/{listing_id}` | 단건 조회                                                |

### Favorite (`/favorites`)

| Method | Path                                       | 설명                        |
| ------ | ------------------------------------------ | --------------------------- |
| POST   | `/favorites/create`                        | 즐겨찾기 등록 (중복 시 409) |
| GET    | `/favorites/mypage/{user_id}`              | mypage 즐겨찾기 목록        |
| DELETE | `/favorites/delete/{user_id}/{listing_id}` | 즐겨찾기 삭제               |

### Profile (`/profiles`)

| Method | Path                  | 설명                                   |
| ------ | --------------------- | -------------------------------------- |
| GET    | `/profiles/{user_id}` | 프로필 조회                            |
| PUT    | `/profiles/{user_id}` | 프로필 수정 (닉네임, 연락처, 관심분야) |

> 회원가입/로그인/비밀번호 변경은 FE_User가 Supabase Auth SDK로 직접 호출하므로 BE API가 없다.

### Log (`/logs`, 실시간 로그 시각화 담당)

| Method | Path            | 설명                                       | 데이터 소스               |
| ------ | --------------- | ------------------------------------------ | ------------------------- |
| GET    | `/logs`         | 최근 로그 조회 (`level`, `limit`)          | 메모리(deque, 최대 200건) |
| GET    | `/logs/history` | warning/error 이력 조회 (`level`, `limit`) | Supabase `logs` 테이블    |

---

## 4. 화면 설계

### FE_Admin (관리자, Streamlit)

| 페이지             | 설명                                                                                            |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| 홈                 | 로그인 상태 안내                                                                                |
| 로그인             | 관리자 로그인 (Session Storage로 새로고침 후에도 상태 유지, 실제 인증 수단은 아님 — 4-5절 참고) |
| 청약정보 등록      | 공고 정보 + 이미지 업로드                                                                       |
| 청약정보 조회/삭제 | 조건검색 + 페이지네이션 + 이미지 교체/삭제 + 삭제(확인 체크 필요)                               |
| 즐겨찾기 순위      | 즐겨찾기 많은 순 표                                                                             |
| 즐겨찾기 상세      | 유저별 즐겨찾기 내역                                                                            |
| 로그 대시보드      | `st.fragment(run_every="5s")` 폴링, level 필터 + 표 + 막대그래프                                |
| 로그 이력 조회     | DB에 저장된 warning/error 이력, level 필터 + 조회 건수 슬라이더                                 |

### FE_User (유저, Streamlit)

| 페이지        | 설명                                                                                            |
| ------------- | ----------------------------------------------------------------------------------------------- |
| 홈            | 서비스 소개                                                                                     |
| 로그인        | Supabase Auth 이메일 로그인. 세션 토큰을 브라우저 Session Storage에 저장했다가 새로고침 시 복원 |
| 회원가입      | 약관 동의 → 이메일/비밀번호/연락처/생년월일/관심분야 입력                                       |
| 청약정보 조회 | 조건검색(자치구, 최대 보증금, 최대 월세) + 즐겨찾기 추가                                        |
| My Page       | 회원정보(성함/연락처/관심분야) 수정, 비밀번호 변경, 즐겨찾기 조회/삭제                          |

---

## 5. 실시간 로그 시각화 (개인 담당 상세)

### 5-1. 목표

`random + time` 기반 시뮬레이터가 만들어내는 로그를 프로세스 메모리(`collections.deque`, `maxlen=200`)에 저장하고, 최근 N개를 Streamlit 대시보드에서 몇 초마다 자동 새로고침(폴링)하는 준실시간 모니터링 화면을 만든다. warning/error는 DB에도 남겨 재시작 후에도 이력을 조회할 수 있게 한다.

### 5-2. 아키텍처

```
[FastAPI 앱 시작 시 백그라운드 스레드 (lifespan으로 기동)]
  random + time.sleep(2초)
    → deque(maxlen=200)에 dict로 append          (실시간 조회용, 휘발성)
    → level이 warning/error면 Supabase logs 테이블에도 INSERT   (영구 이력용)

[GET /logs]           deque 슬라이싱, 준실시간(최대 6~7분치)
[GET /logs/history]   Supabase logs 테이블 조회, 영구 이력(warning/error만)

[Streamlit — FE_Admin]
  로그 대시보드   : st.fragment(run_every="5s")로 GET /logs 폴링 → 표 + 막대그래프
  로그 이력 조회  : GET /logs/history 조회 → 표 (level 필터, 조회 건수 슬라이더)
```

파일+tail 대신 메모리(deque)를 택한 이유는 목표가 "동작하는 준실시간 대시보드"이고, Render 무료 티어가 재시작 시 파일시스템도 초기화되는 휘발성이라 파일 저장의 이점이 없었기 때문이다.

### 5-3. 구현 중 발견한 이슈와 개선 (프로젝트 전체에 적용된 공용 수정)

1. **httpx 쿼리 파라미터에 `None` 전달 시 422 에러**: 프런트에서 검색 필터를 안 쓸 때 `None`이 빈 문자열로 직렬화되어 FastAPI 검증이 실패했다. 공통 `request()` 함수에서 `None` 값을 제거하도록 수정 (FE_Admin, FE_User 공통 적용).
2. **Supabase client를 요청마다 새로 생성 → 응답 지연**: `GET /listings/getall` 평균 응답시간이 2754.6ms였다. client를 프로세스 전역 싱글턴으로 재사용하도록 바꿔 1169.7ms로 약 57% 단축 (`BE/scripts/benchmark_listings.py`로 측정).
3. **전역 싱글턴은 동시 요청에 취약**: 동시 요청 20개 테스트에서 전역 싱글턴 client는 공유 HTTP/2 연결이 끊기며 20개 전부 500 에러가 났다. FastAPI 동기 라우터가 스레드풀에서 실행된다는 점에 착안해 `threading.local()`로 스레드별 client를 쓰도록 수정, 동시 요청 20개 전부 성공을 확인했다. 이 수정은 BE 전체 API(관리자/청약정보/즐겨찾기/프로필/로그)에 공통 적용된다.

---

## 6. 배포 계획

| 구성                          | 대상                      | 비고                                                                                                                   |
| ----------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 백엔드(BE)                    | Render (Free Web Service) | Start Command에 `--workers` 옵션 미사용 — 로그 buffer가 인스턴스 하나의 메모리에만 있어 워커가 여러 개면 로그가 분산됨 |
| 프런트엔드(FE_Admin, FE_User) | Streamlit Community Cloud | 앱별로 `st.secrets`에 `BACKEND_URL` 등록                                                                               |
| DB / Storage                  | Supabase (기존 프로젝트)  | PostgreSQL + Auth + Storage(이미지)                                                                                    |

### 배포용으로 준비한 코드

- BE: `CORSMiddleware` 추가, `ALLOWED_ORIGINS` 환경변수로 허용 도메인 관리 (기본값 `*`, 쿠키 인증이 없는 API라 안전)
- FE_Admin / FE_User: `BACKEND_URL`을 `st.secrets`에서 우선 읽고 없으면 로컬 기본값으로 폴백 (`.env` 대신 secrets 사용, 로컬 개발 흐름은 그대로 유지)

### 무료 티어 유의사항

- Render 무료 티어는 일정 시간 요청이 없으면 슬립되어 첫 요청 시 콜드스타트(수십 초)가 발생한다.
- Streamlit Community Cloud도 비활성 시 슬립된다. 로그 대시보드 폴링 주기는 1~2초처럼 너무 짧게 잡지 않고 5초로 설정했다.

### 현재 배포 상태

코드/설정은 준비 완료. **실제 Render/Streamlit Cloud 배포 및 배포 환경에서의 동작 확인은 진행 예정.**

---

## 7. 진행 상황 체크리스트

### 공통 기능 (5인 팀 전체)
- [x] 관리자 로그인 / 청약정보 CRUD (이미지 업로드 포함) / 페이지네이션
- [x] 유저 회원가입·로그인(Supabase Auth, 세션 토큰 복원) / 회원정보 수정 / 비밀번호 변경
- [x] 청약정보 조회·조건검색 (유저/관리자 양쪽)
- [x] 즐겨찾기 생성/조회/삭제 (유저), 즐겨찾기 순위·상세 (관리자)
- [ ] AI 채팅 요약 (`chat_summaries` 테이블만 준비, 코드 미구현)

### 실시간 로그 시각화 (개인 담당)
- [x] 로그 스키마, deque 저장 버퍼, 백그라운드 시뮬레이터, `lifespan` 기동
- [x] `GET /logs`, `GET /logs/history` API
- [x] warning/error Supabase 저장 (예외 처리 포함)
- [x] FE_Admin 로그 대시보드(폴링) + 로그 이력 조회 페이지
- [x] Supabase client 성능/동시성 개선 (전체 API에 적용)
- [x] 배포용 CORS·secrets 코드 준비
- [ ] Render/Streamlit Cloud 실제 배포
- [ ] 배포 환경에서 폴링 동작 최종 확인

---

## 8. 기술 스택

| 구분                           | 기술                                                       |
| ------------------------------ | ---------------------------------------------------------- |
| 백엔드                         | Python, FastAPI, Pydantic, Uvicorn                         |
| 프런트엔드                     | Streamlit, httpx                                           |
| 데이터베이스 / 인증 / 스토리지 | Supabase (PostgreSQL, Supabase Auth, Storage)              |
| 배포(예정)                     | Render (BE), Streamlit Community Cloud (FE_Admin, FE_User) |
