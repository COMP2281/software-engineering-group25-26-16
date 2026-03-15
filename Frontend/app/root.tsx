import React, { useEffect } from "react";
import { Links, Meta, Outlet, Scripts, ScrollRestoration } from "react-router";
import "./styles/global.css";
import "./styles/index.css";
import "./styles/dashboard.css";
import "./styles/chatbot.css";
import { Chart } from "chart.js";

export default function App() {
  useEffect(() => {
    if (typeof window !== "undefined")
      import("chartjs-plugin-zoom").then((plugin) => {
        Chart.register(plugin.default);
      });
  }, []);

  return <AppInner />;
}

function AppInner() {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <Outlet />
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}
