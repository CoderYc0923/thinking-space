# FastAPI 完整版实战教程（适配 SpringBoot/JS 开发者）

## 前言：写给会 SpringBoot + JS 的开发者

你有 Java SpringBoot、JS 基础，学 FastAPI 会**极速上手**，核心对应关系先记牢：

- **FastAPI ≈ SpringBoot Web**：专门写接口、微服务，替代 Flask/Django 接口开发
- **Python 类型注解 ≈ Java 实体类定义**
- **Pydantic ≈ Spring Validation + DTO**：参数校验、数据序列化
- **FastAPI 自动文档 ≈ SpringDoc/Swagger**：开箱即用，无需配置
- **async/await ≈ Spring WebFlux / 异步 IO**：高并发场景用异步 IO，不是简单等价于线程池

FastAPI 相比 SpringBoot：**更少代码、零配置、启动更快、开发效率更高**，是目前 Python 后端、AI 接口、微服务的主流框架。

当前主流组合是 **FastAPI + Pydantic v2**。下文按 v2 写法讲解；老教程里的 `.dict()`、`orm_mode = True` 已过时。

## 一、环境准备（5分钟搞定）

### 1.1 基础环境要求

必须安装 **Python 3.10+**（推荐 3.11/3.12）。

原因：教程全程使用 `int | None` 这种联合类型写法，这是 **3.10 才有的语法**。Python 3.8/3.9 会直接语法报错。

验证命令（终端执行）：

```bash
python --version
# 或
python3 --version
```

### 1.2 安装核心依赖

对比 SpringBoot：SpringBoot 靠 starter 依赖，Python 靠 pip 安装包。

官方推荐一次装齐（含 uvicorn 等常用组件）：

```bash
pip install "fastapi[standard]"
```

如果只想最小安装：

```bash
pip install fastapi uvicorn python-multipart
```

- **fastapi**：核心框架（已依赖 pydantic，一般不用再单独装）
- **uvicorn**：ASGI 服务器（对应 SpringBoot 内嵌 Tomcat）
- **pydantic**：数据校验、模型映射（随 FastAPI 安装，当前是 v2）
- **python-multipart**：表单、文件上传需要

### 1.3 项目结构（对标 SpringBoot）

极简标准结构（企业通用）：

```text
fastapi-demo/
├── main.py          # 入口文件（对标 SpringBoot 启动类）
├── routers/         # 接口路由（对标 Controller 分层）
│   └── user.py
├── models/          # 数据模型（对标 DTO/Entity）
│   └── user.py
├── services/        # 业务逻辑（对标 Service）
│   └── user_service.py
└── utils/           # 工具类
    └── response.py
```

Python 3.3+ 可以把目录当命名空间包导入。为了兼容性，也可以在 `routers/`、`models/`、`services/`、`utils/` 下各放一个空的 `__init__.py`。

## 二、第一个 HelloWorld 项目（对标 SpringBoot 入门接口）

### 2.1 编写启动入口 main.py

新建 `main.py`，代码极简，无需配置类、无需注解扫描：

```python
from fastapi import FastAPI

# 初始化应用（对标 SpringBoot 启动容器）
app = FastAPI(
    title="FastAPI入门项目",
    description="适配SpringBoot开发者的实战教程",
    version="1.0.0",
)

# 根路径接口（对标 @GetMapping("/")）
@app.get("/")
def index():
    return {"msg": "Hello FastAPI！对标SpringBoot", "code": 200}

# 自定义接口
@app.get("/hello/{name}")
def hello(name: str):
    return {"name": name, "msg": "请求成功"}
```

### 2.2 启动项目

在项目根目录执行（对标 SpringBoot 启动 Run）：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

参数解释：

- `main`：对应 `main.py` 文件名（不要写 `.py`）
- `app`：文件内的 FastAPI 实例对象
- `--reload`：热更新（开发必备，改代码不用重启服务）
- `--port 8000`：端口（默认 8000，可自定义）

### 2.3 访问项目 & 自动文档（核心亮点）

启动成功后，浏览器访问：

- 接口地址：`http://127.0.0.1:8000`
- **自动交互式文档（重点）**：`http://127.0.0.1:8000/docs`（Swagger 风格）
- 备用文档：`http://127.0.0.1:8000/redoc`

对比 SpringBoot：无需引入依赖、无需配置，**零成本自带接口文档**，可直接在线调试接口。

## 三、核心接口开发（对标 SpringBoot Controller）

完全对标 SpringBoot 请求方式：GET、POST、路径参数、查询参数、请求体。

### 3.1 路径参数（@PathVariable）

SpringBoot 写法：`@GetMapping("/user/{id}")`

FastAPI 写法（自带类型校验）：

```python
@app.get("/user/{user_id}")
def get_user(user_id: int):
    return {"userId": user_id, "username": "张三"}
```

路径里传非数字（例如 `/user/abc`）会自动返回 422，不用自己写类型判断。

