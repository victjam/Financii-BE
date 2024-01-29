from fastapi import Depends, FastAPI, UploadFile, File, APIRouter
from controller.auth import get_current_user
from models.user import UserInDB
from db.client import db_client
import csv
import io
import codecs
import datetime

router = APIRouter(prefix="/file", tags=["File"])


def parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%d %b, %Y')


@router.post("/upload-csv/")
async def handle_csv(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    content = await file.read()
    content_io = io.StringIO(codecs.decode(content, 'utf-8-sig'))
    reader = csv.DictReader(content_io)
    transactions = []

    for row in reader:
        date_str = row.get("Date", "")
        try:
            parsed_date = parse_date(date_str)
            formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            formatted_date = None

        transactions.append({
            "title": row.get("Description", ""),
            "user_id": current_user.id,
            "amount": row.get("Amount", ""),
            "date": formatted_date,
            "description": row.get("Description", ""),
        })
    if transactions:
        result = db_client.transactions.insert_many(transactions)
        for i, inserted_id in enumerate(result.inserted_ids):
            transactions[i]['_id'] = str(inserted_id)
    return transactions
