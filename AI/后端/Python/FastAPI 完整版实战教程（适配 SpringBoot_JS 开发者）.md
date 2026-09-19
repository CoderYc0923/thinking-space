# FastAPI 完整版实战教程（适配 SpringBoot/JS 开发者）

## 前言：写给会 SpringBoot \+ JS 的开发者

你有 Java SpringBoot、JS 基础，学 FastAPI 会**极速上手**，核心对应关系先记牢：

- **FastAPI ≈ SpringBoot Web**：专门写接口、微服务，替代 Flask/Django 接口开发

- **Python 类型注解 ≈ Java 实体类定义**

- **Pydantic ≈ Spring Validation \+ DTO**：参数校验、数据序列化

- **FastAPI 自动文档 ≈ SpringDoc/Swagger**：开箱即用，无需配置

- **async/await ≈ Spring 异步线程池**：高并发高性能

FastAPI 相比 SpringBoot：**更少代码、零配置、启动更快、开发效率翻倍**，是目前 Python 后端、AI 接口、微服务的主流框架。

## 一、环境准备（5分钟搞定）

### 1\.1 基础环境要求

必须安装 **Python 3\.8\+**（推荐 3\.10/3\.11，兼容性最好）

验证命令（终端执行）：

```bash
python --version
# 或
python3 --version
```

### 1\.2 安装核心依赖

对比 SpringBoot：SpringBoot 靠 starter 依赖，Python 靠 pip 安装包

```bash
# 核心框架 + 运行器
pip install fastapi uvicorn

# 常用全套依赖（后续实战必备，一次性装好）
pip install pydantic python-multipart requests
```

- **fastapi**：核心框架

- **uvicorn**：ASGI 服务器（对应 SpringBoot 内嵌 Tomcat）

- **pydantic**：数据校验、模型映射（核心）

### 1\.3 项目结构（对标 SpringBoot）

极简标准结构（企业通用）：

```Plain Text
fastapi-demo/
├── main.py        # 入口文件（对标 SpringBoot 启动类）
├── routers/       # 接口路由（对标 Controller 分层）
├── models/        # 数据模型（对标 DTO/Entity）
├── services/      # 业务逻辑（对标 Service）
└── utils/         # 工具类
```

## 二、第一个 HelloWorld 项目（对标 SpringBoot 入门接口）

### 2\.1 编写启动入口 main\.py

新建 `main.py`，代码极简，无需配置类、无需注解扫描：

```python
# 导入核心类
from fastapi import FastAPI

# 初始化应用（对标 SpringBoot 启动容器）
app = FastAPI(
    title="FastAPI入门项目",
    description="适配SpringBoot开发者的实战教程",
    version="1.0.0"
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

### 2\.2 启动项目

终端执行命令（对标 SpringBoot 启动 Run）：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

参数解释：

- `main`：对应 main\.py 文件名

- `app`：文件内的 FastAPI 实例对象

- `--reload`：热更新（开发必备，改代码不用重启服务）

- `--port 8000`：端口（默认8000，可自定义）

### 2\.3 访问项目 \& 自动文档（核心亮点）

启动成功后，浏览器访问：

- 接口地址：`http://127.0.0.1:8000`

- **自动交互式文档（重点）**：`http://127.0.0.1:8000/docs`（Swagger 风格，比 SpringDoc 更简洁）

- 备用文档：`http://127.0.0.1:8000/redoc`

✅ 对比 SpringBoot：无需引入依赖、无需配置，**零成本自带接口文档**，可直接在线调试接口。

## 三、核心接口开发（对标 SpringBoot Controller）

完全对标 SpringBoot 请求方式：GET、POST、路径参数、请求参数、请求体

### 3\.1 路径参数（@PathVariable）

SpringBoot 写法：`@GetMapping("/user/{id}")`

FastAPI 写法（自带类型校验）：

```python
# 路径参数 + 类型限制（自动校验，传字符串会直接报错）
@app.get("/user/{user_id}")
def get_user(user_id: int):
    return {"userId": user_id, "username": "张三"}
```

