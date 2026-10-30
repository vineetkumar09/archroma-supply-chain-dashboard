from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pandas as pd
import io

app = FastAPI()

# 1. Serve your exact HTML file when you open http://localhost:8000
@app.get("/")
async def read_index():
    return FileResponse("index.html")

# 2. API endpoint to provide the initial/sample data to your frontend JavaScript
@app.get("/api/data")
async def get_data():
    # You can load your default sample dataset or a default Excel file here using Pandas
    # For now, it returns your base records as JSON to the frontend
    df = pd.DataFrame([...]) # Your default dataset rows
    return df.to_dict(orient="records")

# 3. API endpoint if you upload a new Excel file through your frontend button
@app.post("/api/upload")
async def upload_excel(file: UploadFile = File(...)):
    contents = await file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        df = pd.read_excel(io.BytesIO(contents))
    
    # Clean and convert to records for JavaScript
    return df.to_dict(orient="records")