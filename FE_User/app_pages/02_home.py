import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from core.auth import is_logged_in


def encode_image(image_path: Path) -> str:
    """로컬 이미지를 HTML에서 표시할 수 있는 Base64 문자열로 변환합니다."""
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def render_banner() -> None:
    """5개의 배너를 일정한 간격으로 자동 순환시킵니다."""
    banner_directory = Path(__file__).resolve().parents[1] / "assets" / "banners"
    banner_paths = [
        banner_directory / f"banner{number}.png"
        for number in range(6, 11)
    ]

    missing_paths = [path.name for path in banner_paths if not path.exists()]
    if missing_paths:
        st.warning(f"배너 이미지를 찾을 수 없습니다: {', '.join(missing_paths)}")
        return

    encoded_images = [encode_image(path) for path in banner_paths]
    encoded_images.append(encoded_images[0])
    slides = "".join(
        f'<div class="banner-slide"><img src="data:image/png;base64,{image}"></div>'
        for image in encoded_images
    )

    components.html(
        f"""
        <style>
            * {{ box-sizing: border-box; }}
            html, body {{ margin: 0; padding: 0; background: transparent; }}
            .banner-container {{
                width: min(100%, 900px);
                aspect-ratio: 900 / 342;
                margin-top: 30px;
                margin-right: auto;
                margin-left: 0;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                background: #111827;
                box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
            }}
            .banner-track {{
                display: flex;
                width: 600%;
                height: 100%;
                animation: banner-slide 25s cubic-bezier(0.4, 0, 0.2, 1) infinite;
            }}
            .banner-slide {{
                width: calc(100% / 6);
                height: 100%;
                flex-shrink: 0;
            }}
            .banner-slide img {{
                display: block;
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}
            @keyframes banner-slide {{
                0%, 17.6% {{ transform: translateX(0); }}
                20%, 37.6% {{ transform: translateX(-16.6667%); }}
                40%, 57.6% {{ transform: translateX(-33.3333%); }}
                60%, 77.6% {{ transform: translateX(-50%); }}
                80%, 97.6% {{ transform: translateX(-66.6667%); }}
                100% {{ transform: translateX(-83.3333%); }}
            }}
        </style>
        <div class="banner-container">
            <div class="banner-track">{slides}</div>
        </div>
        """,
        height=380,
        scrolling=False,
    )


st.title("🏘️ 공공임대 및 분양 청약 통합 안내")

if is_logged_in():
    st.info(f"{st.session_state.email} 님, 환영합니다.")
    st.write("즐겨찾기 페이지에서 저장한 청약정보를 확인할 수 있습니다.")
else:
    st.write("로그인하면 즐겨찾기 페이지에서 저장한 청약정보를 관리할 수 있습니다.")

st.write("왼쪽 메뉴의 '청약정보 조회'에서 공고를 확인해 보세요.")

render_banner()
