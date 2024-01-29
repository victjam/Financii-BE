from fastapi import FastAPI, UploadFile, File
import csv
import io
import codecs

from fastapi import APIRouter

router = APIRouter(prefix="/file", tags=["File"])


@router.post("/upload-csv/")
async def handle_csv(file: UploadFile = File(...)):
    content = await file.read()
    content_io = io.StringIO(codecs.decode(content, 'utf-8-sig'))
    reader = csv.DictReader(content_io)
    result = []

    for row in reader:
        result.append({
            "Description": row.get("Description", ""),
            "Date": row.get("Date", ""),
            "Amount": row.get("Amount", ""),
            "Currency": row.get("Currency", ""),
            "Status": row.get("Status", "")
        })

    return result
