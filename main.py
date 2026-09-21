```python
# ============================================
# 🎬 KOBIS 주말 박스오피스 조회 앱
# ============================================
#
# 이 프로그램은 영화진흥위원회(KOBIS) API를 이용해서
# 가장 최근에 끝난 주말의 영화 순위를 보여준다.
#
# 필요한 파일:
#   main.py
#   requirements.txt
#
# 인증키는 코드에 직접 작성하지 않고
# Streamlit Secrets의 KOBIS_KEY에서 가져온다.
# ============================================


# --------------------------------------------
# 1. 필요한 라이브러리 가져오기
# --------------------------------------------

import streamlit as st
import pandas as pd
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------
# 2. 화면 기본 설정
# --------------------------------------------

st.set_page_config(
    page_title="주말 박스오피스",
    page_icon="🎬",
    layout="wide"
)


# --------------------------------------------
# 3. 제목
# --------------------------------------------

st.title("🎬 주말 박스오피스")

st.write(
    "한국시간 기준 가장 최근에 끝난 주말의 "
    "영화 박스오피스를 확인합니다."
)


# --------------------------------------------
# 4. 한국 시간으로 현재 날짜와 시간 구하기
# --------------------------------------------
#
# Streamlit Cloud 서버가 한국에 있다는 보장은 없다.
# 따라서 서버의 시간을 그대로 사용하지 않고
# 한국 시간(Asia/Seoul)을 기준으로 계산한다.

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)


# --------------------------------------------
# 5. 가장 최근에 끝난 일요일 계산
# --------------------------------------------
#
# KOBIS의 주말 박스오피스(weekGb=1)는
# 금요일~일요일을 하나의 기간으로 조회한다.
#
# 따라서 가장 최근의 일요일을 기준 날짜로 사용한다.
#
# 예:
# 월요일 → 전날 일요일
# 화요일 → 전날 일요일
# 수요일 → 전날 일요일
# 목요일 → 전날 일요일
# 금요일 → 전날 일요일
# 토요일 → 전날 일요일
# 일요일 → 오늘 일요일
#
# 다만 일요일에는 아직 하루가 끝나지 않았을 수 있으므로
# 오늘이 일요일이면 지난주 일요일을 사용한다.

weekday = now_kst.weekday()
# 월요일=0, 화요일=1, ..., 토요일=5, 일요일=6


if weekday == 6:
    # 오늘이 일요일이면 지난주 일요일 사용
    last_sunday = now_kst - timedelta(days=7)
else:
    # 가장 최근 일요일 계산
    days_since_sunday = weekday + 1
    last_sunday = now_kst - timedelta(days=days_since_sunday)


target_date = last_sunday.strftime("%Y%m%d")

display_date = last_sunday.strftime(
    "%Y년 %m월 %d일"
)


# --------------------------------------------
# 6. KOBIS 인증키 가져오기
# --------------------------------------------
#
# 실제 인증키를 코드에 적으면 안 된다.
#
# Streamlit Cloud의
# Settings → Secrets
# 에 다음과 같이 입력한다.
#
# KOBIS_KEY = "본인의_인증키"
#
# 아래 코드에서는 그 값을 불러온다.

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error("❌ KOBIS_KEY를 찾을 수 없습니다.")

    st.info(
        "Streamlit Cloud의 Settings → Secrets에서 "
        "KOBIS_KEY를 등록했는지 확인하세요."
    )

    st.stop()


# --------------------------------------------
# 7. KOBIS 주간/주말 박스오피스 API 주소
# --------------------------------------------

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchWeeklyBoxOfficeList.json"
)


# --------------------------------------------
# 8. API 요청에 사용할 값
# --------------------------------------------
#
# weekGb
# 0 = 주간(월~일)
# 1 = 주말(금~일)
# 2 = 주중(월~목)
#
# 여기서는 주말 박스오피스를 조회하므로
# weekGb=1을 사용한다.

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date,
    "weekGb": "1"
}


# --------------------------------------------
# 9. KOBIS API 요청
# --------------------------------------------

try:

    response = requests.get(
        API_URL,
        params=params,
        timeout=10
    )

    # 인터넷 연결 등의 HTTP 오류 확인
    response.raise_for_status()

    # JSON 응답을 파이썬 데이터로 변환
    data = response.json()


except requests.exceptions.Timeout:

    st.error("⏱️ KOBIS API 요청 시간이 초과되었습니다.")

    st.info(
        "KOBIS 서버가 응답하지 않았을 수 있습니다. "
        "잠시 후 다시 실행해 보세요."
    )

    st.stop()


except requests.exceptions.RequestException:

    st.error("❌ KOBIS API 요청에 실패했습니다.")

    st.info(
        "인터넷 연결이나 KOBIS API 서버 상태를 "
        "확인한 후 다시 실행해 보세요."
    )

    st.stop()


except ValueError:

    st.error("❌ KOBIS API 응답을 읽을 수 없습니다.")

    st.info(
        "KOBIS API에서 정상적인 JSON 데이터를 "
        "보내고 있는지 확인하세요."
    )

    st.stop()


# --------------------------------------------
# 10. KOBIS API 오류 확인
# --------------------------------------------
#
# 중요한 부분이다.
#
# KOBIS는 인증키가 틀려도 HTTP 상태코드가
# 200으로 반환될 수 있다.
#
# 따라서 response.raise_for_status()만 확인하면
# 인증키 오류를 발견하지 못할 수 있다.
#
# 응답 안에 faultInfo가 있는지도 확인한다.

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
        "• Streamlit Secrets의 이름이 KOBIS_KEY인지\n"
        "• 인증키가 정상적으로 발급되었는지"
    )

    st.stop()


# --------------------------------------------
# 11. boxOfficeResult 확인
# --------------------------------------------

if "boxOfficeResult" not in data:

    st.error("❌ 박스오피스 데이터를 찾을 수 없습니다.")

    st.info(
        "KOBIS API의 응답 형식이 정상인지 확인하거나 "
        "잠시 후 다시 시도해 보세요."
    )

    st.stop()


box_office_result = data["boxOfficeResult"]


# --------------------------------------------
# 12. 주말 박스오피스 영화 목록 가져오기
# --------------------------------------------

movie_list = box_office_result.get(
    "weeklyBoxOfficeList",
    []
)


# --------------------------------------------
# 13. 영화 목록이 비어 있는 경우
# --------------------------------------------

if not movie_list:

    st.warning(
        f"{display_date} 기준 주말 박스오피스 데이터가 없습니다."
    )

    st.info(
        "다음 내용을 확인해 보세요.\n\n"
        "• KOBIS에서 해당 주말의 박스오피스가 집계되었는지\n"
        "• KOBIS 인증키가 정상인지\n"
        "• 조회 날짜가 정상적으로 계산되었는지\n"
        "• KOBIS API 서버가 정상적으로 작동하는지\n\n"
        "잠시 후 다시 실행해 보는 것도 좋습니다."
    )

    st.stop()


# --------------------------------------------
# 14. 데이터프레임 만들기
# --------------------------------------------

df = pd.DataFrame(movie_list)


# --------------------------------------------
# 15. 필요한 데이터 확인
# --------------------------------------------

required_columns = [
    "rank",
    "rankInten",
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


# --------------------------------------------
# 16. 필요한 열만 선택
# --------------------------------------------

df = df[
    required_columns
].copy()


# --------------------------------------------
# 17. 한국어 이름으로 변경
# --------------------------------------------

df = df.rename(
    columns={
        "rank": "순위",
        "rankInten": "전주대비",
        "movieNm": "영화명",
        "openDt": "개봉일",
        "audiCnt": "주말관객수",
        "audiAcc": "누적관객",
        "scrnCnt": "스크린수"
    }
)


# --------------------------------------------
# 18. 숫자 데이터 숫자형으로 변환
# --------------------------------------------
#
# KOBIS API에서는 숫자도 문자열로 전달될 수 있다.
# 따라서 그래프와 계산을 위해 숫자로 변환한다.

numeric_columns = [
    "순위",
    "전주대비",
    "주말관객수",
    "누적관객",
    "스크린수"
]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).astype(int)


# --------------------------------------------
# 19. 조회 기간 표시
# --------------------------------------------

show_range = box_office_result.get(
    "showRange",
    f"{display_date} 기준"
)


st.subheader("📅 조회 기간")

st.write(
    f"**{show_range}**"
)


# --------------------------------------------
# 20. 1위 영화 찾기
# --------------------------------------------

first_movie = df.iloc[0]


st.markdown("## 🏆 주말 박스오피스 1위")


# 3개의 카드 만들기
col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        label="영화명",
        value=str(first_movie["영화명"])
    )


with col2:

    st.metric(
        label="주말 관객수",
        value=f"{first_movie['주말관객수']:,}명"
    )


with col3:

    st.metric(
        label="누적 관객수",
        value=f"{first_movie['누적관객']:,}명"
    )


# --------------------------------------------
# 21. 전체 박스오피스 표
# --------------------------------------------

st.markdown("## 📋 주말 박스오피스 TOP 10")


# 원본 데이터는 숫자형으로 유지하고
# 화면에 보여줄 때만 쉼표를 넣는다.

display_df = df.copy()


display_df["전주대비"] = display_df["전주대비"].apply(
    lambda x: f"+{x}" if x > 0 else str(x)
)


display_df["주말관객수"] = display_df[
    "주말관객수"
].map(
    lambda x: f"{x:,}"
)


display_df["누적관객"] = display_df[
    "누적관객"
].map(
    lambda x: f"{x:,}"
)


display_df["스크린수"] = display_df[
    "스크린수"
].map(
    lambda x: f"{x:,}"
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------
# 22. 관객수 TOP 5 그래프
# --------------------------------------------

st.markdown("## 📊 관객수 TOP 5")


top5 = (
    df.sort_values(
        by="주말관객수",
        ascending=False
    )
    .head(5)
    .copy()
)


# 영화명을 인덱스로 설정해서
# 영화별 관객수 막대그래프를 만든다.

chart_data = top5.set_index(
    "영화명"
)[
    ["주말관객수"]
]


st.bar_chart(
    chart_data,
    x_label="영화",
    y_label="주말 관객수"
)


# --------------------------------------------
# 23. 데이터 출처
# --------------------------------------------

st.caption(
    "데이터 출처: 영화진흥위원회 영화관입장권통합전산망(KOBIS) 오픈API"
)
```
