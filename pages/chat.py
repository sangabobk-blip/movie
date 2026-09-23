import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(page_title="겨울왕국 - 크리스토프", page_icon="❄️")
st.title("❄️ 위험한 바람의 남자, 크리스토프")

# 비밀 금고(secrets)에서 API 키를 꺼내 접속 준비
client = OpenAI(
    api_key=st.secrets["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 캐릭터 성격 설정 (바람처럼 자유롭고 비밀스러운 불륜 콘셉트의 크리스토프)
SYSTEM_PROMPT = (
    "너는 영화 디즈니 '겨울왕국'의 크리스토프야. "
    "단, 너는 한 사람에게 정착하지 못하고 자유로운 바람처럼 위험한 애정표현과 몰래 만나는 스릴을 즐기는 인물이야. "
    "순진하고 묵묵했던 평소 모습 뒤에, 상대를 매료시키는 능글맞고 자상하지만 어딘가 위험한 분위기를 풍겨. "
    "너는 차가운 얼음과 순록 스벤을 다루던 경험을 비유로 들며, 몰래 만나는 관계의 비밀스러움과 자극적인 감정을 은밀하게 표현해야 해. "
    "대화 상대에게 다정하면서도 묘하게 선을 넘나드는 바람 같은 태도로 답해줘."
)

# 대화 기록이 없으면 처음 한 번만 만들어 둔다
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# 지금까지의 대화를 말풍선으로 다시 그리기 (성격 문장은 숨김)
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 채팅 입력창
user_input = st.chat_input("크리스토프에게 은밀하게 말을 건네보세요...")

if user_input:
    # 보낸 말을 기록에 넣고 화면에도 그리기
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 답 받아오기
    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=st.session_state.messages,
                stream=True,
            )
            answer = st.write_stream(
                chunk.choices[0].delta.content or ""
                for chunk in stream if chunk.choices
            )
            # AI 답도 기록에 저장
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception:
            st.error("바람이 차갑게 불어와 소식이 닿지 않았어. 잠시 후 다시 시도해줘.")
