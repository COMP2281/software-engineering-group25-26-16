import React from 'react';
import { useNavigate } from 'react-router';
import '../styles/index.css';

export default function Welcome() {
  const navigate = useNavigate();

  const handleEnter = () => {
    // This bypasses login and pushes them straight into your App Layout
    navigate('/dashboard');
  };

  return (
    <div className="welcome_container">
      <div className="welcome_card">
        <h1>Granite Guardian</h1>
        <p className="subtitle">Welcome to Granite Guardian</p>
        
        <button onClick={handleEnter} className="auth_button">
          Enter System
        </button>
      </div>
    </div>
  );
}