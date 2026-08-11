import streamlit as st
import json
import os
import random
import time
from datetime import datetime


# =========================================================
# CONFIGURATION
# =========================================================

QUESTIONS_FILE = "questions.json"
HISTORY_FILE = "exam_history.json"
REPORT_FOLDER = "reports"

EXAM_TIME = 60
TOTAL_QUESTIONS = 10


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Online Examination System",
    page_icon="📝",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .question-box {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
    }

    .result-box {
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #ddd;
        text-align: center;
    }

    .timer {
        font-size: 30px;
        font-weight: bold;
        text-align: center;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

def initialize_session():

    defaults = {
        "page": "home",
        "student_name": "",
        "questions": [],
        "answers": {},
        "start_time": None,
        "exam_started": False,
        "exam_submitted": False,
        "result": None,
        "total_time": 0,
        "attempt_number": 1,
        "submitted_by_timeout": False
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


initialize_session()


# =========================================================
# FILE FUNCTIONS
# =========================================================

def load_questions():

    try:

        with open(
            QUESTIONS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except FileNotFoundError:

        st.error("questions.json file not found.")
        return []

    except json.JSONDecodeError:

        st.error("questions.json contains invalid JSON.")
        return []


def load_history():

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except FileNotFoundError:

        return []

    except json.JSONDecodeError:

        return []


def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            indent=4
        )


# =========================================================
# TIME FUNCTIONS
# =========================================================

def get_remaining_time():

    if st.session_state.start_time is None:
        return EXAM_TIME

    elapsed = time.time() - st.session_state.start_time

    remaining = EXAM_TIME - elapsed

    return max(0, int(remaining))


def format_time(seconds):

    seconds = int(seconds)

    minutes = seconds // 60

    seconds = seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


# =========================================================
# ATTEMPT DETECTION
# =========================================================

def get_previous_attempts(student_name):

    history = load_history()

    attempts = []

    for record in history:

        if record["student_name"].lower() == student_name.lower():

            attempts.append(record)

    return attempts


# =========================================================
# PREPARE EXAM
# =========================================================

def prepare_exam():

    questions = load_questions()

    if not questions:

        return []

    questions = questions.copy()

    random.shuffle(questions)

    questions = questions[:TOTAL_QUESTIONS]

    return questions


# =========================================================
# EVALUATION
# =========================================================

def evaluate_exam():

    questions = st.session_state.questions

    answers = st.session_state.answers

    correct = 0
    wrong = 0
    unanswered = 0

    question_results = []

    for question in questions:

        question_id = str(question["id"])

        correct_answer = question["answer"]

        student_answer = answers.get(question_id)

        if student_answer is None:

            unanswered += 1

            result = "Unanswered"

        elif student_answer == correct_answer:

            correct += 1

            result = "Correct"

        else:

            wrong += 1

            result = "Wrong"

        question_results.append(
            {
                "question_id": question["id"],
                "question": question["question"],
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                "result": result
            }
        )

    total_questions = len(questions)

    score = correct

    if total_questions > 0:

        accuracy = (
            correct / total_questions
        ) * 100

    else:

        accuracy = 0

    total_time = st.session_state.total_time

    time_efficiency = (
        (EXAM_TIME - total_time)
        / EXAM_TIME
    ) * 100

    time_efficiency = max(
        0,
        min(100, time_efficiency)
    )

    return {
        "score": score,
        "correct": correct,
        "wrong": wrong,
        "unanswered": unanswered,
        "accuracy": accuracy,
        "time_efficiency": time_efficiency,
        "question_results": question_results
    }


# =========================================================
# PERFORMANCE
# =========================================================

def get_performance(accuracy):

    if accuracy >= 90:

        return "Excellent"

    elif accuracy >= 75:

        return "Very Good"

    elif accuracy >= 60:

        return "Good"

    elif accuracy >= 40:

        return "Needs Improvement"

    else:

        return "Poor"


# =========================================================
# SAVE REPORT
# =========================================================

def save_report(result):

    if not os.path.exists(REPORT_FOLDER):

        os.makedirs(REPORT_FOLDER)

    student_name = st.session_state.student_name

    safe_name = ""

    for char in student_name:

        if char.isalnum():

            safe_name += char

        else:

            safe_name += "_"

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"{safe_name}_{timestamp}.txt"
    )

    filepath = os.path.join(
        REPORT_FOLDER,
        filename
    )

    report = f"""
========================================================
              ONLINE EXAMINATION REPORT
========================================================

Student Name       : {student_name}

Attempt Number     : {st.session_state.attempt_number}

Date & Time        : {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

--------------------------------------------------------

Score              : {result["score"]}/{len(st.session_state.questions)}

Correct Answers    : {result["correct"]}

Wrong Answers      : {result["wrong"]}

Unanswered         : {result["unanswered"]}

Accuracy           : {result["accuracy"]:.2f}%

Time Taken         : {format_time(st.session_state.total_time)}

Time Efficiency    : {result["time_efficiency"]:.2f}%

Performance        : {get_performance(result["accuracy"])}

Submission Type    : {
"Auto Submitted"
if st.session_state.submitted_by_timeout
else "Normal Submission"
}

========================================================
                  QUESTION ANALYSIS
========================================================
"""

    for item in result["question_results"]:

        report += f"""

Question ID       : {item["question_id"]}

Question          : {item["question"]}

Your Answer       : {item["student_answer"]}

Correct Answer    : {item["correct_answer"]}

Result            : {item["result"]}

--------------------------------------------------------
"""

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report)

    return filepath


