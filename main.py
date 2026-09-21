
# ============================================
# 어제의 박스오피스를 보여주는 Streamlit 앱
# KOBIS 일일 박스오피스 API 사용
# ============================================

import streamlit as st
import pandas as pd
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)


# --------------------------------------------
# 2. 제목과 간단한 설명
# --------------------------------------------

st.title("🎬 어제의 박스오피스")

st.write(
    "한국시간 기준 어제의 영화관 일일 박스오피스를 "
    "KOBIS API에서 불러옵니다."
)


# --------------------------------------------
# 3. 한국 시간 기준으로 '어제' 계산
# --------------------------------------------
# Streamlit Cloud 서버의 시간이 한국 시간이 아닐 수 있으므로
# 서버의 현재 시간(datetime.now())을 그대로 사용하지 않습니다.
#
# ZoneInfo를 이용해 현재 시각을 한국 시간으로 변환한 뒤
# 하루를 빼서 어제 날짜를 계산합니다.

KST = ZoneInfo("Asia/Seoul")

today_kst = datetime.now(KST)
yesterday_kst = today_kst - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday_kst.strftime("%Y%m%d")

# 화면에 표시할 날짜
display_date = yesterday_kst.strftime("%Y년 %m월 %d일")


# --------------------------------------------
# 4. KOBIS API 인증키 가져오기
# --------------------------------------------
# 실제 인증키는 코드에 직접 쓰지 않습니다.
# Streamlit Cloud의 Secrets에 다음과 같이 저장해야 합니다.
#
# [secrets]
# KOBIS_KEY = "발급받은_인증키"
#
# 또는 Streamlit Cloud의 Secrets 설정 화면에서
# KOBIS_KEY를 추가하면 됩니다.

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error("KOBIS_KEY를 찾을 수 없습니다.")
    st.info(
        "Streamlit Cloud의 Settings → Secrets에서 "
        "KOBIS_KEY를 등록했는지 확인하세요."
    )
    st.stop()


# --------------------------------------------
# 5. KOBIS API 요청
# --------------------------------------------

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}


try:
    # KOBIS API에 요청을 보냅니다.
    response = requests.get(
        API_URL,
        params=params,
        timeout=10
    )

    # HTTP 오류가 발생했는지 확인합니다.
    response.raise_for_status()

    # JSON 형태의 응답을 가져옵니다.
    data = response.json()

except requests.exceptions.RequestException as e:
    st.error("KOBIS API 요청에 실패했습니다.")
    st.info(
        "인터넷 연결, KOBIS API 주소, API 서버 상태를 "
        "확인한 뒤 다시 실행해 보세요."
    )
    st.stop()

except ValueError:
    st.error("KOBIS API의 응답을 JSON으로 읽을 수 없습니다.")
    st.info(
        "KOBIS API 서버가 정상적인 JSON 응답을 보내고 있는지 "
        "확인해 보세요."
    )
    st.stop()


# --------------------------------------------
# 6. API 오류(faultInfo) 확인
# --------------------------------------------
# KOBIS API는 인증키가 잘못된 경우에도 HTTP 상태코드가
# 200으로 올 수 있습니다.
#
# 따라서 status_code만 확인하면 안 되고
# 응답 안의 faultInfo도 확인해야 합니다.

if "faultInfo" in data:
    fault_info = data["faultInfo"]

    error_message = fault_info.get(
        "message",
        "KOBIS API에서 오류가 발생했습니다."
    )

    st.error("KOBIS API 오류가 발생했습니다.")
    st.info(
        f"오류 내용: {error_message}\n\n"
        "KOBIS 인증키가 정확한지, 만료되거나 제한된 키가 아닌지 "
        "확인하세요."
    )
    st.stop()


# --------------------------------------------
# 7. boxOfficeResult 확인
# --------------------------------------------

if "boxOfficeResult" not in data:
    st.error("예상한 박스오피스 데이터가 없습니다.")
    st.info(
        "KOBIS API의 응답 구조가 정상인지 확인하고 "
        "잠시 후 다시 시도해 보세요."
    )
    st.stop()


box_office_result = data["boxOfficeResult"]


