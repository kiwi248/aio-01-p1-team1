-- Supabase SQL Editor에서 실행합니다.
-- 테이블이 이미 존재한다면 CREATE TABLE 구문은 생략하세요.

-- ============================================
-- 1. profiles (유저 추가정보 - auth.users와 1:1)
--    회원가입/로그인은 Supabase Auth(auth.users)가 처리합니다.
--    지금은 Email 로그인만 사용하고, 나중에 Kakao/Google OAuth를 추가합니다.
-- ============================================
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nickname    VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 신규 유저가 auth.users에 생기면 profiles 행을 자동 생성하는 트리거
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
-- ============================================
CREATE TABLE IF NOT EXISTS listings (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title         VARCHAR(255) NOT NULL,    -- 공고명
    type          VARCHAR(50),              -- 대상 (공공임대/분양 등)
    location      VARCHAR(255),             -- 위치
    price         BIGINT,                   -- 금액 (원 단위)
    eligibility   TEXT,                     -- 자격 조건
    image_url     TEXT,                     -- 사진 URL
    source_url    TEXT,                     -- 원문 링크
    announced_at  DATE,                     -- 공고일 (최신순 정렬)
    deadline      DATE,                     -- 마감일
    description   TEXT,                     -- 상세 설명
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
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

-- ============================================
-- 검색/정렬 성능용 인덱스
-- ============================================
CREATE INDEX IF NOT EXISTS idx_listings_type         ON listings(type);
CREATE INDEX IF NOT EXISTS idx_listings_location     ON listings(location);
CREATE INDEX IF NOT EXISTS idx_listings_price        ON listings(price);
CREATE INDEX IF NOT EXISTS idx_listings_announced_at ON listings(announced_at DESC);
CREATE INDEX IF NOT EXISTS idx_listings_eligibility  ON listings(eligibility);

CREATE INDEX IF NOT EXISTS idx_favorites_listing_id  ON favorites(listing_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user_id     ON favorites(user_id);