# =========================================================
# SAVE HISTORY
# =========================================================

def save_exam_result(result):

    history = load_history()

    record = {

        "student_name":
            st.session_state.student_name,

        "attempt_number":
            st.session_state.attempt_number,

        "date_time":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "score":
            result["score"],

        "total_questions":
            len(st.session_state.questions),

        "correct":
            result["correct"],

        "wrong":
            result["wrong"],

        "unanswered":
            result["unanswered"],

        "accuracy":
            round(result["accuracy"], 2),

        "time_taken_seconds":
            round(
                st.session_state.total_time,
                2
            ),

        "time_efficiency":
            round(
                result["time_efficiency"],
                2
            ),

        "performance":
            get_performance(
                result["accuracy"]
            ),

        "submitted_by_timeout":
            st.session_state.submitted_by_timeout
    }

    history.append(record)

    save_history(history)


# =========================================================
# SUBMIT EXAM
# =========================================================

def submit_exam(timeout=False):

    if st.session_state.exam_submitted:

        return

    st.session_state.submitted_by_timeout = timeout

    if st.session_state.start_time:

        st.session_state.total_time = (
            time.time()
            - st.session_state.start_time
        )

    else:

        st.session_state.total_time = 0

    st.session_state.result = evaluate_exam()

    save_exam_result(
        st.session_state.result
    )

    save_report(
        st.session_state.result
    )

    st.session_state.exam_submitted = True

    st.session_state.exam_started = False

    st.session_state.page = "result"


# =========================================================
# HOME PAGE
# =========================================================

def home_page():

    st.markdown(
        '<div class="main-title">'
        '📝 Online Examination & Evaluation System'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Online Exam • Automatic Evaluation • Performance Analytics'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Questions",
            TOTAL_QUESTIONS
        )

    with col2:

        st.metric(
            "Exam Time",
            format_time(EXAM_TIME)
        )

    with col3:

        st.metric(
            "Evaluation",
            "Automatic"
        )

    st.divider()

    st.subheader("🎯 Project Features")

    st.write(
        """
        - ⏱️ Timed examination
        - 🔀 Random question shuffle
        - 📝 Multiple-choice questions
        - 🤖 Automatic evaluation
        - 📊 Score and accuracy
        - ⚡ Time efficiency
        - 📚 Exam history
        - 📄 Student report card
        - 🔁 Repeated attempt detection
        - 🚨 Automatic submission when time expires
        """
    )

    st.divider()

    if st.button(
        "🚀 Start Examination",
        type="primary",
        use_container_width=True
    ):

        st.session_state.page = "login"

        st.rerun()

    if st.button(
        "📚 View Exam History",
        use_container_width=True
    ):

        st.session_state.page = "history"

        st.rerun()


