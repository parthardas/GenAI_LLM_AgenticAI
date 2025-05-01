# Conversational Order Taking Cafe ChatBot

Salient updates compared to the older Cafe Order Chat Bot:

1. The order totaling is done now at the LLM by proper prompt tuning
2. Pydantic LLM output structure enforcement by output parsing
3. The Order total on the side bar now always shows the latest order total
4. Replaced Llama3.2-70B with mistralai/Mixtral-8x7B-Instruct-v0.1

Otehr details are as follows:
## 🌟 Features

- Interactive chat interface for placing orders
- Smart order processing and confirmation
- Receipt generation
- Conversation memory management
- Docker support for easy deployment

## 🛠️ Technology Stack

- Python 3.10
- Streamlit
- LangGraph
- Mistral on HuggingFace
- Pydantic
- Docker

## 📋 Prerequisites

- Python 3.10 or higher
- Docker (optional)
- API keys for:
  - HuggingFace
  
## 🚀 Getting Started

### Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Simplified-ReAct-Agent
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
```

5. Run the application:
```bash
streamlit run simplified-react-agent-cafe-order-bot.py
```

### Docker Setup

1. Build the Docker image:
```bash
docker build -t simplified-react-agent .
```

2. Run the container:
```bash
docker run -p 8501:8501 simplified-react-agent
```

## 📁 Project Structure

```
Simplified-HF-Mistral-Totalling-ReAct-Agent/
├── simplified-react-agent-cafe-order-bot.py  # Main application file
├── requirements.txt                # Python dependencies
├── Dockerfile                     # Docker configuration
├── .env                           # Environment variables (create this)
└── README.md                      # This file
```

## 💡 Usage

1. Open your browser and navigate to `http://localhost:8501`
2. Start a conversation with the chatbot
3. Place your order by following the prompts
4. Confirm your order
5. Receive your order receipt

## 🌐 Environment Variables

- `HUGGINGFACEHUB_API_TOKEN`: Your HuggingFace API token 

## 🐳 Docker Commands

Build the image:
```bash
docker build -t simplified-react-agent .
```

Run the container:
```bash
docker run -p 8501:8501 react-cafe-bot
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b /parthardas/DeepLearningNLPLLM`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin /parthardas/DeepLearningNLPLLM`)
5. Open a Pull Request

## DockerHub location

DockerHub Image: parthardas/simplified-react-agent

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Partha R Das

## 🙏 Acknowledgments

- Thanks to the Streamlit team for their amazing framework
- Thanks to the LangGraph community for their support