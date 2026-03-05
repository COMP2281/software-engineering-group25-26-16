import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot } from 'lucide-react';
import '../styles/pages.css';
import '../styles/chatbot.css'; // Make sure this is imported!

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

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim()) return;

    if (!hasStarted) {
      setHasStarted(true);
    }

    const newUserMsg: Message = { id: Date.now(), role: 'user', content: inputValue.trim() };
    setMessages((prev) => [...prev, newUserMsg]);
    setInputValue('');

    setTimeout(() => {
      const botMsg: Message = {
        id: Date.now() + 1,
        role: 'bot',
        content: `I am Granite Guardian. I received your message: "${newUserMsg.content}". How else can I assist you today?`
      };
      setMessages((prev) => [...prev, botMsg]);
    }, 1000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chatbot_page_container">

      {/* HEADER SECTION */}
      <div className={`chatbot_header ${hasStarted ? 'started' : 'centered'}`}>
        <h1 className="chatbot_main_title">Granite Chatbot</h1>

        {/* INITIAL SEARCH BAR (Center of screen) */}
        {!hasStarted && (
          <div className="chatbot_initial_search">
            <div className="search_input_wrapper">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
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

      {/* CHAT HISTORY AREA */}
      {hasStarted && (
        <div className="chatbot_history_area fade_in">
          <div className="chat_messages_container">
            {messages.map((msg) => (
              <div key={msg.id} className={`message_row ${msg.role}`}>

                <div className={`message_avatar ${msg.role}`}>
                  {msg.role === 'user' ? <User size={20} color="white" /> : <Bot size={20} color="white" />}
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

      {/* BOTTOM SEARCH BAR (Pinned to bottom) */}
      {hasStarted && (
        <div className="chatbot_bottom_search fade_in_up">
          <div className="search_input_wrapper bottom_wrapper">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Granite Chatbot..."
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