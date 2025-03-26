from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import CharacterTextSplitter
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import streamlit as st
import os
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    DirectoryLoader, 
    PyPDFLoader,  # Alternative PDF loader
    TextLoader
)

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

load_dotenv()

# Default model can be changed via environment variable
MODEL = os.getenv('LLM_MODEL', 'meta-llama/Meta-Llama-3.1-405B-Instruct')
RAG_DIRECTORY = os.getenv('DIRECTORY', 'uploads')

# from langchain_community.document_loaders import PyPDFLoader
# loader = PyPDFLoader("attention.pdf")
# docs = loader.load()
# docs

@st.cache_resource
def get_local_model():
    """
    Get the local LLM model from Groq.
    """

    # return HuggingFaceEndpoint(
    #     repo_id=MODEL,
    #     task="text-generation",
    #     max_new_tokens=1024,
    #     do_sample=False
    # )

    groq_api_key = os.getenv("GROQ_API_KEY")
    llm=ChatGroq(model_name="llama3-70b-8192")

    return llm

def load_documents(directory):
    """
    Load and split documents from the specified directory.
    Supports PDF and txt files with custom loaders.
    """
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Custom loader to handle different file types
    def pdf_loader(path):
        return PyPDFLoader(path).load()
    
    def txt_loader(path):
        return TextLoader(path, encoding='utf-8').load()
    
    # Load PDF and TXT files with their respective loaders
    pdf_docs = []
    txt_docs = []
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if filename.lower().endswith('.pdf'):
            try:
                pdf_docs.extend(pdf_loader(filepath))
            except Exception as e:
                print(f"Error loading PDF {filename}: {e}")
        
        elif filename.lower().endswith('.txt'):
            try:
                txt_docs.extend(txt_loader(filepath))
            except Exception as e:
                print(f"Error loading TXT {filename}: {e}")
    
    # Combine all documents
    documents = pdf_docs + txt_docs

    # Split the documents into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    return docs

@st.cache_resource
def get_retriever():
    """
    Create a FAISS vector store with document embeddings.
    
    Returns:
        FAISS Retriever: Initialized FAISS vector store
    """
    # Get the documents split into chunks
    docs = load_documents(RAG_DIRECTORY)

    # Create the open-source embedding function
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    #retriever=vectordb.as_retriever()
    #retriever

    # Load documents into Chroma
    #return Chroma.from_documents(docs, embedding_function)

    # Create the FAISS vector store
    #return FAISS.from_documents(docs,embedding_function)
    faiss_store = FAISS.from_documents(docs, embedding_function)
    return faiss_store

def query_documents(question):
    """
    Uses RAG to query documents for information to answer a question.
    
    Args:
        question (str): The question to search documents for
    
    Returns:
        list: Formatted list of matching document sources and contents
    """
    db = get_retriever()
    similar_docs = db.similarity_search(question, k=5)
    docs_formatted = list(map(lambda doc: f"Source: {doc.metadata.get('source', 'NA')}\nContent: {doc.page_content}", similar_docs))

    return docs_formatted

def prompt_ai(messages):
    """
    Generate AI response based on context retrieved from documents.
    
    Args:
        messages (list): Conversation history messages
    
    Returns:
        AIMessage: AI's response message
    """
    # Fetch the relevant documents for the query
    user_prompt = messages[-1].content
    retrieved_context = query_documents(user_prompt)
    formatted_prompt = f"Context for answering the question:\n{retrieved_context}\nQuestion/user input:\n{user_prompt}"    

    # Initialize the LLM
    llm = get_local_model()
    #doc_chatbot = ChatHuggingFace(llm=llm)
    
    # Generate AI response
    #ai_response = doc_chatbot.invoke(messages[:-1] + [HumanMessage(content=formatted_prompt)])
    ai_response = llm.invoke(messages[:-1] + [HumanMessage(content=formatted_prompt)])

    return ai_response
