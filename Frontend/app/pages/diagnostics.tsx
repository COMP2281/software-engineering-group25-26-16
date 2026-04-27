import type { File } from "~/types";
import type { Warning } from "~/types";
import { Button } from "~/components/button";
import { useEffect, useRef, useState } from "react";
import { Chart } from "chart.js/auto";
import { Bar, Scatter } from "react-chartjs-2";
import { Trash } from "lucide-react";

type Sender = "Granite" | "You";

interface GraniteMessage {
  id: number;
  sender: Sender;
  message: string;
}

function DiagnosticInfo({ warning }: { warning: Warning }) {
  const [graniteInput, setGraniteInput] = useState("");
  const [graniteMessages, setGraniteMessages] = useState<GraniteMessage[]>([]);

  useEffect(() => setGraniteMessages([]), [warning]);

  let severityColour = "border-green-400";
  if (warning.severity === "low") {
    severityColour = "border-green-400";
  } else if (warning.severity === "medium") {
    severityColour = "border-orange-400";
  } else if (warning.severity === "high") {
    severityColour = "border-red-500";
  }

  const ask_granite = async () => {
    setGraniteInput("");

    setGraniteMessages((graniteMessages) => [
      ...graniteMessages,
      {
        id:
          graniteMessages.length > 0
            ? graniteMessages[graniteMessages.length - 1].id + 1
            : 1,
        sender: "You",
        message: graniteInput,
      },
      {
        id:
          graniteMessages.length > 0
            ? graniteMessages[graniteMessages.length - 1].id + 2
            : 2,
        sender: "Granite",
        message: "Waiting for Granite's response...",
      },
    ]);

    const response = await fetch(
      `/api/explain/${warning.id}?` +
        new URLSearchParams({
          query: graniteInput,
        }),
      {
        method: "GET",
      },
    );

    const stream_reader = response.body?.getReader();

    if (!stream_reader) {
      setGraniteMessages((prev) => {
        let new_arr = [...prev];
        new_arr[prev.length - 1].message = "Granite failed to respond.";
        return new_arr;
      });
      return;
    }

    const decoder = new TextDecoder("utf-8");
    let result = "";

    while (true) {
      const { value, done } = await stream_reader.read();
      if (done) break;

      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        result += chunk;
      }

      console.log("Current result:", result);
      setGraniteMessages((prev) => {
        let new_arr = [...prev];
        new_arr[prev.length - 1].message = result;
        return new_arr;
      });
    }

    // let response_json: GraniteResponse = await response.json();
    //
    // setGraniteMessages([
    //   ...graniteMessages,
    //   {
    //     sender: "You",
    //     message: graniteInput,
    //   },
    //   {
    //     sender: "Granite",
    //     message: response_json.explanation,
    //   },
    // ]);
  };

  return (
    <div className={`diagnostic_card ${severityColour}`}>
      <h3>Diagnostic Details</h3>
      <p>
        <strong>Type:</strong> {warning.type}
      </p>
      <p>
        <strong>Severity:</strong> {warning.severity}
      </p>
      <p>
        <strong>Run Time:</strong> {warning.run_time}s
      </p>
      <p>{warning.message}</p>

      <div className="flex flex-row m-2">
        <input
          type="text"
          value={graniteInput}
          onChange={(e) => setGraniteInput(e.target.value)}
          placeholder="Ask Granite about this..."
          className="flex-1"
          onKeyDown={(e) => e.key === "Enter" && ask_granite()}
          onSubmit={(e) => {
            e.preventDefault();
            ask_granite();
          }}
        />
        <Button onClick={ask_granite}>Ask Granite</Button>
      </div>

      <div className="flex flex-col gap-4">
        {graniteMessages.map((msg) => (
          <div
            key={msg.id}
            className={`rounded-lg w-8/12 p-4 shadow-lg ${
              msg.sender === "You" ? "self-end" : "self-start"
            }`}
          >
            <strong>{msg.sender}</strong>
            <p>{msg.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function WarningTypeFrequencyChart({ warnings }: { warnings: Warning[] }) {
  // get unique types of warnings and assign id to each one
  const types = Array.from(new Set(warnings.map((w) => w.type)));

  const data = {
    labels: types,
    datasets: [
      {
        label: "Warning Type Frequency",
        data: types.map(
          (type) => warnings.filter((w) => w.type === type).length,
        ),
        backgroundColor: "rgba(75, 192, 192, 0.5)",
      },
    ],
  };

  const options = {
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Diagnostic Type",
        },
      },
      y: {
        title: {
          display: true,
          text: "Frequency",
        },
        beginAtZero: true,
      },
    },
  };

  return <Bar data={data} options={options} />;
}

function DiagnosticsChart({
  warnings,
  setSelectedWarning,
}: {
  warnings: Warning[];
  setSelectedWarning: (w: Warning) => void;
}) {
  // get unique types of warnings and assign id to each one
  const types = Array.from(new Set(warnings.map((w) => w.type)));

  // x axis will be run_time, y axis will be type of warning, color will be severity
  const data = {
    datasets: warnings.map((w) => ({
      label: w.type,
      data: [{ x: w.run_time, y: types.indexOf(w.type) }],
      backgroundColor:
        w.severity === "high"
          ? "red"
          : w.severity === "medium"
            ? "orange"
            : "green",
      radius: 7,
    })),
  };

  const options = {
    parsing: false,
    animation: false,
    plugins: {
      decimation: {
        enabled: true,
        algorithm: "lttb", // or 'min-max'
        samples: 50, // number of visible points
      },
      zoom: {
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true,
          },
          mode: "x",
        },
      },
      legend: {
        display: false,
      },
    },
    onClick: (event: any, elements: any) => {
      if (elements.length == 0) return;
      setSelectedWarning(warnings[elements[0].datasetIndex]);
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Run Time (s)",
        },
      },
      y: {
        title: {
          display: true,
          text: "Diagnostic Type",
        },
        ticks: {
          display: false,
        },
        min: -3,
        max: types.length + 3,
      },
    },
  };

  let chart_ref = useRef(null);

  let reset_zoom = () => {
    if (chart_ref.current) {
      // @ts-ignore
      chart_ref.current.options.scales.x.min = undefined;
      // @ts-ignore
      chart_ref.current.options.scales.x.max = undefined;
      // @ts-ignore
      chart_ref.current.update();
    }
  };

  let full_scale = () => {
    if (chart_ref.current) {
      // make minimum x value 0 and maximum x value the maximum run_time
      // @ts-ignore
      chart_ref.current.options.scales.x.min = 0;
      // @ts-ignore
      chart_ref.current.options.scales.x.max =
        Math.max(...warnings.map((w) => w.run_time)) + 5;
      // @ts-ignore
      chart_ref.current.update();
    }
  };
  return (
    <>
      <Scatter ref={chart_ref} data={data} options={options} />

      <Button onClick={reset_zoom}>Reset Zoom</Button>
      <Button onClick={full_scale}>Show Full</Button>
    </>
  );
}

