# 04_favorite_ranking.py

import pandas as pd
import streamlit as st

from clients.favorite_client import get_favorite_ranking
from core.api_client import BackendAPIError
from core.auth import is_logged_in


st.title("즐겨찾기 많은 순 조회")
st.caption("유저가 즐겨찾기한 청약정보를 즐겨찾기 많은 순으로 보여줍니다.")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

try:
    with st.spinner("불러오는 중..."):
        response = get_favorite_ranking()
    ranking = response.get("data") or []

    if not ranking:
        st.info("즐겨찾기 데이터가 없습니다.")
    else:
        status_filter = st.selectbox("공고 상태", ["전체", "진행 중", "만료"])

        df = pd.DataFrame(ranking)
        df["상태"] = df["is_expired"].map({False: "진행 중", True: "만료"})
        df = df.rename(
            columns={
                "listing_id": "청약 ID",
                "title": "공고명",
                "deadline": "마감일",
                "favorite_count": "즐겨찾기 수",
            }
        ).drop(columns=["is_expired"])

        if status_filter != "전체":
            df = df[df["상태"] == status_filter]

        if df.empty:
            st.info(f"{status_filter} 상태의 즐겨찾기 데이터가 없습니다.")
        else:
            st.caption(f"총 {len(df)}건")

            def fade_expired(row):
                if row["상태"] == "만료":
                    return ["color: #9ca3af; background-color: #f3f4f6"] * len(row)
                return [""] * len(row)

            styled_df = df.style.apply(fade_expired, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
except BackendAPIError as error:
    st.error(str(error))
