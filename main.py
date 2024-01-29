from typing import Union

from fastapi import FastAPI

from controller.user_controller import router as user_router
from controller.auth import router as auth_router
from controller.file import router as file_router

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": exc.status_code},
    )


app.include_router(user_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(file_router, prefix="/api")
