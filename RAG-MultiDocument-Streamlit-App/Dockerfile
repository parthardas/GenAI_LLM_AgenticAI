# Use Python 3.10 as a base image
FROM python:3.13.1-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY streamlit-rag-app.py .
COPY rag_utils.py .

# Expose the port Streamlit runs on
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["streamlit", "run", "streamlit-rag-app.py", "--server.port=8501", "--server.address=0.0.0.0"]