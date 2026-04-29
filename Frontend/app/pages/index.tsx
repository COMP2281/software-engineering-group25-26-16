import React, { useState } from "react";
import { useNavigate } from "react-router";
import { Shield, Mail, Lock, ArrowRight, User } from "lucide-react";
import "../styles/index.css"; // Uses the exact same CSS we wrote earlier!

export default function Index() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);

  // Our three pieces of form data
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Assuming your Caddy server routes to your FastAPI backend.
    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";

    // If logging in, we only send email and password. If signing up, we send all three.
    const payload = isLogin
      ? { email, password }
      : { username, email, password };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        // Success! Send them into the app.
        navigate("/dashboard");
      } else {
        // Handle incorrect passwords or taken usernames
        const data = await response.json();
        setError(data.detail || "Authentication failed. Please try again.");
      }
    } catch (err) {
      setError(
        "Cannot connect to the server. Make sure Caddy and FastAPI are running!",
      );
    }
  };

  return (
    <div className="index_container">
      {/* LEFT SIDE: Branding & Hero */}
      <div className="index_hero">
        <div className="hero_content">
          <Shield size={64} className="hero_icon" />
          <h1 className="hero_title">Granite Guardian</h1>
          <p className="hero_subtitle">
            Your intelligent, secure, and AI-powered car diagnostic companion.
          </p>
          <p className="hero_subtitle">
            Sign in to access your dashboard, upload OBD-II logs, and start
            chatting.
          </p>
        </div>
      </div>

      {/* RIGHT SIDE: Auth Form */}
      <div className="index_auth">
        <div className="auth_card">
          <h2>{isLogin ? "Welcome back" : "Create an account"}</h2>
          <p className="auth_description">
            {isLogin
              ? "Enter your details to access your account."
              : "Sign up to get started with Granite Guardian."}
          </p>

          {error && <div className="auth_error">{error}</div>}

          <form onSubmit={handleSubmit} className="auth_form">
            {/* USERNAME FIELD: Always visible */}
            {!isLogin && (
              <div className="input_group">
                <label>Username</label>
                <div className="input_wrapper input_wrapper_icon">
                  <User size={18} className="input_icon" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. mechanic_mike"
                  />
                </div>
              </div>
            )}

            {/* EMAIL FIELD: Always visible */}
            <div className="input_group fade_in">
              <label>Email</label>
              <div className="input_wrapper input_wrapper_icon">
                <Mail size={18} className="input_icon" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                />
              </div>
            </div>

            {/* PASSWORD FIELD: Always visible */}
            <div className="input_group">
              <label>Password</label>
              <div className="input_wrapper input_wrapper_icon">
                <Lock size={18} className="input_icon" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button type="submit" className="auth_submit">
              {isLogin ? "Sign In" : "Create Account"}
              <ArrowRight size={18} />
            </button>
          </form>

          {/* TOGGLE BUTTON */}
          <div className="auth_switch">
            <p>
              {isLogin
                ? "Don't have an account? "
                : "Already have an account? "}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError(""); // Clears out any red error boxes when switching views
                }}
              >
                {isLogin ? "Sign up" : "Log in"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
