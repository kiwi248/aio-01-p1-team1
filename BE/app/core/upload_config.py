# upload_config.py
"""청약정보 이미지 업로드에 사용하는 설정값입니다."""

# Supabase Storage에 만들어 둔 버킷 이름입니다.
# Public 버킷이라 저장된 이미지 URL을 화면에서 바로 열 수 있습니다.
STORAGE_BUCKET = "listing-images"

# 최대 이미지 크기입니다. 5MB를 넘으면 업로드를 막습니다.
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# 허용하는 이미지 종류입니다. 버킷에 설정한 MIME 목록과 같게 맞춥니다.
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

# 파일 이름을 만들 때 사용할 확장자입니다.
EXTENSION_BY_IMAGE_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
