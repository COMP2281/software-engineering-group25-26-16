import React, { useEffect, useMemo, useState } from "react";
import "../styles/pages.css";
import "../styles/dashboard.css";
import type { FileStats } from "~/types";
import { Button } from "~/components/button";
import Diagnostics, { run_diagnostics } from "./diagnostics";
import { Bar } from "react-chartjs-2";
import { CategoryScale } from "chart.js";

function Bars({
  fileStats,
  setSelectedFileId,
  setSelectedFilename,
}: {
  fileStats: FileStats[];
  setSelectedFileId: (id: number) => void;
  setSelectedFilename: (filename: string) => void;
}) {
  let labels = fileStats.map((stat) => stat.filename);

  // show bar graph with chart.js
  const options = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
        position: "top" as const,
      },
      title: {
        display: true,
        text: "Number of Warnings",
      },
    },
    onClick: (_event: any, elements: any) => {
      if (elements.length == 0) return;
      setSelectedFileId(fileStats[elements[0].index].id);
      setSelectedFilename(fileStats[elements[0].index].filename);
    },
  };

  const data = useMemo(() => {
    const diagnosticsRan = fileStats.filter((stat) => stat.diagnostics_ran);
    return {
      labels,
      datasets: [
        {
          label: "Diagnostics Ran",
          data: diagnosticsRan.map((stat) => stat.warning_count),
        },
      ],
    };
  }, [fileStats]);

  return (
    <div className="bar_chart_container">
      <h2>Number of Warnings by File</h2>
      <Bar options={options} data={data} />
    </div>
  );
}

function Dashboard() {
  const [fileStats, setFileStats] = useState<FileStats[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [selectedFilename, setSelectedFilename] = useState<string | null>(null);

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
      </header>

      <Bars
        fileStats={fileStatsDiagnosticsRanSorted}
        setSelectedFileId={setSelectedFileId}
        setSelectedFilename={setSelectedFilename}
      />

      {fileStatsDiagnosticsNotRan.length > 0 && (
        <div className="alerts_section">
          <div className="flex gap-2 flex-col flex-1">
            <h2>Files Where Diagnostics Have Not Been Run</h2>

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
      )}

      {/* DARKEN AREA IF SIDEBAR IS SHOWING */}
      {selectedFileId && selectedFilename && (
        <div
          onClick={() => {
            setSelectedFileId(null);
            setSelectedFilename(null);
          }}
          className="z-10 fixed top-0 left-0 w-full h-full bg-black/50"
        />
      )}

      {/* SIDEBAR FOR DIAGNOSTIC INSIGHTS */}
      {selectedFileId && selectedFilename && (
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
