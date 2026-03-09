import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot } from 'lucide-react';
import '../styles/pages.css';
import '../styles/chatbot.css'; 

interface Message {
  id: number;
  role: 'user' | 'bot';
  content: string;
}

export default function Chatbot() {
  const [hasStarted, setHasStarted] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const userText = inputValue.trim();
    if (!userText) return;

    if (!hasStarted) setHasStarted(true);

    const newUserMsg: Message = { id: Date.now(), role: 'user', content: userText };
    setMessages((prev) => [...prev, newUserMsg]);
    setInputValue('');

    const typingId = Date.now() + 1;
    setMessages((prev) => [...prev, { id: typingId, role: 'bot', content: '✨ Analyzing engine data with IBM Granite...' }]);

    try {
      // Points to your secure backend to keep the API Key hidden [cite: 388, 389]
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText }),
      });

      const data = await response.json();
      setMessages((prev) => prev.filter(m => m.id !== typingId).concat({
        id: Date.now(),
        role: 'bot',
        content: data.reply || "Analysis error."
      }));
    } catch (error) {
      setMessages((prev) => prev.filter(m => m.id !== typingId).concat({
        id: Date.now(),
        role: 'bot',
        content: "Server unreachable. Please check your diagnostic connection."
      }));
    }
  };

  return (
  <div className="chatbot_page_container">
    {/* This container handles the centering logic */}
    <div className={`chatbot_header ${hasStarted ? 'started' : 'centered'}`}>
      <h1 className="chatbot_main_title">
        Granite <span style={{ color: 'var(--primary-color)' }}>Guardian</span>
      </h1>
      
      {/* Search bar is ONLY here when centered at the start */}
      {!hasStarted && (
        <div className="chatbot_initial_search">
          <div className="search_input_wrapper">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask Granite Guardian anything..."
              className="search_input"
            />
            <button onClick={() => handleSend()} className="send_button">
              <Send size={24} />
            </button>
          </div>
        </div>
      )}
    </div>

    {/* Message area appears only after starting */}
    {hasStarted && (
      <div className="chatbot_history_area fade_in">
        <div className="chat_messages_container">
          {messages.map((msg) => (
            <div key={msg.id} className={`message_row ${msg.role}`}>
              <div className={`message_avatar ${msg.role}`}>
                {msg.role === 'user' ? <User size={20} color="white" /> : <Bot size={20} color="var(--primary-color)" />}
              </div>
              <div className={`message_bubble ${msg.role}`}>
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>
    )}

    {/* Bottom search bar appears only after starting */}
    {hasStarted && (
      <div className="chatbot_bottom_search fade_in_up">
        <div className="search_input_wrapper bottom_wrapper">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Message Granite Guardian..."
            className="search_input bottom_input"
          />
          <button onClick={() => handleSend()} className="send_button bottom_send">
            <Send size={20} />
          </button>
        </div>
      </div>
    )}
  </div>
  );
}