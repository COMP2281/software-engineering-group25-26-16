import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import { Shield, Mail, Lock, ArrowRight } from 'lucide-react';
import '../styles/index.css';

export default function Index() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Sending to Caddy on port 8080 (which forwards to FastAPI)
    const endpoint = isLogin ? '/api/login' : '/api/signup';

    try {
      // For now, if you just want to test the UI without the backend,
      // you can comment out the fetch and just use: navigate('/dashboard');
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        navigate('/dashboard');
      } else {
        const data = await response.json();
        setError(data.detail || 'Authentication failed. Please try again.');
      }
    } catch (err) {
      setError('Cannot connect to the server. Make sure Caddy and FastAPI are running!');
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
            Your intelligent, secure, and AI-powered data companion.
            Sign in to access your dashboard and start chatting.
          </p>
        </div>
      </div>

      {/* RIGHT SIDE: Auth Form */}
      <div className="index_auth">
        <div className="auth_card">
          <h2>{isLogin ? 'Welcome back' : 'Create an account'}</h2>
          <p className="auth_description">
            {isLogin ? 'Enter your details to access your account.' : 'Sign up to get started with Granite Guardian.'}
          </p>

          {error && <div className="auth_error">{error}</div>}

          <form onSubmit={handleSubmit} className="auth_form">
            <div className="input_group">
              <label>Email</label>
              <div className="input_wrapper">
                <Mail size={18} className="input_icon" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                />
              </div>
            </div>

            <div className="input_group">
              <label>Password</label>
              <div className="input_wrapper">
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
              {isLogin ? 'Sign In' : 'Create Account'}
              <ArrowRight size={18} />
            </button>
          </form>

          <div className="auth_switch">
            <p>
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button type="button" onClick={() => setIsLogin(!isLogin)}>
                {isLogin ? 'Sign up' : 'Log in'}
              </button>
            </p>
          </div>
        </div>
      </div>

    </div>
  );
}