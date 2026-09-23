
import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(
    page_title="친절한 AI 정보 선생님",
    page_icon="🤖"
)

st.title("🤖 AI 정보 선생님과의 대화")
st.write("궁금한 점이 있다면 무엇이든 물어보세요! 친절하게 설명해 드릴게요.")

# 1. Streamlit Secrets에서 API 키 가져오기
# (.streamlit/secrets.toml 파일의 GEMINI_API_KEY 값을 사용합니다)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API 키 설정이 올바르지 않습니다. 비밀 금고(secrets.toml)를 확인해 주세요.")
    st.stop()

# 2. OpenAI 호환 클라이언트 초기화 (Gemini 엔드포인트 연결)
client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# 3. AI 시스템 프롬프트 (선생님 페르소나 설정)
SYSTEM_PROMPT = {
    "role": "system",
    "content": "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. 어려운 말은 쉬운 말로 바꿔 주고, 반드시 순수 한국어로만 답해"
}

# 4. 세션 상태에 채팅 기록 저장소 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. 기존 대화 기록을 화면에 표시 (시스템 프롬프트 제외)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 입력 처리
if user_input := st.chat_input("질문을 입력하세요..."):
    # 사용자 메시지를 화면에 표시 및 세션 기록에 추가
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI의 응답을 출력할 말풍선 영역 생성
    with st.chat_message("assistant"):
        try:
            # API에 전달할 대화 목록 구성 (시스템 프롬프트 + 지금까지의 전체 대화)
            api_messages = [SYSTEM_PROMPT] + st.session_state.messages

            # Gemini API 호출 (스트리밍 방식)
            stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=api_messages,
                stream=True
            )

            # 실시간으로 글자가 흘러나오도록 출력 및 반환된 답변 수집
            full_response = st.write_stream(stream)

            # AI 답변을 세션 기록에 추가 (다음 대화 기억용)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception:
            # 요청 실패 시 예외 처리 (한 줄 한국어 안내 문구)
            st.warning("응답을 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
