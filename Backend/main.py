import os
from fastapi import FastAPI, UploadFile, HTTPException
import helpers
from warning import FuelTankWarning
from typing import Sequence
import json

app = FastAPI()

@app.get("/get_data/{filename}")
async def root(filename: str, num_rows: int | None = None, fields: str | None = None):
    full_dict = {}
    if fields == None:
        full_dict = helpers.get_csv_as_dict(f"{filename}")
    else:
        full_dict = helpers.get_csv_as_dict(f"{filename}", fields.split(","))

    if num_rows == None or num_rows < 1:
        return full_dict
    else:
        return helpers.sample_dict(full_dict, num_rows)

# get list of uploaded files
@app.get("/list_uploads/")
async def list_uploads():
    files = helpers.get_csv_list()
    return {"files": files}

# endpoint to delete an uploaded file
@app.delete("/delete_upload/{filename}")
async def delete_upload(filename: str):
    path = helpers.get_csv_path(filename)
    if os.path.exists(path):
        os.remove(path)
    else:
        raise HTTPException(status_code=404, detail="File not found.")

    log_path = f""
    if os.path.exists(log_path):
        os.remove(log_path)

    return f"File {filename} deleted successfully."

# upload a file and store it in ./uploaded_data/
@app.post("/upload_file/")
async def upload_file(file: UploadFile):
    # check content type
    if file.content_type != "text/csv":
        raise HTTPException(status_code=415, detail="Only CSV files are allowed.")

    if file.filename == None:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    path = helpers.get_csv_path(file.filename)

    # check if file exists, and return error if it does
    if os.path.exists(path):
        raise HTTPException(status_code=409, detail="File already exists.")

    with open(path, "wb+") as file_object:
        file_object.write(file.file.read())

    diagnostics = helpers.get_diagnostics_for_csv(file.filename)
    if diagnostics is not None:
        return diagnostics
    else:
        raise HTTPException(status_code=500, detail="File uploaded but diagnostics could not be run.")

# test: scan a csv file and find which rows have a fuel capacity lower than 20
@app.get("/fuel_capacity_scan/{filename}")
async def run_diagnostics(filename: str):
    diagnostics = helpers.get_diagnostics_for_csv(filename)
    if diagnostics is not None:
        return diagnostics
    else:
        raise HTTPException(status_code=404, detail="File not found or could not be read.")

# get list of logged warnings
@app.get("/get_warning_log/")
async def get_logged_warnings():
    # for all files in UPLOAD_FOLDER, get the corresponding logs
    logs = {}
    for filename in helpers.get_csv_list():
        log_json = helpers.get_log_json(filename)
        if log_json is not None:
            logs[filename] = log_json
    return logs


# get list of logged warnings for specific file
@app.get("/get_warning_log/{filename}")
async def get_logged_warnings_for_file(filename: str):
    # for all files in UPLOAD_FOLDER, get the corresponding logs
    log_json = helpers.get_diagnostics_for_csv(filename)
    return log_json



# clear log
# @app.delete("/clear_warning_log")
# async def clear_warning_log():
#     if os.path.exists(helpers.LOG_LOCATION):
#         os.remove(helpers.LOG_LOCATION)
#         return "Log file cleared."
#     else:
#         raise HTTPException(status_code=404, detail="Log file not found.")
