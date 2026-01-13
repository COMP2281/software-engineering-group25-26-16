import React, { useState } from 'react';
import Side_bar from './components/sidebar.tsx';
import Dashboard from './components/dashboard.tsx';
import './styles/global.css';

// Placeholders pour Upload et Chatbot
function Upload() {
  return (
    <div className="upload_container">
      <h2 className="section_title">Upload OBD-II Data</h2>
      <div className="placeholder_box">
        <p>Upload section coming soon</p>
      </div>
    </div>
  );
}

function Chatbot() {
  return (
    <div className="chatbot_container">
      <h2 className="section_title">Chatbot</h2>
      <div className="placeholder_box">
        <p>Chatbot coming soon</p>
      </div>
    </div>
  );
}

export default function App() {
  const [activeSection, setActiveSection] = useState('dashboard');
  
  function changeSection(newSection) {
    setActiveSection(newSection);
  }

  function renderContent() {
    if (activeSection === 'dashboard') return <Dashboard />;
    if (activeSection === 'upload') return <Upload />;
    if (activeSection === 'chatbot') return <Chatbot />;
    return <Dashboard />;
  }

  return (
    <div className="app_container">
      <Side_bar activeSection={activeSection} changeSection={changeSection} />
      
      <div className="main_content">
        <div className="header">
          <h1 className="header_title">
            {activeSection.charAt(0).toUpperCase() + activeSection.slice(1)}
          </h1>
        </div>
        
        <div className="content_area">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}