import streamlit as st
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

groq_api_key=os.environ['GROQ_API_KEY']

llm=ChatGroq(model_name="llama3-70b-8192")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Chatbot with Memory")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Say something...")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate bot response (simple echo for now)
    #bot_response = f"You said: {user_input}"
    if input:= st.session_state.messages:
        bot_response=llm.invoke(input).content
    else:
        bot_response=llm.invoke(user_input).content

    # Add bot response to chat history
    st.session_state.messages.append({"role": "assistant", "content": bot_response})

    # Display bot response
    #with st.chat_message("assistant"):
    #    st.markdown(bot_response)

    # Display last chat
    #with st.chat_message(st.session_state.messages[-1]["role"]):
    with st.chat_message(st.session_state.messages[-2]["role"]):
        st.markdown(st.session_state.messages[-2]["content"])
    with st.chat_message(st.session_state.messages[-1]["role"]):
        st.markdown(st.session_state.messages[-1]["content"])

