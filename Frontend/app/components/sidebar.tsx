import React, { useState } from 'react';
import { Link, useLocation } from 'react-router';
import '../styles/sidebar.css';
// Added 'Menu' icon for the toggle button
import { LayoutDashboard, Upload, MessageCircle, Menu } from 'lucide-react';

function Sidebar() {
  const location = useLocation();
  // 1. Create a state to track if the sidebar is collapsed
  const [isCollapsed, setIsCollapsed] = useState(false);

  function isActive(path: string) {
    return location.pathname === path;
  }

  return (
    // 2. Add a dynamic class based on the state
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>

      <div className="sidebar_header">
        {/* 3. Add a button to toggle the state */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
        >
          <Menu size={24} />
        </button>

        {/* 4. Only show the title if NOT collapsed */}
        {!isCollapsed && <h2>Granite Guardian</h2>}
      </div>

      <nav className="sidebar_nav">
        <Link
          to="/dashboard"
          className={isActive('/dashboard') ? 'sidebar_link active' : 'sidebar_link'}
        >
          <LayoutDashboard size={18} />
          {/* 5. Only show the text if NOT collapsed */}
          {!isCollapsed && <span> Dashboard </span>}
        </Link>

        <Link
          to="/upload"
          className={isActive('/upload') ? 'sidebar_link active' : 'sidebar_link'}
        >
          <Upload size={18} />
          {!isCollapsed && <span> Upload </span>}
        </Link>

        <Link
          to="/chatbot"
          className={isActive('/chatbot') ? 'sidebar_link active' : 'sidebar_link'}
        >
          <MessageCircle size={18} />
          {!isCollapsed && <span> Chatbot </span>}
        </Link>
      </nav>
    </div>
  );
}

export default Sidebar;