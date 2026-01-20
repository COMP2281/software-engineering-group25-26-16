import React from 'react';
import { Link, useLocation } from 'react-router';
import '../styles/sidebar.css';

function Sidebar() {
  const location = useLocation();
  
  // to check if the link is active
  function isActive(path: string) {
    return location.pathname === path;
  }

  return (
    <div className="sidebar">
      <div className="sidebar_header">
        <h2>Granite Guardian</h2>
      </div>
      
      <nav className="sidebar_nav">
        <Link 
          to="/" 
          className={isActive('/') ? 'sidebar_link active' : 'sidebar_link'}
        >
          Dashboard
        </Link>
        
        <Link 
          to="/upload" 
          className={isActive('/upload') ? 'sidebar_link active' : 'sidebar_link'}
        >
          Upload
        </Link>
        
        <Link 
          to="/chatbot" 
          className={isActive('/chatbot') ? 'sidebar_link active' : 'sidebar_link'}
        >
          Chatbot
        </Link>
      </nav>
    </div>
  );
}

export default Sidebar;