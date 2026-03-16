import React, { useEffect, useMemo, useState } from "react";
import "../styles/pages.css";
import "../styles/dashboard.css";
import type { FileStats } from "~/types";
import { Button } from "~/components/button";
import Diagnostics, { run_diagnostics } from "./diagnostics";

function Dashboard() {
  const [fileStats, setFileStats] = useState<FileStats[]>([]);
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);

  function loadFileStats() {
    // load file stats
    fetch("/api/diagnostics/stats", {
      method: "GET",
      credentials: "include",
    })
      .then((response) => response.json())
      .then(setFileStats)
      .catch((error) => console.error("Error fetching stats:", error));
  }

  useEffect(loadFileStats, []);

  let fileStatsDiagnosticsRanSorted = useMemo(() => {
    if (!fileStats) return [];
    return fileStats
      .filter((stat) => stat.diagnostics_ran)
      .sort((a, b) => b.warning_count - a.warning_count);
  }, [fileStats]);

  let fileStatsDiagnosticsNotRan = useMemo(() => {
    if (!fileStats) return [];
    return fileStats.filter((stat) => !stat.diagnostics_ran);
  }, [fileStats]);

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

        <div className="flex gap-4 flex-row">
          <div className="flex gap-2 flex-col flex-1">
            {fileStats &&
              fileStatsDiagnosticsRanSorted.map((stat) => (
                <div className="diagnostic_card border-primary">
                  <h2>{stat.filename}</h2>
                  <p>
                    {stat.warning_count}{" "}
                    {stat.warning_count == 1 ? "warning" : "warnings"}
                  </p>
                </div>
              ))}
          </div>

          <div className="flex gap-2 flex-col flex-1">
            {fileStats &&
              fileStatsDiagnosticsNotRan.map((stat) => (
                <div className="diagnostic_card border-red-500 flex flex-row justify-between">
                  <div className="flex flex-col">
                    <h2>{stat.filename}</h2>
                    <p>
                      {stat.warning_count}{" "}
                      {stat.warning_count == 1 ? "warning" : "warnings"}
                    </p>
                  </div>
                  <div className="flex flex-col">
                    <Button
                      onClick={() =>
                        run_diagnostics(stat.id).then(loadFileStats)
                      }
                    >
                      Run Diagnostics
                    </Button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* DARKEN AREA IF SIDEBAR IS SHOWING */}
      {sidebarVisible && (
        <div
          onClick={() => setSidebarVisible(false)}
          className="z-10 fixed top-0 left-0 w-full h-full bg-black/50"
        />
      )}

      {/* SIDEBAR FOR DIAGNOSTIC INSIGHTS */}
      {sidebarVisible && (
        <Diagnostics
          filename={
            fileStats.filter((stat) => stat.id === selectedFileId)[0]
              ?.filename || null
          }
          selectedFileId={selectedFileId}
        />
      )}
    </div>
  );
}

export default Dashboard;
