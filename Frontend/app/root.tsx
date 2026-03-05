import React from 'react';
import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from 'react-router';
import { PrimeReactProvider, PrimeReactContext } from 'primereact/api';
import './styles/global.css';
import './styles/index.css';
import './styles/dashboard.css';
import './styles/chatbot.css';
import "primereact/resources/themes/lara-light-cyan/theme.css";
import { Button } from 'primereact/button';

export default function App() {
    return (
        <PrimeReactProvider>
            <AppInner />
        </PrimeReactProvider>
    );
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
