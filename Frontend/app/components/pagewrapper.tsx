import React from 'react';
interface Page {
  title: string;
  content: React.ReactNode;
}

function PageWrapper({ title, content }: Page) {
  return (
    <div className="page_container">
      {/* header*/}
      <header className="page_header">
        <h1 className="page_title">{title}</h1>
      </header>
      
      {}
      <div className="page_body">
        {content}
      </div>
    </div>
  );
}

export default PageWrapper;