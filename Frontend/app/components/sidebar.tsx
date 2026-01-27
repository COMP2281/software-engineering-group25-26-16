import React from 'react';
import { Link, useLocation } from 'react-router';
import '../styles/sidebar.css';
import { LayoutDashboard, Upload, MessageCircle } from 'lucide-react';

function Sidebar() {
  const location = useLocation();
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
          <LayoutDashboard size={18} />
          <span> Dashboard </span>
        </Link>
        
        <Link 
          to="/upload" 
          className={isActive('/upload') ? 'sidebar_link active' : 'sidebar_link'}
        >
          <Upload size={18} />
          <span> Upload </span>
        </Link>
        
        <Link 
          to="/chatbot" 
          className={isActive('/chatbot') ? 'sidebar_link active' : 'sidebar_link'}
        >
          <MessageCircle size={18} />
          <span> Chatbot </span>
        </Link>
      </nav>
    </div>
  );
}

export default Sidebar;