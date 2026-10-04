from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from routers import user
from utils.response import Result

app = FastAPI(title="demo", description="this is a demo api", version="1.0.0")

# 注册路由
app.include_router(user.router)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:xxxx"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=Result.error(msg=str(exc.detail), code=exc.status_code).model_dump(),
    )


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=Result.error(msg="服务器内部错误").model_dump(),
    )
