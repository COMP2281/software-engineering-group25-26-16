import React, { useState } from 'react';
import '../styles/pages.css';
import '../styles/dashboard.css'; // Make sure to import your new CSS file!

// 1. Let's create some mock data to test your CSS
const initialAlerts = [
  {
    id: 1,
    severity: 'high',
    component: 'Fuel Pump A',
    title: 'Pressure Drop Detected',
    message: 'Fuel pump A is showing a 15% drop in pressure over the last 2 hours. This could indicate a potential leak or valve failure.',
    recommendation: 'Initiate emergency diagnostic scan and inspect the primary valve.'
  },
  {
    id: 2,
    severity: 'medium',
    component: 'Cooling System',
    title: 'Temperature Fluctuation',
    message: 'Coolant temperature is fluctuating outside optimal parameters by 3 degrees.',
    recommendation: 'Verify coolant levels and monitor for the next hour.'
  }
];

function Dashboard() {
  // 2. We use state so we can delete alerts later when clicking "Mark as Read"
  const [alerts, setAlerts] = useState(initialAlerts);

  // 3. A quick function to remove an alert from the screen
  const dismissAlert = (id: number) => {
    setAlerts(alerts.filter(alert => alert.id !== id));
  };

  return (
    <div className="page_container dashboard_container">
      <h1>Dashboard Overview</h1>

      {/* --- SUMMARY SECTION --- */}
      <div className="summary_section" style={{ marginBottom: '40px' }}>
        <h3>System Status</h3>
        <div className="summary_grid">
          <div className="summary_card">
            <h4>Active Alerts</h4>
            <div className="summary_number">{alerts.length}</div>
          </div>
          <div className="summary_card">
            <h4>Critical Issues</h4>
            <div className="summary_number critical">
              {alerts.filter(a => a.severity === 'high').length}
            </div>
          </div>
        </div>
      </div>

      {/* --- ALERTS SECTION --- */}
      <div className="alerts_section">
        <h3 style={{ marginBottom: '20px', color: '#2c3e50' }}>Recent Alerts</h3>

        {/* If there are no alerts, show your empty state */}
        {alerts.length === 0 ? (
          <div className="no_alerts">All systems normal. No active alerts!</div>
        ) : (
          /* Map through our data to create cards */
          alerts.map(alert => (
            <div key={alert.id} className={`alert_card ${alert.severity}`}>

              <div className="alert_header">
                <span className="badge_component">{alert.component}</span>
                {/* Dynamically coloring the badge based on severity */}
                <span
                  className="badge_severity"
                  style={{
                    backgroundColor: alert.severity === 'high' ? '#e74c3c' : '#f39c12'
                  }}
                >
                  {alert.severity.toUpperCase()}
                </span>
              </div>

              <h3 className="alert_title">{alert.title}</h3>
              <p className="alert_message">{alert.message}</p>

              <div className="recommendation_box">
                <strong>Recommendation:</strong>
                <p>{alert.recommendation}</p>
              </div>

              <button
                className="button_mark_read"
                onClick={() => dismissAlert(alert.id)}
              >
                Mark as Read
              </button>

            </div>
          ))
        )}
      </div>

    </div>
  );
}

export default Dashboard;