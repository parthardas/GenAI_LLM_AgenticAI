# Use Python 3.10 as a base image
#FROM python:3.13.1-slim
FROM python:3.10-slim

# Set environment variables to avoid caching issues with Hugging Face
ENV HF_HOME=/tmp/huggingface \
    TRANSFORMERS_CACHE=/tmp/huggingface/transformers \
    HF_DATASETS_CACHE=/tmp/huggingface/datasets \
    HUGGINGFACE_HUB_CACHE=/tmp/huggingface/hub \
    XDG_CACHE_HOME=/tmp/huggingface

# Set working directory
WORKDIR /app

# Copy files to the container
COPY requirements.txt streamlit-rag-app.py rag_utils.py ./

# Install dependencies and pre-download model
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "from transformers import AutoTokenizer, AutoModel; \
    AutoTokenizer.from_pretrained('BAAI/bge-large-en-v1.5'); \
    AutoModel.from_pretrained('BAAI/bge-large-en-v1.5')"

# Expose the port Streamlit runs on
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["streamlit", "run", "streamlit-rag-app.py", "--server.port=8501", "--server.address=0.0.0.0"]