# =========================================================
# LOGIN PAGE
# =========================================================

def login_page():

    st.title("👨‍🎓 Student Information")

    name = st.text_input(
        "Enter Student Name"
    )

    if st.button(
        "Continue",
        type="primary"
    ):

        if not name.strip():

            st.error(
                "Please enter your name."
            )

            return

        name = name.strip()

        previous_attempts = (
            get_previous_attempts(name)
        )

        st.session_state.student_name = name

        st.session_state.attempt_number = (
            len(previous_attempts) + 1
        )

        if previous_attempts:

            st.warning(
                f"""
                ⚠️ Repeated Attempt Detected!

                {name} has already attempted
                this exam {len(previous_attempts)} time(s).
                """
            )

            st.info(
                "You can still continue with another attempt."
            )

        st.session_state.page = "instructions"

        st.rerun()

    if st.button("⬅️ Back"):

        st.session_state.page = "home"

        st.rerun()


# =========================================================
# INSTRUCTIONS PAGE
# =========================================================

def instructions_page():

    st.title("📋 Exam Instructions")

    st.info(
        f"""
        Welcome **{st.session_state.student_name}**!

        Please read the instructions before starting.
        """
    )

    st.subheader("Instructions")

    st.write(
        f"""
        1. Total questions: **{TOTAL_QUESTIONS}**
        2. Exam duration: **{EXAM_TIME} seconds**
        3. Each question has four options.
        4. Questions will appear in random order.
        5. Select one answer for each question.
        6. The exam will automatically submit when time expires.
        7. After submission, your score and accuracy will be calculated.
        8. Your attempt will be stored in exam history.
        9. A report card will automatically be generated.
        """
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🚀 Start Exam",
            type="primary",
            use_container_width=True
        ):

            questions = prepare_exam()

            if not questions:

                st.error(
                    "No questions available."
                )

                return

            st.session_state.questions = questions

            st.session_state.answers = {}

            st.session_state.start_time = time.time()

            st.session_state.exam_started = True

            st.session_state.exam_submitted = False

            st.session_state.submitted_by_timeout = False

            st.session_state.page = "exam"

            st.rerun()

    with col2:

        if st.button(
            "⬅️ Back",
            use_container_width=True
        ):

            st.session_state.page = "login"

            st.rerun()


# =========================================================
# EXAM PAGE
# =========================================================

