// frontend/package.json
{
  "name": "multi-agent-arithmetic-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "uuid": "^9.0.1",
    "lucide-react": "^0.263.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.1.0",
    "eslint": "^8.53.0",
    "eslint-plugin-react": "^7.33.2",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "vite": "^4.5.0"
  }
}

// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000
  }
})

// frontend/src/services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'http://localhost:8000' 
  : 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatAPI = {
  sendMessage: async (message, conversationId = null) => {
    try {
      const response = await api.post('/chat', {
        message,
        conversation_id: conversationId
      });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error(error.response?.data?.detail || 'Failed to send message');
    }
  },

  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'unhealthy' };
    }
  }
};

// frontend/src/components/ConversationHistory.jsx
import React from 'react';
import { Calculator, User, Bot, Clock } from 'lucide-react';

const ConversationHistory = ({ conversations, onClearHistory }) => {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const renderCalculations = (calculations) => {
    if (!calculations || calculations.length === 0) return null;

    return (
      <div className="mt-2 p-2 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-1 text-sm text-gray-600 mb-1">
          <Calculator size={14} />
          <span>Calculations:</span>
        </div>
        {calculations.map((calc, idx) => (
          <div key={idx} className="text-xs text-gray-700 font-mono">
            {calc.operation}: [{calc.operands.join(', ')}] = {calc.result}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <Clock size={20} />
          Conversation History
        </h2>
        {conversations.length > 0 && (
          <button
            onClick={onClearHistory}
            className="text-sm text-red-600 hover:text-red-800 transition-colors"
          >
            Clear History
          </button>
        )}
      </div>
      
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {conversations.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No conversations yet. Start by asking a mathematical question!
          </p>
        ) : (
          conversations.map((conv, index) => (
            <div key={index} className="border-l-4 border-blue-200 pl-4">
              <div className="flex items-start gap-2 mb-2">
                <User size={16} className="text-blue-600 mt-1" />
                <div className="flex-1">
                  <p className="text-gray-800">{conv.userMessage}</p>
                  <span className="text-xs text-gray-500">{formatTime(conv.timestamp)}</span>
                </div>
              </div>
              
              <div className="flex items-start gap-2 ml-4">
                <Bot size={16} className="text-green-600 mt-1" />
                <div className="flex-1">
                  <p className="text-gray-700">{conv.botResponse}</p>
                  {renderCalculations(conv.calculations)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ConversationHistory;

// frontend/src/components/ChatInterface.jsx
import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { chatAPI } from '../services/api';

const ChatInterface = ({ onNewMessage }) => {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [conversationId, setConversationId] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const health = await chatAPI.healthCheck();
      setConnectionStatus(health.status === 'healthy' ? 'connected' : 'disconnected');
    } catch (error) {
      setConnectionStatus('disconnected');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage('');
    setError(null);
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(userMessage, conversationId);
      
      // Set conversation ID for subsequent messages
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      // Add to conversation history
      onNewMessage({
        userMessage,
        botResponse: response.response,
        calculations: response.calculations,
        reasoningSteps: response.reasoning_steps,
        timestamp: new Date().toISOString(),
        conversationId: response.conversation_id
      });

    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'disconnected':
        return <AlertCircle size={16} className="text-red-500" />;
      default:
        return <Loader2 size={16} className="text-yellow-500 animate-spin" />;
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Checking...';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-800">
          Multi-Agent Calculator
        </h1>
        <div className="flex items-center gap-2 text-sm">
          {getStatusIcon()}
          <span className={`${
            connectionStatus === 'connected' ? 'text-green-600' : 
            connectionStatus === 'disconnected' ? 'text-red-600' : 'text-yellow-600'
          }`}>
            {getStatusText()}
          </span>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-gray-600 text-sm">
          Ask me to perform mathematical calculations! I can handle addition, subtraction, 
          multiplication, division, and complex expressions with proper order of operations.
        </p>
        <div className="mt-2 text-xs text-gray-500">
          <strong>Examples:</strong> "What's 5 + 3?", "Calculate (10 - 4) * 2", "Divide 20 by 4"
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle size={16} />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter your mathematical question..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading || connectionStatus !== 'connected'}
          />
          <button
            type="submit"
            disabled={isLoading || !message.trim() || connectionStatus !== 'connected'}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Send size={16} />
                Send
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;

// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import ConversationHistory from './components/ConversationHistory';
import { v4 as uuidv4 } from 'uuid';

function App() {
  const [conversations, setConversations] = useState([]);

  // Load conversation history from localStorage on component mount
  useEffect(() => {
    const savedConversations = localStorage.getItem('arithmetic-conversations');
    if (savedConversations) {
      try {
        setConversations(JSON.parse(savedConversations));
      } catch (error) {
        console.error('Error loading saved conversations:', error);
      }
    }
  }, []);

  // Save conversations to localStorage whenever conversations change
  useEffect(() => {
    localStorage.setItem('arithmetic-conversations', JSON.stringify(conversations));
  }, [conversations]);

  const handleNewMessage = (messageData) => {
    setConversations(prev => [...prev, {
      id: uuidv4(),
      ...messageData
    }]);
  };

  const handleClearHistory = () => {
    setConversations([]);
    localStorage.removeItem('arithmetic-conversations');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <ChatInterface onNewMessage={handleNewMessage} />
          </div>
          <div>
            <ConversationHistory 
              conversations={conversations}
              onClearHistory={handleClearHistory}
            />
          </div>
        </div>
        
        <footer className="mt-8 text-center text-sm text-gray-600">
          <p>Multi-Agent Arithmetic System powered by LangGraph, FastAPI, and React</p>
        </footer>
      </div>
    </div>
  );
}

export default App;

// frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// frontend/src/index.css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

/* Custom scrollbar styles */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}