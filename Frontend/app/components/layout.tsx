import React, { useEffect } from "react";
import { Outlet } from "react-router";
import Sidebar from "./sidebar";
import "../styles/layout.css";

function Layout() {
  // check if signed in
  useEffect(() => {
    fetch("/api/auth/me", {
      method: "GET",
      credentials: "include",
    }).then((response) => {
      if (!response.ok) {
        window.location.href = "/"; // Redirect to home page if not signed in
      }
    });
  }, []);

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