### 3\.2 查询参数（@RequestParam）

SpringBoot 写法：`@RequestParam String name, Integer age`

```python
# 普通查询参数，可选/必填自动识别
@app.get("/search")
def search_user(name: str, age: int | None = None):
    """
    name: 必填参数
    age: 可选参数，默认None
    """
    return {"searchName": name, "age": age, "msg": "查询成功"}
```

请求地址：`/search?name=李四&age=20`

### 3\.3 POST 请求 \+ JSON 请求体（@RequestBody）

这是后端最常用场景，对标 SpringBoot **DTO 接收 JSON 参数**，FastAPI 用 Pydantic 模型实现。

```python
from pydantic import BaseModel

# 定义DTO模型（对标 UserDTO）
class UserDTO(BaseModel):
    username: str
    password: str
    age: int | None = None
    email: str | None = None

# POST接口接收JSON
@app.post("/user/add")
def add_user(user: UserDTO):
    # 自动解析JSON、自动参数校验、自动过滤多余字段
    return {
        "code": 200,
        "msg": "用户新增成功",
        "data": user.dict()
    }
```

核心优势：**不用手动判空、不用类型转换**，参数错误自动返回友好提示，比 Spring Validation 更简洁。

### 3\.4 表单提交、文件上传

```python
from fastapi import Form, UploadFile, File

# 表单提交（对标 @RequestParam 表单）
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "success": True}

# 文件上传
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename, "msg": "上传成功"}
```

## 四、分层开发（对标 SpringBoot 三层架构）

入门写完后，正式项目必须分层，杜绝所有代码写在 main\.py 中，完全对标 **Controller \+ Service \+ DTO**

### 4\.1 第一步：拆分模型 models

新建 `models/user.py`（存放所有DTO、实体模型）

```python
from pydantic import BaseModel, Field

# 用户创建DTO
class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=20, description="用户名2-20位")
    password: str = Field(min_length=6, description="密码至少6位")
    age: int | None = Field(None, ge=0, le=150, description="年龄0-150")

# 用户返回VO
class UserVO(BaseModel):
    id: int
    username: str
    age: int | None

    class Config:
        orm_mode = True  # 支持ORM对象转JSON（后续数据库必备）
```

### 4\.2 第二步：拆分路由 routers（Controller）

新建 `routers/user.py`（专门存放用户相关接口，对标 UserController）

```python
from fastapi import APIRouter
from models.user import UserCreate, UserVO

# 初始化路由（对标 @RestController）
router = APIRouter(prefix="/user", tags=["用户管理"])

# 接口（对标 @RequestMapping）
@router.post("/add", response_model=UserVO)
def create_user(user: UserCreate):
    # 调用service业务逻辑
    return {
        "id": 1001,
        "username": user.username,
        "age": user.age
    }

@router.get("/{user_id}")
def get_user_info(user_id: int):
    return {"userId": user_id, "username": "测试用户"}
```

### 4\.3 第三步：整合路由到主入口

修改 `main.py`，统一注册路由（对标 SpringBoot 自动扫描Controller）

```python
from fastapi import FastAPI
from routers import user

app = FastAPI(title="分层架构Demo")

# 注册路由
app.include_router(user.router)

```

### 4\.4 第四步：拆分业务 service

新建 `services/user_service.py`（存放核心业务逻辑，解耦Controller）

```python
from models.user import UserCreate

# 模拟数据库业务逻辑
class UserService:
    @staticmethod
    def create_user(user: UserCreate):
        # 此处可写：数据库新增、密码加密、日志记录等业务
        return {
            "id": 2001,
            "username": user.username,
            "age": user.age
        }

user_service = UserService()
```

修改 user 路由，调用 service 层，实现**彻底解耦**：

```python
from services.user_service import user_service

@router.post("/add", response_model=UserVO)
def create_user(user: UserCreate):
    res = user_service.create_user(user)
    return res
```

## 五、全局统一响应结果（对标 SpringBoot 统一返回体）

