import React, { useState } from "react";
import "../styles/pages.css";
import "../styles/dashboard.css";

const initialAlerts = [
  {
    id: 1,
    severity: "high",
    component: "Fuel Pump A",
    title: "Pressure Drop Detected",
    message:
      "Fuel pump A is showing a 15% drop in pressure over the last 2 hours. This could indicate a potential leak or valve failure.",
    recommendation:
      "Initiate emergency diagnostic scan and inspect the primary valve.",
  },
  {
    id: 2,
    severity: "medium",
    component: "Cooling System",
    title: "Temperature Fluctuation",
    message:
      "Coolant temperature is fluctuating outside optimal parameters by 3 degrees.",
    recommendation: "Verify coolant levels and monitor for the next hour.",
  },
];

function Dashboard() {
  const [alerts, setAlerts] = useState(initialAlerts);

  const dismissAlert = (id: number) => {
    setAlerts(alerts.filter((alert) => alert.id !== id));
  };

  return (
    <div className="page_container bg-main min-h-screen">
      <header
        style={{
          marginBottom: "40px",
          borderBottom: "1px solid #e0e0e0",
          paddingBottom: "20px",
        }}
      >
        <h1>
          Dashboard{" "}
          <span style={{ color: "var(--primary-color)" }}>Overview</span>
        </h1>
        <p style={{ color: "var(--secondary-text)", fontSize: "1.1rem" }}>
          Real-time vehicle health status and predictive maintenance alerts.
        </p>
      </header>

      <div
        className="summary_grid"
        style={{ marginBottom: "50px", gap: "30px" }}
      >
        <div
          className="summary_card"
          style={{
            borderTop: "4px solid var(--primary-color)",
            textAlign: "left",
            padding: "30px",
            background: "white",
            boxShadow: "var(--shadow-md)",
          }}
        >
          <h4
            style={{
              textTransform: "uppercase",
              letterSpacing: "1px",
              fontSize: "0.75rem",
              color: "var(--light-text)",
              fontWeight: "bold",
            }}
          >
            Active Alerts
          </h4>
          <div
            className="summary_number"
            style={{
              fontSize: "3.5rem",
              fontWeight: "800",
              marginTop: "10px",
              color: "var(--text-primary)",
            }}
          >
            {alerts.length}
          </div>
        </div>

        <div
          className="summary_card"
          style={{
            borderTop: "4px solid var(--danger-color)",
            textAlign: "left",
            padding: "30px",
            background: "white",
            boxShadow: "var(--shadow-md)",
          }}
        >
          <h4
            style={{
              textTransform: "uppercase",
              letterSpacing: "1px",
              fontSize: "0.75rem",
              color: "var(--light-text)",
              fontWeight: "bold",
            }}
          >
            Critical Issues
          </h4>
          <div
            className="summary_number critical"
            style={{
              fontSize: "3.5rem",
              fontWeight: "800",
              marginTop: "10px",
              color: "var(--danger-color)",
            }}
          >
            {alerts.filter((a) => a.severity === "high").length}
          </div>
        </div>
      </div>

      <div className="alerts_section">
        <h2
          style={{
            marginBottom: "25px",
            fontSize: "1.5rem",
            fontWeight: "700",
            color: "var(--text-primary)",
          }}
        >
          Recent Maintenance Alerts
        </h2>

        {alerts.length === 0 ? (
          <div
            className="no_alerts"
            style={{
              padding: "60px",
              borderRadius: "12px",
              textAlign: "center",
              background: "white",
              color: "var(--success-color)",
              boxShadow: "var(--shadow-sm)",
            }}
          >
            <p style={{ fontSize: "1.2rem", fontWeight: "600" }}>
              All systems normal. No active alerts!
            </p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert_card ${alert.severity}`}
              style={{
                background: "white",
                borderRadius: "12px",
                padding: "30px",
                marginBottom: "25px",
                boxShadow: "var(--shadow-md)",
                borderLeft: `6px solid ${alert.severity === "high" ? "var(--danger-color)" : "var(--warning-color)"}`,
                transition: "transform 0.2s ease",
              }}
            >
              <div
                className="alert_header"
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span
                  className="badge_component"
                  style={{
                    background: "#f1f5f9",
                    color: "#475569",
                    borderRadius: "6px",
                    padding: "6px 12px",
                    fontWeight: "bold",
                    fontSize: "0.8rem",
                  }}
                >
                  {alert.component}
                </span>
                <span
                  className="badge_severity"
                  style={{
                    backgroundColor:
                      alert.severity === "high"
                        ? "var(--danger-color)"
                        : "var(--warning-color)",
                    borderRadius: "20px",
                    padding: "4px 15px",
                    fontSize: "0.7rem",
                    fontWeight: "800",
                    color: "white",
                  }}
                >
                  {alert.severity.toUpperCase()}
                </span>
              </div>

              <h3
                className="alert_title"
                style={{
                  fontSize: "1.4rem",
                  fontWeight: "700",
                  marginTop: "15px",
                  color: "var(--text-primary)",
                }}
              >
                {alert.title}
              </h3>
              <p
                className="alert_message"
                style={{
                  fontSize: "1.05rem",
                  lineHeight: "1.6",
                  color: "var(--secondary-text)",
                  margin: "15px 0",
                }}
              >
                {alert.message}
              </p>

              <div
                className="recommendation_box"
                style={{
                  background: "#fffbeb",
                  borderLeft: "4px solid #f59e0b",
                  padding: "20px",
                  borderRadius: "8px",
                }}
              >
                <strong
                  style={{
                    color: "#92400e",
                    fontSize: "0.9rem",
                    textTransform: "uppercase",
                  }}
                >
                  Granite Recommendation:
                </strong>
                <p
                  style={{
                    color: "#b45309",
                    marginTop: "5px",
                    fontSize: "1rem",
                  }}
                >
                  {alert.recommendation}
                </p>
              </div>

              <div style={{ textAlign: "right", marginTop: "20px" }}>
                <button
                  className="button_mark_read"
                  onClick={() => dismissAlert(alert.id)}
                  style={{
                    background: "transparent",
                    border: "1px solid #cbd5e1",
                    color: "#64748b",
                    padding: "8px 20px",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontWeight: "600",
                    transition: "all 0.2s",
                  }}
                  onMouseOver={(e) =>
                    (e.currentTarget.style.background = "#f8fafc")
                  }
                  onMouseOut={(e) =>
                    (e.currentTarget.style.background = "transparent")
                  }
                >
                  Mark as Read
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Dashboard;

