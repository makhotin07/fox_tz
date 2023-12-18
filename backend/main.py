import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from src.api.v1 import auth, file, message, scheduler, ticket
from src.core.config import settings

# Создаем FastAPI приложение
app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse
)

# Включаем маршруты для различных модулей
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(ticket.router, prefix="/api/v1/ticket", tags=["ticket"])
app.include_router(message.router, prefix="/api/v1/message", tags=["message"])
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["scheduler"])
app.include_router(file.router, prefix="/api/v1/file", tags=["file"])

# Запускаем сервер приложения, если файл выполняется как скрипт
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
    )
