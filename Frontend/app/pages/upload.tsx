import React, { useEffect, useState } from "react";

import "../styles/pages.css";
import "../styles/dashboard.css";
import Diagnostics from "./diagnostics";
import type { File } from "~/types";
import { Button } from "~/components/button";
import { Trash } from "lucide-react";

export default function Upload() {
  const [files, setFiles] = useState<File[] | null>(null);
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);

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

  const onUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch("/api/uploads/upload", {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (response.ok) {
        // refresh page
        window.location.reload();
      }
    } catch (error) {
      console.error("Upload failed:", error);
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
        <h1>
          Upload <span className="text-primary">Files</span>
        </h1>
        <p style={{ color: "var(--secondary-text)", fontSize: "1.1rem" }}>
          Intelligent OBD-II Diagnostic Management System
        </p>
      </header>

      <h2>Upload Vehicle OBD-II Logs</h2>
      <br />

      <input
        type="file"
        name="fileupload"
        accept=".csv"
        onChange={onUpload}
        className="cursor-pointer rounded-sm border border-gray-300 px-4 py-2 transition-colors duration-200 hover:bg-gray-100"
      />

      <section style={{ marginTop: "50px" }}>
        <h2>Uploaded Vehicle Reports</h2>
        <div className="summary_grid" style={{ gap: "25px" }}>
          {files === null ? (
            <p>Loading garage database...</p>
          ) : files.length === 0 ? (
            <p>No reports available. Please upload a vehicle log.</p>
          ) : (
            files.map((file) => (
              <div
                key={file.id}
                className="summary_card cursor-pointer flex flex-col justify-between items-start p-6 border border-gray-200 transition-transform duration-200 hover:-translate-y-1 flex flex-row justify-between"
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
                <div className="flex flex-col items-start">
                  <div className="w-[40px] h-[4px] mb-4 bg-primary"></div>
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
              </div>
            ))
          )}
        </div>
      </section>

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
            files?.filter((file) => file.id === selectedFileId)[0]?.filename ||
            null
          }
          selectedFileId={selectedFileId}
        />
      )}
    </div>
  );
}