### 3.2 查询参数（@RequestParam）

SpringBoot 写法：`@RequestParam String name, Integer age`

```python
@app.get("/search")
def search_user(name: str, age: int | None = None):
    """
    name: 必填参数
    age: 可选参数，默认 None
    """
    return {"searchName": name, "age": age, "msg": "查询成功"}
```

请求地址：`/search?name=李四&age=20`

规则很简单：**没有默认值 = 必填，有默认值 = 可选**。

### 3.3 POST 请求 + JSON 请求体（@RequestBody）

这是后端最常用场景，对标 SpringBoot **DTO 接收 JSON**，FastAPI 用 Pydantic 模型实现。

```python
from pydantic import BaseModel

class UserDTO(BaseModel):
    username: str
    password: str
    age: int | None = None
    email: str | None = None

@app.post("/user/add")
def add_user(user: UserDTO):
    # 自动解析 JSON、自动参数校验、自动忽略未声明字段
    return {
        "code": 200,
        "msg": "用户新增成功",
        "data": user.model_dump(),  # Pydantic v2；v1 才是 user.dict()
    }
```

核心优势：**不用手动判空、不用类型转换**，参数错误自动返回 422 和字段级提示。

也可以直接 `return {"data": user}`，FastAPI 会自己把模型序列化成 JSON。

### 3.4 表单提交、文件上传

```python
from fastapi import Form, UploadFile, File

@app.post("/login")
def login(username: str = Form(), password: str = Form()):
    return {"username": username, "success": True}

@app.post("/upload")
def upload_file(file: UploadFile = File()):
    return {"filename": file.filename, "msg": "上传成功"}
```

表单和文件上传需要安装 `python-multipart`（`fastapi[standard]` 已包含）。

## 四、分层开发（对标 SpringBoot 三层架构）

入门写完后，正式项目必须分层，杜绝所有代码写在 `main.py` 中，完全对标 **Controller + Service + DTO**。

### 4.1 第一步：拆分模型 models

新建 `models/user.py`（存放 DTO、VO）：

```python
from pydantic import BaseModel, ConfigDict, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=20, description="用户名2-20位")
    password: str = Field(min_length=6, description="密码至少6位")
    age: int | None = Field(default=None, ge=0, le=150, description="年龄0-150")

class UserVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2；v1 才是 orm_mode = True

    id: int
    username: str
    age: int | None
```

`from_attributes=True` 的作用：以后从 SQLAlchemy ORM 对象直接生成 VO，而不必先手动转 dict。

### 4.2 第二步：拆分业务 service

新建 `services/user_service.py`：

```python
from models.user import UserCreate, UserVO

class UserService:
    @staticmethod
    def create_user(user: UserCreate) -> UserVO:
        # 此处可写：数据库新增、密码加密、日志记录等
        return UserVO(id=2001, username=user.username, age=user.age)

user_service = UserService()
```

建议 Service **返回 VO 对象**，不要返回松散 dict，类型更清楚，也方便 Controller 包装统一响应。

### 4.3 第三步：拆分路由 routers（Controller）

新建 `routers/user.py`：

```python
from fastapi import APIRouter

from models.user import UserCreate, UserVO
from services.user_service import user_service
from utils.response import Result

router = APIRouter(prefix="/user", tags=["用户管理"])

@router.post("/add")
def create_user(user: UserCreate):
    user_vo = user_service.create_user(user)
    return Result.success(data=user_vo)

@router.get("/{user_id}")
def get_user_info(user_id: int):
    user_vo = UserVO(id=user_id, username="测试用户", age=20)
    return Result.success(data=user_vo)
```

注意：**不要同时写 `response_model=UserVO` 又返回 `Result.success(...)`**。

`response_model` 会按声明的模型裁剪/校验响应。你实际返回的是 `{code, msg, data}`，声明成 `UserVO` 会校验失败或把统一响应结构弄丢。用了统一返回体，就不要再把 `response_model` 设成 VO。

### 4.4 第四步：整合路由到主入口

修改 `main.py`，统一注册路由（对标 SpringBoot 扫描 Controller）：

```python
from fastapi import FastAPI
from routers import user

app = FastAPI(title="分层架构Demo")

app.include_router(user.router)
```

## 五、全局统一响应结果（对标 SpringBoot 统一返回体）

SpringBoot 中会封装 `Result.java`，FastAPI 同样可以。

新建 `utils/response.py`：

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

class Result(BaseModel):
    code: int
    msg: str
    data: Any | None = None

    @staticmethod
    def success(data: Any = None, msg: str = "操作成功") -> Result:
        return Result(code=200, msg=msg, data=data)

    @staticmethod
    def fail(msg: str = "操作失败", code: int = 500) -> Result:
        return Result(code=code, msg=msg, data=None)
