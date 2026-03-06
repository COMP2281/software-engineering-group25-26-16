import React, { useState } from 'react';
import '../styles/pages.css';

// function for the dashboard (ill complete it later)
function Dashboard() {
  // 2. We use state so we can delete alerts later when clicking "Mark as Read"
  const [alerts, setAlerts] = useState(initialAlerts);

  // 3. A quick function to remove an alert from the screen
  const dismissAlert = (id: number) => {
    setAlerts(alerts.filter(alert => alert.id !== id));
  };

  return (
    <div className="page_container">
      <h1>Dashboard</h1>
      <p>dashboard content here!!</p>
    </div>
  );
}

export default Dashboard;


// in order to access the api from the fontend, jdois faire une request from api.localhost:8000/get_warning_log/ for example, and then use the data in the frontend to display it. I can also do a request to get the list of uploaded files, and then for each file, do a request to get the diagnostics for that file, and then display it in the frontend.
