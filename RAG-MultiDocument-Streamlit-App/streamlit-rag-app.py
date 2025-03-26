import streamlit as st
from datetime import datetime
import os
import json
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage


from rag_utils import (
    load_documents, 
    get_retriever, 
    query_documents, 
    get_local_model, 
    prompt_ai,
    RAG_DIRECTORY
    )

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content=f"You are a personal assistant who answers questions based on the context provided if the provided context can answer the question. You only provide the answer to the question/user input and nothing else. The current date is: {datetime.now().date()}")
        ]
    
    if "rag_directory" not in st.session_state:
        st.session_state.rag_directory = "uploads"

def file_uploader():
    """
    Streamlit file uploader for documents to be used in RAG.
    Supports PDF and txt files.
    """
    st.sidebar.header("Document Upload")
    uploaded_files = st.sidebar.file_uploader(
        "Upload Documents", 
        type=['pdf', 'txt'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Create directory if it doesn't exist
        os.makedirs(st.session_state.rag_directory, exist_ok=True)
        
        # Save uploaded files
        for uploaded_file in uploaded_files:
            file_path = os.path.join(st.session_state.rag_directory, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
        
        st.sidebar.success(f"Uploaded {len(uploaded_files)} files successfully!")
        
        # Reinitialize Chroma instance with new documents
        st.cache_resource.clear()
        #get_chroma_instance()
        get_retriever()
        #st.experimental_rerun()
        #st.rerun()

def display_chat_history():
    """Display chat history from session state."""
    for message in st.session_state.messages:
        message_json = json.loads(message.json())
        message_type = message_json["type"]
        #if message_type in ["human", "ai", "system"]:
        if message_type in ["human", "ai"]:
            with st.chat_message(message_type):
                st.markdown(message_json["content"])

def cleanup_directory(directory):
    """
    Remove all files in the specified directory.
    
    Args:
        directory (str): Path to the directory to be cleaned
    """
    try:
        # Check if directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)
            return

        # Remove all files and subdirectories
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                st.error(f"Failed to delete {file_path}. Reason: {e}")

        st.sidebar.info("Previous uploaded files have been cleared.")
    except Exception as e:
        st.error(f"Error during cleanup: {e}")

def main():
    st.set_page_config(page_title="Local Document RAG Chatbot", page_icon="📄")
    st.title("💬 Document RAG Chatbot")

    # Cleanup directory when app starts
    cleanup_directory(RAG_DIRECTORY)
    
    # Initialize session state
    initialize_session_state()
    
    # File uploader sidebar
    file_uploader()
    
    # Display chat history
    display_chat_history()
    
    # User input
    if prompt := st.chat_input("What questions do you have about your documents?"):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append(HumanMessage(content=prompt))

        # Get AI response
        with st.chat_message("assistant"):
            try:
                ai_response = prompt_ai(st.session_state.messages)
                st.markdown(ai_response.content)
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.warning("Make sure you have uploaded documents and have a valid model.")
        
        st.session_state.messages.append(ai_response)

if __name__ == "__main__":
    main()
