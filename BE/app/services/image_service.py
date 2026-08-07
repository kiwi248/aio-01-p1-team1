# image_service.py
"""청약정보 이미지를 Supabase Storage에 저장합니다."""

import uuid

from fastapi import HTTPException, UploadFile

from app.core.supabase_config import get_supabase
from app.core.upload_config import (
    ALLOWED_IMAGE_TYPES,
    EXTENSION_BY_IMAGE_TYPE,
    MAX_IMAGE_SIZE,
    STORAGE_BUCKET,
)


def detect_image_type(content: bytes) -> str | None:
    """파일 앞부분(매직 넘버)을 보고 실제 이미지 종류를 알아냅니다.

    확장자나 MIME 타입은 이름만 바꿔도 속일 수 있습니다.
    실제 이미지 파일은 정해진 바이트로 시작하므로 그 값을 직접 확인합니다.
    """

    # JPEG는 FF D8 FF로 시작합니다.
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG는 89 50 4E 47 0D 0A 1A 0A로 시작합니다.
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # WEBP는 RIFF로 시작하고 9~12번째 바이트가 WEBP입니다.
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"

    return None


async def upload_listing_image(image: UploadFile) -> str:
    """이미지를 검사한 뒤 Storage에 올리고 공개 URL을 반환합니다."""

    if image is None or not image.filename:
        raise HTTPException(status_code=400, detail="이미지 파일을 선택해 주세요.")

    content = await image.read()

    # 1. 크기 검사
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"이미지 크기는 5MB를 넘을 수 없습니다. (선택한 파일: {len(content) / 1024 / 1024:.1f}MB)",
        )

    # 2. 브라우저가 보낸 MIME 타입 검사
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="JPG, PNG, WEBP 형식의 이미지만 업로드할 수 있습니다.",
        )

    # 3. 실제 파일 내용 검사 (확장자만 바꾼 파일을 걸러냅니다)
    actual_image_type = detect_image_type(content)
    if actual_image_type is None:
        raise HTTPException(
            status_code=400,
            detail="이미지 파일이 아닙니다. 확장자만 바꾼 파일은 업로드할 수 없습니다.",
        )

    # 4. 겹치지 않는 파일 이름을 만듭니다. 확장자는 실제 종류를 따릅니다.
    extension = EXTENSION_BY_IMAGE_TYPE[actual_image_type]
    storage_path = f"{uuid.uuid4().hex}{extension}"

    # 5. Storage에 올립니다.
    supabase = get_supabase()
    try:
        supabase.storage.from_(STORAGE_BUCKET).upload(
            storage_path,
            content,
            {"content-type": actual_image_type},
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 저장에 실패했습니다. ({error})",
        ) from error

    # 6. 화면에서 바로 열 수 있는 공개 URL을 돌려줍니다.
    #    supabase-py는 URL 끝에 빈 물음표를 붙이므로 떼어내고 저장합니다.
    public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
    return public_url.rstrip("?")