SpringBoot 中我们会封装 `Result.java` 统一返回格式，FastAPI 同样可以全局封装。

新建 `utils/response.py`

```python
from pydantic import BaseModel
from typing import Any

# 统一返回体
class Result(BaseModel):
    code: int
    msg: str
    data: Any | None = None

    # 成功响应
    @staticmethod
    def success(data: Any = None, msg: str = "操作成功") -> Result:
        return Result(code=200, msg=msg, data=data)

    # 失败响应
    @staticmethod
    def fail(msg: str = "操作失败", code: int = 500) -> Result:
        return Result(code=code, msg=msg, data=None)
```

接口使用示例：

```python
@router.get("/{user_id}")
def get_user_info(user_id: int):
    data = {"userId": user_id, "username": "测试用户"}
    return Result.success(data=data)
```

统一返回格式：

```json
{"code":200,"msg":"操作成功","data":{"userId":1001,"username":"测试用户"}}
```

## 六、异常统一处理（对标 SpringBoot GlobalExceptionHandler）

对标 SpringBoot 全局异常捕获，统一返回错误信息，不返回原生报错堆栈。

在 main\.py 加入全局异常处理器：

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from utils.response import Result

app = FastAPI()

# 全局HTTP异常捕获
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        content=Result.fail(msg=exc.detail, code=exc.status_code).dict()
    )

# 全局系统异常捕获
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        content=Result.fail(msg="服务器内部异常")
    )
```

## 七、跨域配置（对标 SpringBoot @CrossOrigin）

前端 JS 调用接口必配，解决前端跨域问题，直接在 main\.py 添加：

```python
from fastapi.middleware.cors import CORSMiddleware

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 八、异步接口（FastAPI 核心优势）

SpringBoot 异步需要手动配置线程池，FastAPI **原生支持 async/await**，高并发性能碾压同步框架。

```python
# 异步接口（高并发推荐）
@app.get("/async/demo")
async def async_demo():
    # 可执行异步IO操作：数据库、redis、网络请求
    return Result.success(msg="异步接口请求成功")

# 同步接口（简单业务使用）
@app.get("/sync/demo")
def sync_demo():
    return Result.success(msg="同步接口请求成功")
```

✅ 总结：**IO密集型业务（数据库、请求第三方）全部用 async**，性能远超 SpringBoot 同步接口。

## 九、项目启动 \& 生产部署

### 9\.1 开发启动（热更新）

```bash
uvicorn main:app --reload --port 8000
```

### 9\.2 生产启动（正式环境）

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

`--workers 4`：开启多进程，对标 SpringBoot 集群部署，提升并发能力。

## 十、SpringBoot \& FastAPI 核心对照表（必记）

|功能场景|SpringBoot|FastAPI|
|---|---|---|
|接口控制器|@RestController|APIRouter|
|GET请求|@GetMapping|@router\.get|
|POST请求|@PostMapping|@router\.post|
|JSON参数接收|@RequestBody \+ DTO|Pydantic BaseModel|
|参数校验|Spring Validation|Pydantic 原生支持|
|接口文档|整合Swagger/SpringDoc|原生自带 /docs|
|统一返回体|自定义Result类|自定义Result模型|
|全局异常处理|@RestControllerAdvice|@app\.exception\_handler|
|跨域配置|全局跨域配置类|CORS中间件一键配置|

## 十一、后续进阶学习路线

学完本教程，已掌握 FastAPI **企业级基础开发能力**，后续进阶方向：

1. **数据库操作**：SQLAlchemy 对标 MyBatis/MyBatis\-Plus

2. **权限认证**：JWT 登录认证、接口权限（对标 SpringSecurity）

3. **缓存中间件**：Redis 整合

4. **日志、配置文件**：全局日志、env配置（对标 application\.yml）

5. **数据库迁移**：Alembic 对标 Flyway

6. **AI接口开发**：模型推理、文件流式返回（FastAPI 核心强项）

> （注：部分内容可能由 AI 生成）
