import React, { useEffect, useState } from "react";
import type { FileUploadHandlerEvent } from "primereact/fileupload";
import { FileUpload } from "primereact/fileupload";
import { Button } from "primereact/button";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Sidebar } from "primereact/sidebar";

import "../styles/pages.css";
import "../styles/dashboard.css";

interface Warning {
  run_time: string;
  severity: string;
  type: string;
  message: string;
}

interface File {
  user_id: number;
  filename: string;
  id: number;
}

export default function Upload() {
  const [files, setFiles] = useState<File[] | null>(null);
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [warnings, setWarnings] = useState<Warning[]>([]);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await fetch(`/api/uploads/list`, {
        method: "GET",
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files);
      }
    } catch (error) {
      console.error("Error retrieving logs:", error);
    }
  };

  const onUpload = async (event: FileUploadHandlerEvent) => {
    const file = event.files[0];
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch(`/api/uploads/upload`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (response.ok) fetchFiles();
    } catch (error) {
      console.error("Upload failed:", error);
    }
  };

  const run_diagnostics = async () => {
    if (!selectedFileId) return;
    try {
      const response = await fetch(`/api/diagnostics/${selectedFileId}`, {
        method: "GET",
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setWarnings(data);
      }
    } catch (error) {
      console.error("Diagnostics failed:", error);
    }
  };

  return (
    <div
      className="page_container"
      style={{ background: "var(--bg-main)", minHeight: "100vh" }}
    >
      <header
        style={{
          marginBottom: "40px",
          borderBottom: "1px solid #e0e0e0",
          paddingBottom: "20px",
        }}
      >
        <h1
          style={{
            fontSize: "2.5rem",
            fontWeight: "800",
            color: "var(--text-primary)",
            letterSpacing: "-1px",
          }}
        >
          Granite{" "}
          <span style={{ color: "var(--primary-color)" }}>Guardian</span>
        </h1>
        <p style={{ color: "var(--secondary-text)", fontSize: "1.1rem" }}>
          Intelligent OBD-II Diagnostic Management System
        </p>
      </header>

      <div
        className="alert_card"
        style={{
          borderLeft: "5px solid var(--primary-color)",
          padding: "40px",
          background: "var(--bg-white)",
          boxShadow: "var(--shadow-md)",
        }}
      >
        <h3 style={{ marginBottom: "20px", fontWeight: "600" }}>
          Import New Vehicle Log
        </h3>
        <FileUpload
          mode="advanced"
          customUpload
          uploadHandler={onUpload}
          accept="text/csv"
          maxFileSize={1000000}
          chooseLabel="Browse"
          uploadLabel="Analyze"
          cancelLabel="Clear"
          emptyTemplate={
            <div style={{ textAlign: "center", padding: "20px" }}>
              <p style={{ color: "var(--light-text)" }}>
                Drag and drop .csv log files here for Granite-powered
                diagnostics.
              </p>
            </div>
          }
        />
      </div>

      <section style={{ marginTop: "50px" }}>
        <h2
          style={{
            marginBottom: "25px",
            fontSize: "1.5rem",
            fontWeight: "700",
          }}
        >
          Recent Vehicle Reports
        </h2>
        <div className="summary_grid" style={{ gap: "25px" }}>
          {files === null ? (
            <p>Loading garage database...</p>
          ) : files.length === 0 ? (
            <p>No reports available. Please upload a vehicle log.</p>
          ) : (
            files.map((file) => (
              <div
                key={file.id}
                className="summary_card"
                style={{
                  transition: "transform 0.2s ease",
                  border: "1px solid #eee",
                  textAlign: "left",
                  padding: "25px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.transform = "translateY(-5px)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.transform = "translateY(0)")
                }
                onClick={() => {
                  setSelectedFileId(file.id);
                  setSidebarVisible(true);
                }}
              >
                <div>
                  <div
                    style={{
                      width: "40px",
                      height: "4px",
                      background: "var(--primary-color)",
                      marginBottom: "15px",
                    }}
                  ></div>
                  <h4
                    style={{
                      margin: "0",
                      fontSize: "1.2rem",
                      fontWeight: "600",
                      color: "var(--text-primary)",
                    }}
                  >
                    {file.filename}
                  </h4>
                  <span
                    className="badge_component"
                    style={{ marginTop: "10px", display: "inline-block" }}
                  >
                    OBD-II Data Log
                  </span>
                </div>
                <Button
                  label="View Insights"
                  className="p-button-text p-button-sm"
                  style={{
                    padding: "0",
                    marginTop: "20px",
                    color: "var(--primary-color)",
                    fontWeight: "bold",
                  }}
                />
              </div>
            ))
          )}
        </div>
      </section>

      <Sidebar
        visible={sidebarVisible}
        onHide={() => setSidebarVisible(false)}
        position="right"
        style={{ width: "500px", padding: "2rem" }}
      >
        <h2 style={{ fontWeight: "800", marginBottom: "10px" }}>
          Granite Insights
        </h2>
        <p style={{ color: "var(--light-text)", marginBottom: "30px" }}>
          Log File: {selectedFileId}
        </p>

        <Button onClick={run_diagnostics}>Run Diagnostics</Button>

        <DataTable value={warnings} className="p-datatable-sm" stripedRows>
          <Column
            field="run_time"
            header="TIMESTAMP"
            style={{ color: "var(--light-text)", fontSize: "0.8rem" }}
          />
          <Column field="message" header="DIAGNOSTIC SUMMARY" />
        </DataTable>

        <div
          className="recommendation_box"
          style={{
            marginTop: "30px",
            borderLeft: "3px solid var(--primary-color)",
            background: "#f0f4ff",
          }}
        >
          <strong>System Note:</strong>
          <p>
            These diagnostics are AI-generated for guidance and do not replace
            professional mechanical inspection.
          </p>
        </div>
      </Sidebar>
    </div>
  );
}
