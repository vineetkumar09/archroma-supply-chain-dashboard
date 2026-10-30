from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd
import io
import os

app = FastAPI()

# Sample data fallback matching your procurement metrics
SAMPLE_DATA = [
    {
        'Mat+Plant': '286009308125811', 'Material': '28600930812', 'Material Name': 'Ultraphor PWC R pdr 0020',
        'Plant': '5811', 'Plant Region': 'North America', 'Sub Category': 'Process & OBA Chemicals',
        'Catergory Manager': 'Ben Mo', 'Dyes/Chem': 'Chemicals', 'Initiative Type': 'New/alternative source/vendor',
        'Ytd Sep26 12mths PO Qty (Kgs)': 460000, 'Ytd Sep26 12mths PO Spends (USD)': 8199069, 'Total Projected Saving': 1380000.0, 'Stage Gate': '4-Go Live'
    },
    {
        'Mat+Plant': '2417472104', 'Material': '241747', 'Material Name': 'Perfluorhexylethylmethacrylat',
        'Plant': '2104', 'Plant Region': 'EMEA', 'Sub Category': 'Fluoro Chemicals',
        'Catergory Manager': 'Charles Allotey', 'Dyes/Chem': 'Chemicals', 'Initiative Type': 'Respecification',
        'Ytd Sep26 12mths PO Qty (Kgs)': 203600, 'Ytd Sep26 12mths PO Spends (USD)': 9425250, 'Total Projected Saving': 606728.02, 'Stage Gate': '4-Go Live'
    }
]

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>index.html not found in repository root!</h1>"

@app.get("/api/data")
async def get_data():
    return SAMPLE_DATA

@app.post("/api/upload")
async def upload_excel(file: UploadFile = File(...)):
    contents = await file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        df = pd.read_excel(io.BytesIO(contents))
    df.columns = [str(c).strip() for c in df.columns]
    return df.to_dict(orient="records")