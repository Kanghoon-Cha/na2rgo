import streamlit as st
import datetime
from PIL import Image
import tempfile
from deepface import DeepFace
from openai import OpenAI
import os

# ----------- OpenAI API 키 설정 -----------
api_key = st.secrets.get("openai_api_key")
if not api_key or api_key.startswith("YOUR_API_KEY"):
    st.error("🔐 OpenAI API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인하세요.")
    st.stop()
client = OpenAI(api_key=api_key)

# ----------- 세션 상태 초기화 -----------
if "page" not in st.session_state:
    st.session_state.page = "main"
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "tmp_path" not in st.session_state:
    st.session_state.tmp_path = None
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

# ----------- 페이지 전환 함수 -----------
def go_to_upload():
    st.session_state.page = "upload"
    st.rerun()

def go_to_result():
    st.session_state.page = "result"
    st.rerun()

def go_to_main():
    st.session_state.page = "main"
    st.rerun()

# ----------- GPT 피드백 생성 함수 -----------
def generate_youthfulness_feedback(age, emotion):
    prompt = f"""
    사용자의 얼굴을 분석한 결과 다음과 같습니다:
    - 추정 나이: {age}세
    - 현재 감정: {emotion}

    이 사람에게 더 젊어 보이기 위한 뷰티/피부관리/생활 습관 팁을 3가지 제안해 주세요.
    간결하고 실용적인 문장으로 작성해 주세요.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 피부미용 및 뷰티 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT 응답 오류: {e}"

# ----------- 메인 화면 -----------
def show_main():
    st.set_page_config(page_title="Na2Rgo - 나이알고", layout="centered")
    st.markdown("""
        <h1 style='text-align: center;'>Na2Rgo - 나이알고</h1>
        <p style='text-align: center;'>자신의 사진으로 나이를 추정해보아요!</p><br>
    """, unsafe_allow_html=True)

    with st.form("user_info_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("이름")
            birth = st.date_input("생년월일", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
        with col2:
            address = st.text_input("주소")
            hobby = st.text_input("취미")
        submitted = st.form_submit_button("정보 입력 완료")
        if submitted:
            st.session_state.user_info = {
                "name": name,
                "birth": str(birth),
                "address": address,
                "hobby": hobby
            }

    st.markdown("<h4>사진을 선택하는 방법을 골라주세요</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📷 카메라로 사진 찍기"):
            st.markdown("<p style='color:red;'>※ Streamlit은 카메라 촬영을 직접 지원하지 않으므로, 사진 업로드를 이용해주세요.</p>", unsafe_allow_html=True)
    with col2:
        if st.button("🖼 사진 파일 업로드"):
            go_to_upload()

# ----------- 업로드 화면 -----------
def show_upload():
    st.markdown("<h2>사진을 업로드하세요</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("사진 업로드", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드한 사진", use_container_width=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            image.save(tmp_file.name)
            st.session_state.tmp_path = tmp_file.name

    if st.session_state.tmp_path:
        if st.button("AI 분석 시작"):
            st.session_state.analyzed = True
            go_to_result()
    if st.button("⬅ 돌아가기"):
        go_to_main()

# ----------- 결과 화면 -----------
def show_result():
    st.markdown("<h2>분석 결과</h2>", unsafe_allow_html=True)
    if st.session_state.analyzed:
        with st.spinner('AI가 나이를 추정 중입니다...'):
            try:
                result = DeepFace.analyze(img_path=st.session_state.tmp_path, actions=['age', 'emotion'], enforce_detection=False)
                predicted_age = result[0]["age"]
                emotion = result[0]["dominant_emotion"]
                st.success(f"AI가 추정한 나이는 약 **{predicted_age}세** 입니다.")
                st.markdown(f"😐 현재 감정 상태는: **{emotion}**")
                st.markdown("---")
                st.markdown("<h4>✨ 더 어려 보이기 위한 AI 전문가의 제안:</h4>", unsafe_allow_html=True)
                feedback = generate_youthfulness_feedback(predicted_age, emotion)
                st.markdown(feedback)
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
        st.session_state.analyzed = False

    if st.button("다시 시작하기"):
        go_to_main()

# ----------- 라우팅 -----------
if st.session_state.page == "main":
    show_main()
elif st.session_state.page == "upload":
    show_upload()
elif st.session_state.page == "result":
    show_result()

# ----------- Footer -----------
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>YSK Company - 재미로 만든 AI Application</p>", unsafe_allow_html=True)