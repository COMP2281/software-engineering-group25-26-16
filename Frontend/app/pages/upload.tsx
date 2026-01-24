import React, { useEffect } from 'react';
import '../styles/pages.css';
import { Button } from 'primereact/button';
import { FileUpload, type FileUploadBeforeUploadEvent, type FileUploadHandlerEvent, type FileUploadProps, type FileUploadUploadEvent } from 'primereact/fileupload';
import { ListBox } from 'primereact/listbox';
import { Toast } from 'primereact/toast';
import { Sidebar } from 'primereact/sidebar';
import type { Warning } from '~/types';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';

// to upload the files
function onUpload(event: FileUploadHandlerEvent) {
    if (event.files.length == 0) {
        return;
    }

    const file = event.files[0];

    // upload file to `/api/upload_file` via POST request
    const formData = new FormData();
    formData.append('file', file);

    // fetch from api.{DOMAIN}/upload_file
    if (typeof window === 'undefined') {
        return;
    }

    console.log('Uploading file to', `api.${window.location.host}/upload_file`);
    let domain = `${window.location.protocol}//api.${window.location.host}`;

    fetch(`${domain}/upload_file`, {
        method: 'POST',
        body: formData,
    }).then(response => {
        if (response.ok) {
            alert('File uploaded successfully.');
        } else {
            alert('File upload failed.');
        }
    }).catch(error => {
        alert('File upload failed.');
    });
}

// get uploadad files from api.{DOMAIN}/list_uploads
async function getUploadedFiles() {
    if (typeof window === 'undefined') {
        return;
    }
    
    let domain = `${window.location.protocol}//api.${window.location.host}`;
    let response = await fetch(`${domain}/list_uploads`, {
        method: 'GET',
    })

    if (response.ok) {
        let data = await response.json();
        return data.files;
    } else {
        alert('Failed to fetch uploaded files.');
        return [];
    }
}

export default function Upload() {
    let [files, setFiles] = React.useState<string[] | null>(null);
    let [sidebar_visible, setSidebarVisible] = React.useState(false);
    let [sidebar_file, setSidebarFile] = React.useState<string | null>(null);
    let [warnings, setWarnings] = React.useState<Warning[]>([]);

    useEffect(() => {
        async function get_files() {
            let files = await getUploadedFiles();
            setFiles(files);
        }

        get_files();
    }, []);


    async function runDiagnostics(file: string) {
        // run diagnostics by calling "/fuel_capacity_scan/{filename}"
        if (typeof window === 'undefined') {
            return;
        }

        let domain = `${window.location.protocol}//api.${window.location.host}`;
        let response = await fetch(`${domain}/fuel_capacity_scan/${file}`, {
            method: 'GET',
        });

        if (!response.ok) {
            alert('Failed to run diagnostics.');
            return;
        }

        // data.warnings is a list of FuelTankWarnings
        let data = await response.json();
        setWarnings(data.warnings);
    }

    function DiagnosticSidebar() {
        if (sidebar_file === null) {
            return null;
        }

        // warning table with two columns: one for run_time, other for message
        let warnings_table = (<DataTable value={warnings} tableStyle={{ minWidth: '50rem' }}>
            <Column field="run_time" header="Run Time"></Column>
            <Column field="message" header="Message"></Column>
        </DataTable>);

        return (
            <Sidebar visible position="right" style={{ width: '50%' }} onHide={() => {setSidebarVisible(false)}}>
                <h2>Diagnostics</h2>
                <p>Running diagnostics for file: {sidebar_file}</p>
                <Button label="Run Diagnostics" onClick={() => {runDiagnostics(sidebar_file)}} />

                <h3>Warnings</h3>
                {warnings.length === 0 ? <p>No warnings.</p> : warnings_table}

            </Sidebar>
        );
    }


    let displayed_list;
    if (files === null) {
        displayed_list = <p>Loading...</p>;
    } else if (files.length === 0) {
        displayed_list = <p>No files uploaded yet.</p>;
    } else {
        displayed_list = files.map(file => (
            <>
                <Button link key={file} label={file} className="file_button" onClick={() => {
                    setSidebarVisible(true);
                    setSidebarFile(file);
                    setWarnings([]);
                }} />
                <br />
            </>
        ));
    }

    let sidebar;
    if (sidebar_visible) {
        sidebar = <DiagnosticSidebar />;
    } else {
        sidebar = null;
    }

    return (
        <div className="page_container">
            <h1>Upload</h1>
            <FileUpload mode="basic" name="demo[]" uploadHandler={onUpload} accept="text/csv" maxFileSize={1000000} customUpload />
            
            <h2>Uploaded Files</h2>
            <p>Click on a file to perform diagnostics on it.</p>
            
            {displayed_list}
            {sidebar}
        </div>  
    );
}
