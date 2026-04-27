import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Plus, Trash2, Menu } from "lucide-react";

import "../styles/pages.css";
import "../styles/chatbot.css";

interface Message {
  id: number;
  role: "user" | "bot";
  content: string;
  created_at?: string;
}

interface ChatSession {
  id: number;
  title: string;
  created_at: string;
}

export default function Chatbot() {
  const [hasStarted, setHasStarted] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load saved chats when the page first opens
  useEffect(() => {
    loadSessions(true);
  }, []);

  // Always scroll to the newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addBotMessage = (text: string) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        role: "bot",
        content: text,
      },
    ]);
    setHasStarted(true);
  };

  const loadSessions = async (autoOpenLatest = false) => {
    try {
      const response = await fetch("/api/chat/sessions", {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        console.error("Failed to load chat sessions:", response.status);

        if (response.status === 401) {
          setSessions([]);
        }

        return;
      }

      const data = await response.json();
      setSessions(data);

      // open latest chat
      if (autoOpenLatest && data.length > 0) {
        const latestSessionId = data[0].id;
        setActiveSessionId(latestSessionId);
        setHasStarted(true);
        loadMessages(latestSessionId);
      }
    } catch (error) {
      console.error("Error loading sessions:", error);
    }
  };

  const loadMessages = async (sessionId: number) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        console.error("Failed to load messages:", response.status);

        if (response.status === 401) {
          addBotMessage("You are not logged in. Please sign in again.");
          return;
        }

        addBotMessage("Could not load previous chat messages.");
        return;
      }

      const data = await response.json();
      setMessages(data);
      setActiveSessionId(sessionId);
      setHasStarted(true);
    } catch (error) {
      console.error("Error loading messages:", error);
      addBotMessage("Error loading previous chat messages.");
    }
  };

  const createNewChat = async () => {
    try {
      const response = await fetch("/api/chat/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ title: "New Chat" }),
      });

      if (!response.ok) {
        console.error("Failed to create new chat:", response.status);

        if (response.status === 401) {
          addBotMessage("You are not logged in. Please sign in again.");
          return null;
        }

        addBotMessage(
          `Could not create a new chat. Server returned ${response.status}.`,
        );
        return null;
      }

      const newSession = await response.json();
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);
      setHasStarted(false);
      setInputValue("");
      return newSession.id;
    } catch (error) {
      console.error("Error creating chat:", error);
      addBotMessage("Error creating a new chat session.");
      return null;
    }
  };

  const deleteChat = async (sessionId: number) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!response.ok) {
        console.error("Failed to delete chat:", response.status);

        if (response.status === 401) {
          addBotMessage("You are not logged in. Please sign in again.");
          return;
        }

        addBotMessage(
          `Could not delete chat. Server returned ${response.status}.`,
        );
        return;
      }

      const updatedSessions = sessions.filter((s) => s.id !== sessionId);
      setSessions(updatedSessions);

      // If the deleted chat was open, move to another one if possible
      if (activeSessionId === sessionId) {
        if (updatedSessions.length > 0) {
          const nextSessionId = updatedSessions[0].id;
          setActiveSessionId(nextSessionId);
          loadMessages(nextSessionId);
        } else {
          setActiveSessionId(null);
          setMessages([]);
          setHasStarted(false);
        }
      }
    } catch (error) {
      console.error("Error deleting chat:", error);
      addBotMessage("Error deleting chat.");
    }
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const userText = inputValue.trim();
    if (!userText) return;

    let sessionId = activeSessionId;

    // If there is no active chat yet, create one first
    if (!sessionId) {
      sessionId = await createNewChat();

      if (!sessionId) {
        return;
      }
    }

    if (!hasStarted) setHasStarted(true);

    const userMsgId = Date.now();
    const typingId = userMsgId + 1;

    const newUserMsg: Message = {
      id: userMsgId,
      role: "user",
      content: userText,
    };

    // Show the user message immediately and a temporary loading message
    setMessages((prev) => [
      ...prev,
      newUserMsg,
      {
        id: typingId,
        role: "bot",
        content: "✨ Analyzing engine data with IBM Granite...",
      },
    ]);

    setInputValue("");

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          session_id: sessionId,
          message: userText,
        }),
      });

      if (!response.ok || !response.body) {
        const errorText = await response.text();
        console.error("Chat request failed:", response.status, errorText);

        let message = `Chat request failed. Server returned ${response.status}.`;

        if (response.status === 401) {
          message = "You are not logged in. Please sign in again.";
        }

        setMessages((prev) =>
          prev
            .filter((m) => m.id !== typingId)
            .concat({
              id: Date.now(),
              role: "bot",
              content: message,
            }),
        );

        return;
      }

      // append new message to the end
      setMessages((prev) =>
        prev
          .filter((m) => m.id !== typingId)
          .concat({
            id: Date.now(),
            role: "bot",
            content: "",
          }),
      );

      const stream_reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let result = "";

      while (true) {
        const { value, done } = await stream_reader.read();
        if (done) break;

        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          result += chunk;
        }

        setMessages((prev) => {
          let new_arr = [...prev];
          new_arr[prev.length - 1].content = result;
          return new_arr;
        });
      }

      // Refresh the sidebar in case the title changed
      loadSessions();
    } catch (error) {
      console.error("Chat request error:", error);

      setMessages((prev) =>
        prev
          .filter((m) => m.id !== typingId)
          .concat({
            id: Date.now(),
            role: "bot",
            content:
              "Server unreachable. Please check your diagnostic connection.",
          }),
      );
    }
  };

  return (
    <div className="chatbot_page_container">
      <div className={`chatbot_header ${hasStarted ? "started" : "centered"}`}>
        {hasStarted && (
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="sidebar_toggle_button"
            title="Toggle Sidebar"
          >
            <Menu size={24} />
          </button>
        )}

        <h1 className="chatbot_main_title">
          Granite{" "}
          <span style={{ color: "var(--primary-color)" }}>Guardian</span>
        </h1>

        {!hasStarted && (
          <div className="chatbot_initial_search">
            <div className="search_input_wrapper">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask Granite Guardian anything..."
                className="search_input"
              />
              <button
                onClick={() => handleSend()}
                className="send_button"
                aria-label="Send message"
                title="Send message"
              >
                <Send size={24} />
              </button>
            </div>
          </div>
        )}
      </div>

      {hasStarted && (
        <div className="chatbot_content_row">
          <aside className={`chat_sidebar ${!isSidebarOpen ? "closed" : ""}`}>
            <button
              onClick={createNewChat}
              className="new_chat_button"
              aria-label="Create new chat"
              title="Create new chat"
            >
              <Plus size={18} />
              <span>New Chat</span>
            </button>

            <div className="chat_sessions_list">
              {sessions.map((session) => (
                <div key={session.id} className="chat_session_row">
                  <button
                    onClick={() => loadMessages(session.id)}
                    className={`chat_session_button ${session.id === activeSessionId ? "active" : ""}`}
                    aria-label={`Open chat ${session.title}`}
                    title={session.title}
                  >
                    <span className="chat_session_title">{session.title}</span>
                  </button>

                  <button
                    onClick={() => deleteChat(session.id)}
                    className="delete_chat_button"
                    aria-label={`Delete chat ${session.title}`}
                    title="Delete chat"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </aside>

          <div className="chatbot_history_area fade_in chat_history_panel">
            <div className="chat_messages_container">
              {messages.map((msg) => (
                <div key={msg.id} className={`message_row ${msg.role}`}>
                  <div className={`message_avatar ${msg.role}`}>
                    {msg.role === "user" ? (
                      <User size={20} color="white" />
                    ) : (
                      <Bot size={20} color="var(--primary-color)" />
                    )}
                  </div>
                  <div className={`message_bubble ${msg.role}`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>
      )}

      {hasStarted && (
        <div
          className={`chatbot_bottom_search fade_in_up ${!isSidebarOpen ? "expanded" : ""}`}
        >
          <div className="search_input_wrapper bottom_wrapper">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Message Granite Guardian..."
              className="search_input bottom_input"
            />
            <button
              onClick={() => handleSend()}
              className="send_button bottom_send"
              aria-label="Send message"
              title="Send message"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