def exam_page():

    remaining_time = get_remaining_time()

    # Automatic submission
    if remaining_time <= 0:

        submit_exam(timeout=True)

        st.rerun()

    # Header

    col1, col2, col3 = st.columns(3)

    with col1:

        st.write(
            f"👨‍🎓 **{st.session_state.student_name}**"
        )

    with col2:

        st.write(
            f"Questions: **{len(st.session_state.questions)}**"
        )

    with col3:

        if remaining_time <= 10:

            st.error(
                f"⏰ Time: {format_time(remaining_time)}"
            )

        else:

            st.warning(
                f"⏰ Time: {format_time(remaining_time)}"
            )

    st.progress(
        remaining_time / EXAM_TIME
    )

    st.divider()

    # Questions

    for index, question in enumerate(
        st.session_state.questions,
        start=1
    ):

        st.markdown(
            f"""
            <div class="question-box">

            <h3>
            Question {index}
            </h3>

            <p>
            {question["question"]}
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        question_id = str(
            question["id"]
        )

        options = list(
            question["options"].keys()
        )

        current_answer = (
            st.session_state.answers.get(
                question_id
            )
        )

        default_index = 0

        if current_answer in options:

            default_index = options.index(
                current_answer
            )

        answer = st.radio(
            "Select your answer:",
            options,
            format_func=lambda option:
                f"{option}. "
                f"{question['options'][option]}",
            index=default_index,
            key=f"question_{question_id}"
        )

        st.session_state.answers[
            question_id
        ] = answer

        st.divider()

    # Submit button

    if st.button(
        "✅ Submit Exam",
        type="primary",
        use_container_width=True
    ):

        submit_exam()

        st.rerun()

    # Refresh page every second
    time.sleep(1)

    st.rerun()


# =========================================================
# RESULT PAGE
# =========================================================

def result_page():

    result = st.session_state.result

    st.title("🎉 Examination Result")

    if st.session_state.submitted_by_timeout:

        st.error(
            "⏰ Time was over. Your exam was automatically submitted."
        )

    else:

        st.success(
            "✅ Your exam has been submitted successfully."
        )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Score",
            f"{result['score']}/{len(st.session_state.questions)}"
        )

    with col2:

        st.metric(
            "Accuracy",
            f"{result['accuracy']:.2f}%"
        )

    with col3:

        st.metric(
            "Time",
            format_time(
                st.session_state.total_time
            )
        )

    with col4:

        st.metric(
            "Efficiency",
            f"{result['time_efficiency']:.2f}%"
        )

    st.divider()

    performance = get_performance(
        result["accuracy"]
    )

    st.subheader(
        f"🏆 Performance: {performance}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.success(
            f"Correct: {result['correct']}"
        )

    with col2:

        st.error(
            f"Wrong: {result['wrong']}"
        )

    with col3:

        st.warning(
            f"Unanswered: {result['unanswered']}"
        )

    st.divider()

    st.subheader("📊 Question Analysis")

    for item in result["question_results"]:

        with st.expander(
            f"Question {item['question_id']} — "
            f"{item['result']}"
        ):

            st.write(
                f"**Question:** {item['question']}"
            )

            st.write(
                f"**Your Answer:** "
                f"{item['student_answer']}"
            )

            st.write(
                f"**Correct Answer:** "
                f"{item['correct_answer']}"
            )

            if item["result"] == "Correct":

                st.success("Correct Answer")

            elif item["result"] == "Wrong":

                st.error("Wrong Answer")

            else:

                st.warning("Not Answered")

    st.divider()

    st.info(
        """
        📄 Your report card has been generated
        and saved inside the `reports` folder.
        """
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "📚 View History",
            use_container_width=True
        ):

            st.session_state.page = "history"

            st.rerun()

    with col2:

        if st.button(
            "🏠 Home",
            use_container_width=True
        ):

            # Reset exam state

            st.session_state.page = "home"

            st.session_state.exam_started = False

            st.session_state.exam_submitted = False

            st.session_state.result = None

            st.rerun()


# =========================================================
# HISTORY PAGE
# =========================================================

def history_page():

    st.title("📚 Exam History")

    history = load_history()

    if not history:

        st.info(
            "No exam attempts found."
        )

    else:

        for index, record in enumerate(
            reversed(history),
            start=1
        ):

            with st.expander(
                f"👨‍🎓 {record['student_name']} "
                f"— Attempt {record['attempt_number']}"
            ):

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.write(
                        f"**Date:** {record['date_time']}"
                    )

                    st.write(
                        f"**Score:** "
                        f"{record['score']}/"
                        f"{record['total_questions']}"
                    )

                with col2:

                    st.write(
                        f"**Accuracy:** "
                        f"{record['accuracy']}%"
                    )

                    st.write(
                        f"**Performance:** "
                        f"{record['performance']}"
                    )

                with col3:

                    st.write(
                        f"**Time:** "
                        f"{format_time(record['time_taken_seconds'])}"
                    )

                    st.write(
                        f"**Efficiency:** "
                        f"{record['time_efficiency']}%"
                    )

    st.divider()

    if st.button(
        "🏠 Back to Home"
    ):

        st.session_state.page = "home"

        st.rerun()


# =========================================================
# ROUTING
# =========================================================

if st.session_state.page == "home":

    home_page()

elif st.session_state.page == "login":

    login_page()

elif st.session_state.page == "instructions":

    instructions_page()

elif st.session_state.page == "exam":

    exam_page()

elif st.session_state.page == "result":

    result_page()

elif st.session_state.page == "history":

    history_page()