# --------------------------------------------
# 8. 영화 목록 가져오기
# --------------------------------------------

movie_list = box_office_result.get(
    "dailyBoxOfficeList",
    []
)


# 영화 목록이 비어 있는 경우
if not movie_list:
    st.warning(
        f"{display_date}의 영화 목록이 없습니다."
    )

    st.info(
        "다음 내용을 확인해 보세요.\n\n"
        "• KOBIS에서 해당 날짜의 일일 박스오피스가 집계되었는지\n"
        "• KOBIS API 인증키가 정상인지\n"
        "• 조회 날짜가 API에서 제공되는 날짜인지\n"
        "• 잠시 후 다시 요청해 볼 수 있는지"
    )

    st.stop()


# --------------------------------------------
# 9. 데이터프레임 만들기
# --------------------------------------------

df = pd.DataFrame(movie_list)


# --------------------------------------------
# 10. 필요한 열만 선택
# --------------------------------------------

columns = {
    "rank": "순위",
    "movieNm": "영화명",
    "openDt": "개봉일",
    "audiCnt": "관객수",
    "audiAcc": "누적관객",
    "scrnCnt": "스크린수"
}

# API에서 필요한 열이 실제로 존재하는지 확인
missing_columns = [
    column
    for column in columns
    if column not in df.columns
]

if missing_columns:
    st.error("API 응답에 필요한 영화 정보가 없습니다.")
    st.info(
        "KOBIS API의 응답 구조가 변경되었는지 확인하세요."
    )
    st.stop()


# 필요한 열만 가져오고 한글 이름으로 변경
df = df[list(columns.keys())].rename(
    columns=columns
)


# --------------------------------------------
# 11. 숫자 데이터 변환
# --------------------------------------------
# KOBIS API에서는 숫자도 문자열로 전달될 수 있으므로
# 그래프와 표에서 제대로 처리할 수 있도록 숫자로 변환합니다.

numeric_columns = [
    "순위",
    "관객수",
    "누적관객",
    "스크린수"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).astype(int)


# 관객수가 큰 숫자로 보이도록 천 단위 쉼표를 넣습니다.
# 그래프용 데이터는 숫자형을 그대로 사용해야 하므로
# 화면 표시용 표에서는 별도로 포맷을 적용합니다.


# --------------------------------------------
# 12. 조회 날짜 표시
# --------------------------------------------

st.subheader(f"📅 {display_date} 박스오피스")


# --------------------------------------------
# 13. 1위 영화 정보
# --------------------------------------------

first_movie = df.iloc[0]

st.markdown("### 🏆 1위 영화")

# 3개의 지표 카드를 나란히 표시
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="영화명",
        value=str(first_movie["영화명"])
    )

with col2:
    st.metric(
        label="관객수",
        value=f"{first_movie['관객수']:,}명"
    )

with col3:
    st.metric(
        label="누적관객",
        value=f"{first_movie['누적관객']:,}명"
    )


# --------------------------------------------
# 14. 전체 영화 표
# --------------------------------------------

st.markdown("### 📋 전체 박스오피스")

# 화면에 표시할 복사본
display_df = df.copy()

display_df["관객수"] = display_df["관객수"].map(
    lambda x: f"{x:,}"
)

display_df["누적관객"] = display_df["누적관객"].map(
    lambda x: f"{x:,}"
)

display_df["스크린수"] = display_df["스크린수"].map(
    lambda x: f"{x:,}"
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------
# 15. 관객수 상위 5편 막대그래프
# --------------------------------------------

st.markdown("### 📊 관객수 상위 5편")

top5 = (
    df.sort_values(
        by="관객수",
        ascending=False
    )
    .head(5)
    .copy()
)

# 영화명을 인덱스로 설정하면
# Streamlit에서 영화별 막대그래프로 표시됩니다.
chart_data = top5.set_index("영화명")[["관객수"]]

st.bar_chart(
    chart_data,
    x_label="영화",
    y_label="관객수"
)


# --------------------------------------------
# 16. 데이터 출처
# --------------------------------------------

st.caption(
    "데이터 출처: 영화진흥위원회 영화관입장권통합전산망(KOBIS) 오픈API"
)
