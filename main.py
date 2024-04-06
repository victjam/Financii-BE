from typing import Union
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Your routers
from controller.user import router as user_router
from controller.auth import router as auth_router
from controller.account import router as account_router
from controller.file import router as file_router
from controller.transaction import router as transaction_router
from controller.category import router as category_router

app = FastAPI()

# Define a list of origins that are allowed to make requests to this API
origins = [
    "http://localhost:4000",  # Add other origins as needed
    "http://127.0.0.1:4000",   # Example if your frontend runs here too
]

# Add CORS middleware to allow requests from the frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": exc.status_code},
    )

# Include your routers
app.include_router(user_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(file_router, prefix="/api")
app.include_router(transaction_router, prefix="/api")
app.include_router(category_router, prefix="/api")
app.include_router(account_router, prefix="/api")
