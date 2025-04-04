# Document RAG Chatbot

A Streamlit-based chatbot that uses Retrieval-Augmented Generation (RAG) to answer questions about uploaded documents.

## Features

- 📄 Support for PDF and TXT file uploads
- 🔍 Advanced document search using BGE embeddings
- 💬 Interactive chat interface
- 🤖 Powered by Groq LLM API
- 📊 FAISS vector store for efficient retrieval

## Prerequisites

- Python 3.8+
- pip package manager
- Groq API key

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd RAG-MultiDocument-Streamlit-App
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
DIRECTORY=uploads
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run streamlit-rag-app.py
```

2. Upload your documents using the sidebar
3. Ask questions about your documents in the chat interface

## Project Structure

```
RAG-MultiDocument-Streamlit-App
├── streamlit-rag-app.py    # Main Streamlit application
├── rag_utils.py           # RAG implementation utilities
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
└── uploads/             # Directory for uploaded documents
```

## Technologies Used

- Streamlit - Web interface
- LangChain - LLM framework
- FAISS - Vector storage
- HuggingFace BGE Embeddings - Document embeddings
- Groq - LLM provider

## Environment Variables

- `GROQ_API_KEY`: Your Groq API key
- `DIRECTORY`: Upload directory path (default: 'uploads')

## License

MIT

## Acknowledgments

- Built with LangChain
- Uses Groq's LLM API
- Powered by HuggingFace's BGE embeddings