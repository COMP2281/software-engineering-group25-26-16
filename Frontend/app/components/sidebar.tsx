import React, { useState } from 'react';
import { Link, useLocation } from 'react-router';
import '../styles/sidebar.css';

import { LayoutDashboard, Upload, MessageCircle, Menu } from 'lucide-react';

function Sidebar() {
  const location = useLocation();

  const [isCollapsed, setIsCollapsed] = useState(false);

  function isActive(path: string) {
    return location.pathname === path;
  }

  return (

    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>

      <div className="sidebar_header">

        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
        >
          <Menu size={24} color="white" />
        </button>


        {!isCollapsed && <h2>Granite Guardian</h2>}
      </div>

      <nav className="sidebar_nav">
        <Link
          to="/"
          className={isActive('/') ? 'sidebar_link active' : 'sidebar_link'}
        >

          <LayoutDashboard size={20} />


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