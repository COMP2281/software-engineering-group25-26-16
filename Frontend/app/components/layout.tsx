import React from 'react';
import { Outlet } from 'react-router';
import Sidebar from './sidebar';
import '../styles/layout.css';

function Layout() {
  return (
    <div className="app_layout">
      <Sidebar />
      <main className="main_content">
        <Outlet />
      </main>
    </div>
  );
}
export default Layout;

