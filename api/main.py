from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.config import frontend_origins
from api.routers.analytics import router as analytics_router
from api.routers.profiles import router as profiles_router
from api.routers.workouts import router as workouts_router


class HealthResponse(BaseModel):
    status: str
    service: str


app = FastAPI(
    title="HYROX Coach API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles_router)
app.include_router(workouts_router)
app.include_router(analytics_router)


def error_response(code: str, message: str, request_id: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exception: HTTPException) -> JSONResponse:
    code = "UNAUTHORIZED" if exception.status_code == 401 else "REQUEST_FAILED"
    return JSONResponse(
        status_code=exception.status_code,
        content=error_response(code, str(exception.detail), request.state.request_id),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_response(
            "VALIDATION_ERROR",
            "The request contains invalid values.",
            request.state.request_id,
        ),
    )


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="hyrox-coach-api")
