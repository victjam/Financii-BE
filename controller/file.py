from fastapi import Depends, FastAPI, UploadFile, File
import csv
import io
import codecs

from fastapi import APIRouter
from controller.auth import get_current_user

from models.user import UserInDB

router = APIRouter(prefix="/file", tags=["File"])


@router.post("/upload-csv/")
async def handle_csv(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
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
        })

    return result
