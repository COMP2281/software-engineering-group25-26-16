import React from 'react';
import '../styles/pages.css';
import pagewrapper from '../components/Pagewrapper';

// function for the dashboard (ill complete it later)
function Dashboard() {
  return (
    <pagewrapper 
    title="Dashboard">
      <h1>Dashboard</h1>
      <p>dashboard content here!!</p>
    </pagewrapper>
  );
}
export default Dashboard;


// in order to access the api from the fontend, jdois faire une request from api.localhost:8000/get_warning_log/ for example, and then use the data in the frontend to display it. I can also do a request to get the list of uploaded files, and then for each file, do a request to get the diagnostics for that file, and then display it in the frontend.
