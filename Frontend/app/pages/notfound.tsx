import React from 'react';
import '../styles/pages.css';

// errors handling 
function NotFound() {
  return (
    <div className="notfound_container">
      <div className="notfound_content">
        <h1 className="notfound_title"> Error 404</h1>
        <h2 className="notfound_subtitle">Page not found</h2>
        <p className="notfound_text">
          The page does not exist
        </p>
        <a href="/" className="notfound_button">
          Well go back to dashboard
        </a>
      </div>
    </div>
  );
}
export default NotFound;