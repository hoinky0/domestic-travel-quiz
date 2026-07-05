import json
from pathlib import Path

import streamlit as st


# 페이지 기본 설정
st.set_page_config(
    page_title="국내여행지 추천 퀴즈",
    page_icon="🧳",
    layout="centered",
)

DATA_FILE = Path(__file__).with_name("travel_data.json")
CORRECT_USER_ID = "travel"
CORRECT_PASSWORD = "1234"


# 캐싱 적용 부분:
# JSON 파일을 반복해서 읽지 않도록 데이터 불러오기 함수에 st.cache_data를 적용했습니다.
@st.cache_data
def load_travel_data(file_path: str) -> dict:
    """JSON 파일에서 퀴즈 질문과 여행지 정보를 불러옵니다."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def initialize_session_state() -> None:
    """앱에서 사용할 세션 상태의 초기값을 만듭니다."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "quiz_result" not in st.session_state:
        st.session_state.quiz_result = None
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}


def reset_quiz() -> None:
    """퀴즈 진행 상태와 선택한 답변을 처음 상태로 되돌립니다."""
    st.session_state.quiz_result = None
    st.session_state.current_question = 0
    st.session_state.quiz_answers = {}

    for key in list(st.session_state.keys()):
        if key.startswith("question_"):
            del st.session_state[key]


def show_login() -> None:
    """로그인 입력 화면을 보여주고 아이디와 비밀번호를 확인합니다."""
    st.subheader("🔐 로그인")
    st.info("퀴즈를 시작하려면 로그인해 주세요.")

    with st.form("login_form"):
        user_id = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")

        left, center, right = st.columns([1, 1, 1])
        login_button = center.form_submit_button(
            "로그인",
            use_container_width=True
        )

    if login_button:
        print(f"[LOG] 로그인 버튼 클릭됨 / 입력 ID: {user_id}", flush=True)

        if user_id == CORRECT_USER_ID and password == CORRECT_PASSWORD:
            print("[LOG] 로그인 성공", flush=True)
            st.session_state.logged_in = True
            st.success("로그인에 성공했습니다!")
            st.rerun()
        else:
            print("[LOG] 로그인 실패", flush=True)
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")


def calculate_scores(answers: list[dict], destinations: list[str]) -> dict:
    """사용자가 고른 답변의 여행지별 점수를 합산합니다."""
    scores = {destination: 0 for destination in destinations}

    for answer in answers:
        for destination, point in answer["scores"].items():
            scores[destination] += point

    return scores


def show_result(scores: dict, results: dict) -> None:
    """가장 높은 점수를 받은 추천 여행지와 상세 정보를 보여줍니다."""
    # 동점이면 JSON의 destinations 순서에서 앞선 여행지를 추천합니다.
    recommended_place = max(scores, key=scores.get)
    travel_info = results[recommended_place]

    st.subheader("🎉 나의 추천 여행지")
    st.success(f"당신에게 어울리는 국내여행지는 **{recommended_place}**입니다!")

    st.markdown(f"### {travel_info['emoji']} {recommended_place}")
    st.write(f"**추천 이유:** {travel_info['reason']}")
    st.write("**추천 코스:**")
    for index, course in enumerate(travel_info["course"], start=1):
        st.write(f"{index}. {course}")

    st.write("**점수 계산 결과:**")
    score_columns = st.columns(len(scores))
    for column, (destination, score) in zip(score_columns, scores.items()):
        column.metric(destination, f"{score}점")

    empty_area, retry_area = st.columns([4, 2])

    with retry_area:
        if st.button("퀴즈 다시 하기", use_container_width=True):
            print("[LOG] 퀴즈 다시 하기 버튼 클릭됨", flush=True)
            reset_quiz()
            st.rerun()