```

`from __future__ import annotations` 必须放在文件最上面。类还没定义完就写 `-> Result` 时，检查器会报 `Undefined name Result`；加了这行后，类型标注会延后解析。

接口直接 `return Result.success(...)` 即可，FastAPI 会把 Pydantic 模型序列化成 JSON：

```json
{"code": 200, "msg": "操作成功", "data": {"id": 1001, "username": "测试用户", "age": 20}}
```

如果要自己转成 dict（例如塞进 `JSONResponse`），用 **`result.model_dump()`**，不要再用 `.dict()`。

## 六、异常统一处理（对标 SpringBoot GlobalExceptionHandler）

对标 SpringBoot 全局异常捕获，统一返回错误信息，不把原生堆栈直接甩给前端。

在 `main.py` 加入：

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from utils.response import Result

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=Result.fail(msg=str(exc.detail), code=exc.status_code).model_dump(),
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=Result.fail(msg="服务器内部异常").model_dump(),
    )
```

要点：

- `JSONResponse(content=...)` 只能收 **dict / list / 基本类型**，不能直接塞 Pydantic 对象，所以要 `.model_dump()`
- 记得设置 `status_code`，否则 HTTP 状态码会一直是 200，只有 body 里的 `code` 在变化
- 生产环境不要把 `exc` 原文返回给前端，避免泄露内部信息

## 七、跨域配置（对标 SpringBoot @CrossOrigin）

前端 JS 调用接口必配。直接在 `main.py` 添加：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 写成真实前端源，不要用 "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

注意：**`allow_origins=["*"]` 不能和 `allow_credentials=True` 一起用**。浏览器会拒绝这种组合，Starlette 也会按规范处理。开发阶段如果暂时不带 Cookie，可以：

```python
allow_origins=["*"]
allow_credentials=False
```

生产环境务必改成具体前端域名。

## 八、异步接口（FastAPI 核心优势）

FastAPI **原生支持 async/await**。适合等数据库、Redis、HTTP 这类 IO；纯 CPU 计算写成 `async def` 并不会变快。

```python
@app.get("/async/demo")
async def async_demo():
    # 这里应 await 异步 IO：数据库、Redis、httpx 等
    return Result.success(msg="异步接口请求成功")

@app.get("/sync/demo")
def sync_demo():
    return Result.success(msg="同步接口请求成功")
```

总结：

- **IO 等待**（查库、调第三方）：优先 `async def` + 异步驱动
- **简单业务 / 同步 SDK**：用普通 `def` 即可
- 不要在 `async def` 里直接写阻塞的 `time.sleep()`、同步 `requests.get()`，会卡住事件循环

它和 Spring 线程池不是同一套模型：FastAPI 的 async 是事件循环 + 非阻塞 IO。

## 九、项目启动 & 生产部署

### 9.1 开发启动（热更新）

```bash
uvicorn main:app --reload --port 8000
```

`--reload` 不要和生产 `--workers` 一起用。

### 9.2 生产启动（正式环境）

Linux / 容器里常用：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

`--workers 4`：多进程提升并发，类似前面再挂一层多实例，**不是** SpringBoot 集群本身。

Windows 上 uvicorn 多 worker 支持较差，本机开发用 `--reload` 即可；上线建议 Linux 或容器。

## 十、SpringBoot & FastAPI 核心对照表（必记）

| 功能场景 | SpringBoot | FastAPI |
|---|---|---|
| 接口控制器 | `@RestController` | `APIRouter` |
| GET 请求 | `@GetMapping` | `@router.get` |
| POST 请求 | `@PostMapping` | `@router.post` |
| JSON 参数接收 | `@RequestBody` + DTO | Pydantic `BaseModel` |
| 参数校验 | Spring Validation | Pydantic 原生支持 |
| 接口文档 | 整合 Swagger / SpringDoc | 原生自带 `/docs` |
| 统一返回体 | 自定义 Result 类 | 自定义 Result 模型 |
| 全局异常处理 | `@RestControllerAdvice` | `@app.exception_handler` |
| 跨域配置 | 全局跨域配置类 | CORS 中间件 |
| 模型转 dict | Jackson 序列化 | `model_dump()`（Pydantic v2） |

## 十一、后续进阶学习路线

学完本教程，已掌握 FastAPI **企业级基础开发能力**，后续进阶方向：

1. **数据库操作**：SQLAlchemy 对标 MyBatis / MyBatis-Plus
2. **权限认证**：JWT 登录认证、接口权限（对标 Spring Security）
3. **缓存中间件**：Redis 整合
4. **日志、配置文件**：全局日志、`.env`（对标 `application.yml`）
5. **数据库迁移**：Alembic 对标 Flyway
6. **AI 接口开发**：模型推理、SSE / 流式返回（FastAPI 核心强项）

实战续篇（后台管理 Demo：登录 JWT + 用户 CRUD + 秒杀 Redis + MySQL）见：

→ [FastAPI 后台管理实战教程（登录JWT_用户CRUD_秒杀Redis_MySQL）](./FastAPI%20后台管理实战教程（登录JWT_用户CRUD_秒杀Redis_MySQL）.md)