type GraphShown = "frequency" | "timeline";

function DiagnosticsChartArea({ warnings }: { warnings: Warning[] }) {
  const [selectedWarning, setSelectedWarning] = useState<Warning | null>(null);
  const [graphShown, setGraphShown] = useState<GraphShown>("timeline");

  return (
    <>
      <h3>Diagnostic Timeline</h3>

      <p>
        <i className="text-gray-500">
          {warnings.length} {warnings.length === 1 ? "warning" : "warnings"}
        </i>
      </p>
      {graphShown == "frequency" && (
        <Button onClick={() => setGraphShown("timeline")}>Show Timeline</Button>
      )}
      {graphShown == "timeline" && (
        <Button onClick={() => setGraphShown("frequency")}>
          By Warning Frequency
        </Button>
      )}
      {graphShown == "frequency" && (
        <WarningTypeFrequencyChart warnings={warnings} />
      )}
      {graphShown == "timeline" && (
        <DiagnosticsChart
          warnings={warnings}
          setSelectedWarning={setSelectedWarning}
        />
      )}
      {selectedWarning && <DiagnosticInfo warning={selectedWarning} />}
    </>
  );
}

export async function run_diagnostics(selectedFileId: number | null) {
  console.log("Running diagnostics for file ID:", selectedFileId);
  if (selectedFileId === null) return;
  try {
    const response = await fetch(`/api/diagnostics/${selectedFileId}`, {
      method: "GET",
      credentials: "include",
    });
    if (response.ok) {
      const data = await response.json();
      return data;
    }
  } catch (error) {
    console.error("Diagnostics failed:", error);
  }
  return [];
}

export default function Diagnostics({
  filename,
  selectedFileId,
}: {
  filename: string | null;
  selectedFileId: number | null;
}) {
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [diagnosticsRunning, setDiagnosticsRunning] = useState(false);

  // run diagnostics when file is selected
  useEffect(() => {
    setDiagnosticsRunning(true);
    run_diagnostics(selectedFileId)
      .then(setWarnings)
      .then(() => setDiagnosticsRunning(false));
  }, [selectedFileId]);

  return (
    <aside className="fixed top-0 right-0 h-full bg-background p-5 z-20 w-[60em] overflow-y-auto">
      <h2>Granite Insights</h2>
      <p style={{ color: "var(--light-text)", marginBottom: "30px" }}>
        Log File: {filename || "N/A"}
      </p>

      {!diagnosticsRunning && <DiagnosticsChartArea warnings={warnings} />}
      {diagnosticsRunning && <p>Diagnostics are running...</p>}

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
    </aside>
  );
}
