import os
from fastapi import FastAPI, UploadFile, HTTPException
import helpers
from warning import FuelTankWarning
from typing import Sequence
import json

UPLOAD_FOLDER = "./uploaded_data/"

app = FastAPI()

@app.get("/get_data/{filename}")
async def root(filename: str, num_rows: int | None = None, fields: str | None = None):
    full_dict = {}
    if fields == None:
        full_dict = helpers.get_csv_as_dict(f"{UPLOAD_FOLDER}/{filename}")
    else:
        full_dict = helpers.get_csv_as_dict(f"{UPLOAD_FOLDER}/{filename}", fields.split(","))

    if num_rows == None or num_rows < 1:
        return full_dict
    else:
        return helpers.sample_dict(full_dict, num_rows)

# get list of uploaded files
@app.get("/list_uploads/")
async def list_uploads():
    files = os.listdir(f"./{UPLOAD_FOLDER}/")
    return {"files": files}

# endpoint to delete an uploaded file
@app.delete("/delete_upload/{filename}")
async def delete_upload(filename: str):
    path = f"{UPLOAD_FOLDER}/{filename}"
    if os.path.exists(path):
        os.remove(path)
        return f"File {filename} deleted successfully."
    else:
        raise HTTPException(status_code=404, detail="File not found.")

# upload a file and store it in ./uploaded_data/
@app.post("/upload_file/")
async def upload_file(file: UploadFile):
    # check content type
    if file.content_type != "text/csv":
        raise HTTPException(status_code=415, detail="Only CSV files are allowed.")

    # check if file exists, and return error if it does
    if os.path.exists(f"{UPLOAD_FOLDER}/{file.filename}"):
        raise HTTPException(status_code=409, detail="File already exists.")

    file_location = f"{UPLOAD_FOLDER}/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    return f"File {file.filename} saved successfully"

# test: scan a csv file and find which rows have a fuel capacity lower than 20
@app.get("/fuel_capacity_scan/{filename}")
async def fuel_capacity_scan(filename: str):
    full_dict = helpers.get_csv_as_dict(f"{UPLOAD_FOLDER}/{filename}")
    if full_dict is None:
        raise HTTPException(status_code=404, detail="File not found or could not be read.")

    warnings: list[FuelTankWarning] = []
    for _, value in full_dict.items():
        try:
            if float(value["FUEL TANK"]) < 20:
                warning = FuelTankWarning(run_time=value["ENGINE RUN TIME"], capacity=float(value["FUEL TANK"]))
                warnings.append(warning)
        except:
            continue
    
    helpers.log_warnings(warnings)
    return {
        "warnings": list(map(lambda w : w.to_dict(), warnings))
    }

# get list of logged warnings
@app.get("/get_warning_log")
async def get_logged_warnings():
    if not os.path.exists(helpers.LOG_LOCATION):
        return {"warnings": []}

    with open(helpers.LOG_LOCATION, "r") as log_file:
        logs = log_file.readlines()
    
    return {"warnings": [json.loads(log.strip()) for log in logs]}

# clear log
@app.delete("/clear_warning_log")
async def clear_warning_log():
    if os.path.exists(helpers.LOG_LOCATION):
        os.remove(helpers.LOG_LOCATION)
        return "Log file cleared."
    else:
        raise HTTPException(status_code=404, detail="Log file not found.")
