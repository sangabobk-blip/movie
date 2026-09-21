import streamlit as st
import pandas as pd
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ============================================
# 1. 페이지 기본 설정
# ============================================

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)


# ============================================
# 2. 마인크래프트 배경 설정
# ============================================
# 뒤에 있는 영화 정보가 잘 보이도록
# 배경 위에 반투명한 어두운 레이어를 추가한다.

background_url = (
    "https://www.informallounge.com/assets/"
    "InformalSMP-ZKSqRgst.webp"
)

st.markdown(
    f"""
    <style>

    /* 전체 화면 배경 */
    .stApp {{
        background-image:
            linear-gradient(
                rgba(0, 0, 0, 0.58),
                rgba(0, 0, 0, 0.58)
            ),
            url("{background_url}");

        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* 메인 화면을 조금 투명하게 만들어 배경이 보이도록 설정 */
    .main .block-container {{
        background-color: rgba(0, 0, 0, 0.18);
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}

    /* 제목 */
    h1, h2, h3 {{
        color: white !important;
    }}

    /* 일반 글씨 */
    p, label {{
        color: white !important;
    }}

    /* 표 주변 */
    [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.93);
        border-radius: 10px;
        padding: 5px;
    }}

    /* 지표 카드 */
    [data-testid="stMetric"] {{
        background-color: rgba(255, 255, 255, 0.90);
        padding: 20px;
        border-radius: 12px;
    }}

    /* 지표 카드 안의 글씨 */
    [data-testid="stMetricLabel"] {{
        color: #333333 !important;
    }}

    [data-testid="stMetricValue"] {{
        color: #111111 !important;
    }}

    /* 안내문 */
    [data-testid="stAlert"] {{
        border-radius: 10px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================
# 3. 제목
# ============================================

st.title("🎬 어제의 박스오피스")

st.write(
    "한국시간 기준 어제의 영화관 일일 박스오피스를 "
    "KOBIS에서 불러옵니다."
)


# ============================================
# 4. 한국 시간 기준으로 '어제' 계산
# ============================================
# Streamlit Cloud 서버의 시간이 한국 시간이 아닐 수 있기 때문에
# 서버 시간을 그대로 사용하지 않는다.
#
# Asia/Seoul을 이용해서 한국 시간을 구한 다음
# 하루를 빼서 '어제'를 계산한다.

KST = ZoneInfo("Asia/Seoul")

today_kst = datetime.now(KST)

yesterday_kst = today_kst - timedelta(days=1)

# KOBIS에서 사용하는 날짜 형식
# 예: 20260921
target_date = yesterday_kst.strftime("%Y%m%d")

# 화면에 표시할 날짜
display_date = yesterday_kst.strftime("%Y년 %m월 %d일")


# ============================================
# 5. KOBIS 인증키 가져오기
# ============================================
# 인증키를 코드에 직접 입력하지 않는다.
#
# Streamlit Cloud의 Settings → Secrets에
# 다음과 같이 등록해야 한다.
#
# KOBIS_KEY = "본인의_인증키"

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error("❌ KOBIS_KEY를 찾을 수 없습니다.")

    st.info(
        "Streamlit Cloud에서 "
        "Settings → Secrets로 들어간 후 "
        "KOBIS_KEY를 등록했는지 확인하세요."
    )

    st.stop()


# ============================================
# 6. KOBIS API 주소
# ============================================

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)


# ============================================
# 7. API 요청에 필요한 값
# ============================================

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}


# ============================================
# 8. KOBIS API 요청
# ============================================

try:
    response = requests.get(
        API_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

except requests.exceptions.Timeout:
    st.error("⏱️ KOBIS API 요청 시간이 초과되었습니다.")

    st.info(
        "KOBIS 서버가 늦게 응답하고 있을 수 있습니다. "
        "잠시 후 다시 실행해 보세요."
    )

    st.stop()

except requests.exceptions.RequestException:
    st.error("❌ KOBIS API 요청에 실패했습니다.")

    st.info(
        "인터넷 연결이나 KOBIS API 서버 상태를 "
        "확인한 뒤 다시 실행해 보세요."
    )

    st.stop()


# ============================================
# 9. JSON 데이터로 변환
# ============================================

try:
    data = response.json()

except ValueError:
    st.error("❌ KOBIS API 응답을 읽을 수 없습니다.")

    st.info(
        "KOBIS 서버에서 정상적인 JSON 데이터를 "
        "보내고 있는지 확인해 보세요."
    )

    st.stop()


# ============================================
# 10. KOBIS API 오류 확인
# ============================================
# KOBIS는 인증키가 잘못되어도 상태코드가 200일 수 있다.
# 따라서 faultInfo가 있는지 반드시 확인한다.

if "faultInfo" in data:

    fault_info = data["faultInfo"]

    error_message = fault_info.get(
        "message",
        "KOBIS API에서 오류가 발생했습니다."
    )

    st.error("❌ KOBIS API 오류가 발생했습니다.")

    st.info(
        f"오류 내용: {error_message}\n\n"
        "다음 내용을 확인하세요.\n"
        "• KOBIS 인증키가 정확한지\n"
        "• Secrets의 이름이 KOBIS_KEY인지\n"
        "• 인증키가 정상적으로 발급되었는지"
    )

    st.stop()


# ============================================
# 11. boxOfficeResult 확인
# ============================================

if "boxOfficeResult" not in data:

    st.error("❌ 박스오피스 데이터를 찾을 수 없습니다.")

    st.info(
        "KOBIS API의 응답 형식이 정상인지 확인하거나 "
        "잠시 후 다시 실행해 보세요."
    )

    st.stop()


box_office_result = data["boxOfficeResult"]


# ============================================
# 12. 영화 목록 가져오기
# ============================================

movie_list = box_office_result.get(
    "dailyBoxOfficeList",
    []
)


# ============================================
# 13. 영화 목록이 비어 있는 경우
# ============================================

if not movie_list:

    st.warning(
        f"{display_date}의 영화 목록이 없습니다."
    )

    st.info(
        "다음 내용을 확인해 보세요.\n\n"
        "• KOBIS에서 해당 날짜의 박스오피스가 집계되었는지\n"
        "• KOBIS 인증키가 정상인지\n"
        "• KOBIS API 서버가 정상적으로 작동하는지\n"
        "• 잠시 후 다시 실행해 볼 수 있는지"
    )

    st.stop()


# ============================================
# 14. 데이터프레임 만들기
# ============================================

df = pd.DataFrame(movie_list)


# ============================================
# 15. 필요한 데이터가 있는지 확인
# ============================================

required_columns = [
    "rank",
    "movieNm",
    "openDt",
    "audiCnt",
    "audiAcc",
    "scrnCnt"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    st.error("❌ 필요한 영화 정보가 없습니다.")

    st.info(
        "KOBIS API의 응답 구조가 변경되었을 가능성이 있습니다."
    )

    st.stop()


# ============================================
# 16. 필요한 열만 선택
# ============================================

df = df[
    required_columns
].copy()


# ============================================
# 17. 열 이름을 한국어로 변경
# ============================================

df = df.rename(
    columns={
        "rank": "순위",
        "movieNm": "영화명",
        "openDt": "개봉일",
        "audiCnt": "관객수",
        "audiAcc": "누적관객",
        "scrnCnt": "스크린수"
    }
)


# ============================================
# 18. 숫자 데이터 변환
# ============================================
# KOBIS API에서는 숫자도 문자열로 전달된다.
# 따라서 그래프와 계산을 위해 숫자로 변환한다.

number_columns = [
    "순위",
    "관객수",
    "누적관객",
    "스크린수"
]

for column in number_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).astype(int)


# ============================================
# 19. 조회 날짜 표시
# ============================================

st.subheader(
    f"📅 {display_date} 박스오피스"
)


# ============================================
# 20. 1위 영화 찾기
# ============================================

first_movie = df.iloc[0]


st.subheader("🏆 1위 영화")


# 3개의 지표 카드를 크게 표시
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


# ============================================
# 21. 전체 박스오피스 표
# ============================================

st.subheader("📋 박스오피스")


display_df = df.copy()


# 화면에 표시할 때만 천 단위 쉼표를 넣는다.
display_df["관객수"] = display_df[
    "관객수"
].apply(
    lambda x: f"{x:,}"
)


display_df["누적관객"] = display_df[
    "누적관객"
].apply(
    lambda x: f"{x:,}"
)


display_df["스크린수"] = display_df[
    "스크린수"
].apply(
    lambda x: f"{x:,}"
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ============================================
# 22. 관객수 상위 5편 그래프
# ============================================

st.subheader("📊 관객수 상위 5편")


top5 = (
    df.sort_values(
        by="관객수",
        ascending=False
    )
    .head(5)
    .copy()
)


# 영화명을 기준으로 그래프를 만든다.
chart_data = top5[
    ["영화명", "관객수"]
].set_index("영화명")


st.bar_chart(
    chart_data,
    use_container_width=True
)


# ============================================
# 23. 데이터 출처
# ============================================

st.caption(
    "데이터 출처: 영화진흥위원회 영화관입장권통합전산망(KOBIS) 오픈API"
)
