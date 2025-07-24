import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
import re

load_dotenv()

# st.set_page_config(page_title="GenAI/ML Engineer interview questions – Powered by LLaMA3", page_icon=":books:", layout="wide")
# st.title("GenAI/ML Engineer interview questions – Powered by LLaMA3")

st.set_page_config(page_title="Python coding test – Powered by LLaMA3", page_icon=":books:", layout="wide")
st.markdown("<h3 style='font-size:1.5rem;'>Python coding test – Powered by LLaMA3</h3>", unsafe_allow_html=True)

# Initialize session state variables
if "next_question" not in st.session_state:
    if not hasattr(st.session_state, "next_question"):
        st.session_state.next_question = False
        st.session_state.init = True

if "score" not in st.session_state or not hasattr(st.session_state, "score"):
    st.session_state.score = 0
if "q_count" not in st.session_state or not hasattr(st.session_state, "q_count"):
    st.session_state.q_count = 0

if "previous_questions" not in st.session_state:
    if not hasattr(st.session_state, "previous_questions"):
        st.session_state.previous_questions = set()

groq_api_key = os.getenv("GROQ_API_KEY")
#llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)
llm = ChatGroq(model="llama3-70b-8192", temperature=0.3)


def generate_mcq(previous_questions):
    history_text = "\n".join(f"- {q}" for q in previous_questions if q)
    prompt = f"""You are testing an intermediate level candidate on Python knowledge \
for a Python coding test. Generate amultiple-choice question (MCQ) with code \
snippet which will have 4 options.
The question should be relevant to Python programming. The question should be clear \
and concise, with one correct answer and three distractors.
Randomize the order of the questions including the first question. DO NOT generate \
more than one question at a time and DO NOT repeat any of the previous \
questions which are given in the history. If you repeat, you will lose \
points. Here are the previous questions:
{history_text}

Format it exactly like this:

Question: <question text>
Code: '''<code with code snippet here enclosed by triple single quotes>'''
A. <option A>
B. <option B>
C. <option C>
D. <option D>
Answer: <correct option letter only>
Explanation: <short explanation>"""
    response = llm.invoke([SystemMessage(content=prompt)])
    return response.content

def parse_mcq(mcq_text):
    # Extract question
    q_match = re.search(r"Question:\s*(.*)", mcq_text)
    q = q_match.group(1).strip() if q_match else ""
    # Extract code snippet (multiline, enclosed by triple single quotes)
    code_match = re.search(r"Code:\s*'''(.*?)'''", mcq_text, re.DOTALL)
    code = code_match.group(1).strip() if code_match else ""
    # Extract options
    options = {}
    for opt in ["A", "B", "C", "D"]:
        opt_match = re.search(rf"{opt}\.\s*(.*)", mcq_text)
        if opt_match:
            options[opt] = opt_match.group(1).strip()
    # Extract answer
    answer_match = re.search(r"Answer:\s*([A-D])", mcq_text)
    answer = answer_match.group(1).strip() if answer_match else ""
    # Extract explanation
    explanation_match = re.search(r"Explanation:\s*(.*)", mcq_text, re.DOTALL)
    explanation = explanation_match.group(1).strip() if explanation_match else ""
    return q, code, options, answer, explanation

if st.session_state.next_question == True or st.session_state.init == True:
    st.session_state.init = False
    mcq_raw = generate_mcq(st.session_state.previous_questions)
    q, code, options, correct, explanation = parse_mcq(mcq_raw)
    st.session_state.current_mcq = (q, code, options, correct, explanation)
    st.session_state.next_question = False
    # Add the last question to history BEFORE generating the next one
    if "current_mcq" in st.session_state or hasattr(st.session_state, "current_mcq"):
        prev_q = st.session_state.current_mcq[0]  # Get the question text
        if prev_q:  # Ensure it's not empty
            if "previous_questions" not in st.session_state or not hasattr(st.session_state, "previous_questions"):
                st.session_state.previous_questions = set()
            # Add the question to the history
            if prev_q not in st.session_state.previous_questions:
                st.session_state.previous_questions.add(prev_q)

# Unpack the current MCQ
q, code, options, correct, explanation = st.session_state.current_mcq

st.markdown(f"**Q{st.session_state.q_count+1}:** {q}")
st.markdown(f"**Code:** {code}")
#st.session_state.submitted = False
user_answer = st.radio(
    "Choose your answer:",
    list(options.keys()),
    format_func=lambda x: f"{x}. {options[x]}",
    key="user_answer_radio",
    index=None  # No default selection
)

if st.button("Submit Answer"):
    st.session_state.q_count += 1
    #st.session_state.submitted = True

    selected_answer = st.session_state.user_answer_radio
    st.session_state.selected_answer = selected_answer
    st.session_state.show_explanation = True

#if st.session_state.get("show_explanation") or st.session_state.get("submitted"):

if st.session_state.get("show_explanation"):
    selected_answer = st.session_state.selected_answer
    if selected_answer == correct:
        st.success("✅ Correct!")
        st.markdown(f"**Your answer:** {selected_answer}. {options[selected_answer]}")
        if not st.session_state.get("score_updated", False):
            st.session_state.score += 1
            st.session_state.score_updated = True
    else:
        st.error(f"❌ Incorrect. Correct answer is {correct}.")
    st.markdown(f"**Explanation:** {explanation}")


    if st.button("Next Question"):
        st.session_state.next_question = True
        st.session_state.show_explanation = False
        st.session_state.score_updated = False  # Reset for next question   
        st.rerun()


st.markdown(f"**Score: {st.session_state.score} / {st.session_state.q_count}**")