def show_quiz(data: dict) -> None:
    """질문을 한 페이지에 하나씩 보여주고 여행지를 추천합니다."""

    if st.session_state.quiz_result is not None:
        show_result(st.session_state.quiz_result, data["results"])
        return

    questions = data["questions"]
    question_index = st.session_state.current_question
    question = questions[question_index]
    question_number = question_index + 1

    st.subheader("📝 여행 취향 퀴즈")
    st.write("각 질문에서 나와 가장 가까운 답변을 골라주세요.")
    st.progress(question_number / len(questions))
    st.caption(f"{question_number} / {len(questions)}")

    # 질문을 이미지 위에 크게 표시
    st.markdown(
        f"""
        <div style="
            font-size: 22px;
            font-weight: 700;
            margin-top: 18px;
            margin-bottom: 12px;
        ">
            Q{question_number}. {question['question']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    image_path = DATA_FILE.parent / question["image"]
    st.image(str(image_path), use_container_width=True)

    option_texts = [option["text"] for option in question["options"]]

    saved_answer = st.session_state.quiz_answers.get(str(question["id"]))
    if saved_answer is not None:
        default_index = option_texts.index(saved_answer["text"])
    else:
        default_index = None

    selected_text = st.radio(
        "답변 선택",
        option_texts,
        index=default_index,
        key=f"question_{question['id']}",
        label_visibility="collapsed",
    )

    previous_area, next_area = st.columns(2)

    previous_button = previous_area.button(
        "← 이전 질문",
        use_container_width=True,
        disabled=question_index == 0,
    )

    if question_number == len(questions):
        next_button = False
        result_button = next_area.button(
            "여행지 추천받기",
            use_container_width=True,
        )
    else:
        next_button = next_area.button(
            "다음 질문 →",
            use_container_width=True,
        )
        result_button = False

    if previous_button:
        print(f"[LOG] 이전 질문 버튼 클릭됨 / 현재 Q{question_number}", flush=True)
        st.session_state.current_question -= 1
        st.rerun()

    if next_button or result_button:
        print(
            f"[LOG] Q{question_number} 버튼 클릭됨 / 선택 답변: {selected_text}",
            flush=True
        )

        if selected_text is None:
            print(f"[LOG] Q{question_number} 답변 미선택", flush=True)
            st.warning("답변을 선택한 후 다음으로 넘어가 주세요.")
            return

        selected_option = next(
            option for option in question["options"]
            if option["text"] == selected_text
        )

        st.session_state.quiz_answers[str(question["id"])] = selected_option

        if next_button:
            st.session_state.current_question += 1
            st.rerun()

        if result_button:
            print("[LOG] 여행지 추천받기 버튼 클릭됨", flush=True)

            unanswered_numbers = [
                index
                for index, item in enumerate(questions, start=1)
                if str(item["id"]) not in st.session_state.quiz_answers
            ]

            if unanswered_numbers:
                number_text = ", ".join(
                    f"{number}번" for number in unanswered_numbers
                )
                st.warning(f"선택하지 않은 문항: {number_text}")
                st.info("모든 문항에 답한 후 다시 눌러주세요.")
                return

            selected_answers = [
                st.session_state.quiz_answers[str(item["id"])]
                for item in questions
            ]

            st.session_state.quiz_result = calculate_scores(
                selected_answers,
                data["destinations"]
            )
            print(f"[LOG] 퀴즈 결과 계산 완료 / 점수: {st.session_state.quiz_result}", flush=True)
            st.rerun()


def main() -> None:
    """앱의 전체 화면 흐름을 관리합니다."""
    initialize_session_state()

    st.title("🧳 국내여행지 추천 퀴즈")
    student_info, logout_area = st.columns([5, 1])
    student_info.write("**학번: 202630009 | 이름: 곽인경**")

    if st.session_state.logged_in:
        with logout_area:
            if st.button("로그아웃", use_container_width=True):
                print("[LOG] 로그아웃 버튼 클릭됨", flush=True)
                st.session_state.logged_in = False
                reset_quiz()
                st.rerun()

    st.divider()

    if not st.session_state.logged_in:
        show_login()
        return

    try:
        travel_data = load_travel_data(str(DATA_FILE))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        st.error(f"여행 데이터를 불러오지 못했습니다: {error}")
        return

    show_quiz(travel_data)


if __name__ == "__main__":
    main()
