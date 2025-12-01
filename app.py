import streamlit as st
import google.generativeai as genai
import json
import os

# 페이지 설정
st.set_page_config(page_title="KakaoTalk Python Automator", page_icon="💬", layout="wide")

# API 키 설정 (Streamlit Secrets에서 가져오거나 사이드바에서 입력)
api_key = os.environ.get("API_KEY")
if not api_key:
    with st.sidebar:
        api_key = st.text_input("Google API Key", type="password")
        st.markdown("[Get API Key](https://aistudio.google.com/app/apikey)")

if not api_key:
    st.warning("API Key를 입력해주세요.")
    st.stop()

genai.configure(api_key=api_key)

# 제목
st.title("💬 KakaoTalk Python Automator")
st.markdown("카카오톡 단체 메시지 발송을 위한 파이썬 자동화 스크립트 생성기")

# 레이아웃 분할
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 수신자 및 메시지 설정")
    
    # 수신자 목록 입력
    st.markdown("**수신자 목록** (PC 카카오톡 친구 이름과 정확히 일치해야 함)")
    
    # 세션 상태로 친구 목록 관리
    if "contacts" not in st.session_state:
        st.session_state.contacts = []
    
    new_contact = st.text_input("친구 이름 추가", placeholder="이름 입력 후 Enter")
    if new_contact:
        if new_contact not in st.session_state.contacts:
            st.session_state.contacts.append(new_contact)
        # 입력창 초기화를 위한 트릭은 복잡하므로 여기선 생략하거나 st.form 사용 권장
    
    # 추가된 목록 표시
    if st.session_state.contacts:
        st.write("현재 수신자:", ", ".join([f"`{name}`" for name in st.session_state.contacts]))
        if st.button("목록 초기화"):
            st.session_state.contacts = []
            st.rerun()
    else:
        st.info("수신자를 추가해주세요.")

    st.divider()

    # 메시지 작성
    st.markdown("**메시지 내용**")
    
    # AI 도우미
    with st.expander("✨ AI 메시지 도우미"):
        topic = st.text_input("주제 (예: 새해 인사, 회식 공지)")
        if st.button("메시지 자동 작성"):
            if topic:
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = f"Write a warm, natural KakaoTalk group message in Korean.\nContext: {topic}\nKeep it under 300 characters. Body only."
                    response = model.generate_content(prompt)
                    st.session_state.generated_msg = response.text.strip()
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    # 메시지 입력창 (AI가 생성한 내용이 있으면 기본값으로 사용)
    default_msg = st.session_state.get("generated_msg", "")
    message = st.text_area("전송할 메시지", value=default_msg, height=150)

with col2:
    st.subheader("2. 파이썬 스크립트 생성")
    
    generate_btn = st.button("🚀 스크립트 생성", type="primary", use_container_width=True)
    
    if generate_btn:
        if not st.session_state.contacts or not message.strip():
            st.error("수신자와 메시지를 모두 입력해주세요.")
        else:
            with st.spinner("AI가 코드를 작성 중입니다..."):
                try:
                    contact_names = ", ".join(st.session_state.contacts)
                    prompt = f"""
                    Create a Python script using 'pyautogui' and 'pyperclip' to automate sending a KakaoTalk message.
                    Target Contacts: [{contact_names}]
                    Message content: "{message}"
                    
                    Return ONLY raw JSON format: {{"code": "python code here", "explanation": "brief instructions in Korean"}}
                    """
                    
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                    
                    result = json.loads(response.text)
                    
                    st.success("생성 완료!")
                    
                    # 설명 표시
                    st.info(result['explanation'])
                    
                    # 코드 표시
                    st.code(result['code'], language='python')
                    
                except Exception as e:
                    st.error(f"스크립트 생성 실패: {e}")

# 사용법 안내
with st.expander("사용 가이드"):
    st.markdown("""
    1. **Python 설치**: 컴퓨터에 Python이 설치되어 있어야 합니다.
    2. **라이브러리 설치**: `pip install pyautogui pyperclip`
    3. **코드 실행**: 생성된 코드를 복사하여 파일로 저장 후 실행하세요.
    4. **주의**: 실행 중 마우스/키보드를 조작하지 마세요.
    """)
