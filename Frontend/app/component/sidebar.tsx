import React from 'react';

function Side_bar({ activeSection, changeSection }) {
  return (
    <div className="sidebar">
      <div className="sidebar_header">
        <h2>Granite Guardian</h2>
      </div>
      <ul className="sidebar_menu">
        <li 
          className={activeSection === 'dashboard' ? 'sidebar_item active' : 'sidebar_item'}
          onClick={() => changeSection('dashboard')}
        >
          Dashboard
        </li>
        <li 
          className={activeSection === 'upload' ? 'sidebar_item active' : 'sidebar_item'}
          onClick={() => changeSection('upload')}
        >
          Upload
        </li>
        <li 
          className={activeSection === 'chatbot' ? 'sidebar_item active' : 'sidebar_item'}
          onClick={() => changeSection('chatbot')}
        >
          Chatbot
        </li>
      </ul>
    </div>
  );
}

export default Side_bar;