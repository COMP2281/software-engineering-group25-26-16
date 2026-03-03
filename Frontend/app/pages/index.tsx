import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import '../styles/index.css';

export default function Welcome() {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/dashboard');
  };

  return (
    <div className="welcome_container">
      <div className="welcome_card">
        <h1>Granite Guardian</h1>
        <h2>{isLogin ? 'Welcome Back' : 'Create an Account'}</h2>
        
        <form onSubmit={handleSubmit} className="auth_form">
          {!isLogin && (
            <div className="form_group">
              <label>Full Name</label>
              <input type="text" required placeholder="Jane Doe" />
            </div>
          )}
          
          <div className="form_group">
            <label>Email Address</label>
            <input type="email" required placeholder="name@company.com" />
          </div>
          
          <div className="form_group">
            <label>Password</label>
            <input type="password" required placeholder="••••••••" />
          </div>

          <button type="submit" className="auth_button">
            {isLogin ? 'Log In' : 'Sign Up'}
          </button>
        </form>

        <div className="auth_toggle">
          <span>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
          </span>
          <button onClick={() => setIsLogin(!isLogin)} className="toggle_button">
            {isLogin ? 'Sign up here' : 'Log in here'}
          </button>
        </div>
      </div>
    </div>
  );
}