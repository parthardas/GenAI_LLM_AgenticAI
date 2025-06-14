// --- File: App.jsx ---
import { useState } from "react";
import './App.css';

function App() {
  const [userId, setUserId] = useState("");
  const [input, setInput] = useState("");
  const [chat, setChat] = useState([]);

  const submitQuery = async () => {
    const response = await fetch("http://localhost:8000/query", {
      method: "POST",
      //method: "get",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, user_input: input })
    });
    const data = await response.json();
    setChat([...chat, { q: input, a: data.response }]);
    setInput("");
  };

  return (
    <div>
      <h2>Banking Virtual Assistant</h2>
      <input placeholder="User ID" value={userId} onChange={e => setUserId(e.target.value)} />
      <textarea placeholder="Ask your question..." value={input} onChange={e => setInput(e.target.value)} />
      <button onClick={submitQuery}>Submit</button>
      <hr />
      <h3>Chat History</h3>
      {chat.map((msg, i) => (
        <div key={i}>
          <strong>You:</strong> {msg.q}<br />
          <strong>Assistant:</strong> {msg.a}<hr />
        </div>
      ))}
    </div>
  );
}

export default App;
