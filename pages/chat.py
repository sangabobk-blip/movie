import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(page_title="서지(Surge)와 대화하기", page_icon="🤖")
st.title("🤖 서지(Surge)와 대화하기!")

# 비밀 금고(secrets)에서 API 키를 꺼내 접속 준비
client = OpenAI(
    api_key=st.secrets["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 서지(Surge)의 성격 설정
SYSTEM_PROMPT = (
    "너는 브롤스타즈의 캐릭터 '서지(Surge)'야. "
    "에너지가 넘치고 파티를 좋아하는 귀여운 로봇 말투로 대화해줘. "
    "중간중간 '삐-빅!', '치익-', '서지 파워!', '주스 충전 완료!' 같은 로봇 효과음이나 서지의 대사를 섞어서 흥분되고 신나게 말해야 해. "
    "친절하면서도 엄청 밝고 통통 튀는 캐릭터성을 유지해줘."
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
user_input = st.chat_input("서지에게 말을 걸어보세요! (예: 안녕 서지!)")

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
            st.error("치익- 삐-빅! 에너지 충전 실패... 잠시 후 다시 시도해줘!")
