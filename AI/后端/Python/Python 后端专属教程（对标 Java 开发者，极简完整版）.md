# Python 后端专属教程（对标 Java 开发者，极简完整版）

## 0\. 前置：Java 与 Python 核心区别（一句话吃透）

- **Java：静态强类型、编译型、必须类和方法、语句分号结尾、严格结构**

- **Python：动态强类型、解释型、不用类也能写、缩进代替大括号、简洁极致**

写 FastAPI 后端用到的 Python，**只学本教程内容就够了**，不用学杂七杂八的语法。

## 1\. 变量与数据类型（对标 Java 基本类型 \+ 包装类）

### 1\.1 变量定义

Java 需要写类型，Python **不用声明类型，自动推导**（3\.5\+ 支持类型注解，和 Java 一样写）。

```python
# 无注解（自动推导）
name = "张三"
age = 20
score = 99.5
is_ok = True

# 有注解（后端开发推荐！和 Java 一模一样）
name: str = "张三"
age: int = 20
score: float = 99.5
is_ok: bool = True

```

### 1\.2 八大常用类型对标 Java

|Java 类型|Python 类型|说明|
|---|---|---|
|int|int|整型|
|double/float|float|浮点|
|boolean|bool|布尔：True/False（大写）|
|String|str|字符串，不可变|
|List|list|可变数组|
|Map|dict|键值对|
|Set|set|集合去重|
|null|None|空值|

## 2\. 字符串操作（对标 Java String）

Python 字符串比 Java 简洁非常多。

```python
s: str = "hello python"

# 长度
len(s)

# 包含
"python" in s

# 截取（和 Java substring 一致）
s[0:5]

# 拼接（推荐 f-string，秒杀 Java + 拼接）
name = "李四"
info = f"姓名：{name}"

# 转大小写、去除空格
s.upper()
s.lower()
s.strip()

```

## 3\. 容器类型（后端最常用，对应 Java List/Map/Set）

### 3\.1 list 列表（对应 Java ArrayList）

```python
arr: list[int] = [1, 2, 3, 4]

# 增删改查
arr.append(5)   # 末尾添加
arr.pop()       # 删除末尾
arr.remove(2)   # 删除指定元素
arr[0] = 100    # 修改

# 遍历（增强 for 循环）
for item in arr:
    print(item)

```

### 3\.2 dict 字典（对应 Java HashMap）

**后端开发高频使用，等价 Java Map**

```python
user: dict = {
    "id": 1,
    "username": "张三",
    "age": 20
}

# 取值
user["username"]
user.get("age")

# 新增/修改
user["email"] = "test@qq.com"

# 删除
del user["age"]

```

### 3\.3 set 集合（去重）

```python
s = {1,2,2,3}
# 自动去重 = {1,2,3}

```

## 4\. 运算符、判断、循环（完全对标 Java）

### 4\.1 条件判断（if/else if/else）

区别：**不用括号、不用大括号，靠缩进**

```python
age: int = 20

if age < 18:
    print("未成年")
elif age < 60:
    print("成年")
else:
    print("老年")

```

### 4\.2 循环

```python
# 1. for 增强循环（最常用）
nums = [1,2,3]
for n in nums:
    print(n)

# 2. 区间循环（for i 从0到9）
for i in range(10):
    print(i)

# 3. while 循环
i = 0
while i < 5:
    i += 1

```

## 5\. 函数（对标 Java Method）

Python 函数 = Java 方法，支持**类型注解、默认值、返回值**。

```python
# 无参无返回
def hello() -> None:
    print("hello")

# 有参有返回（标准后端写法，和 Java 一模一样）
def get_user_name(uid: int) -> str:
    if uid == 1:
        return "admin"
    return "user"

```

关键点：**\-\> 代表返回值类型**，完全对标 Java 方法返回值。

## 6\. 面向对象 OOP（对标 Java Class）

FastAPI 的 DTO、Service 全部基于面向对象，和 Java 完全一致。

### 6\.1 定义类、构造方法

```python
class User:
    # 构造方法 = Java 构造器
    def __init__(self, id: int, username: str):
        self.id = id
        self.username = username

    # 成员方法
    def get_info(self) -> dict:
        return {"id": self.id, "username": self.username}

# new 对象
user = User(1, "张三")
print(user.get_info())

```

重点：**self 等价 Java this**

### 6\.2 静态方法（对标 Java static）

```python
class UserService:
    @staticmethod
    def get_list() -> list:
        return [1,2,3]

```

## 7\. 异常处理（对标 Java try\-catch）

```python
try:
    num = 1 / 0
except Exception as e:
    print("异常：", e)
finally:
    print("最终执行")

```

## 8\. 模块与包（对标 Java package / import）

Java：包路径 \+ import
Python：文件夹就是包，py 文件就是模块

举例：

```python
# 从 routers 文件夹导入 user 对象
from routers.user import router

# 从 models.user 导入 UserDTO
from models.user import UserDTO

```

## 9\. 类型注解（后端必须掌握 = Java 强类型）

写 FastAPI 必须加类型注解，否则无法校验、无法生成文档。

```python
# 基础类型
a: int = 1

# 列表、字典泛型（对标 Java List<String>）
from typing import List, Dict

names: List[str] = ["张三", "李四"]
map_data: Dict[str, int] = {"age": 20}

# 可为空（对标 Integer 可 null）
age: int | None = None

```

## 10\. 异步语法 async/await（FastAPI 核心）

Java 异步需要线程池、CompletableFuture，Python 极简原生支持。

```python
# 异步函数
async def async_task() -> str:
    return "异步执行完成"

# FastAPI 接口直接用
@app.get("/async")
async def demo():
    res = await async_task()
    return res

```

## 11\. Java ↔ Python 速查对照表（开发必看）

|Java|Python|
|---|---|
|String|str|
|int / Integer|int / int \| None|
|boolean|bool|
|List\<T\>|list\[T\]|
|Map\<K,V\>|dict\[K,V\]|
|null|None|
|this|self|
|static|@staticmethod|
|try\-catch\-finally|try\-except\-finally|
|方法返回值|\-\> 类型注解|
|for循环|for in 循环|

## 12\. 你学完这套能做什么？

- 完全看懂、写得懂 **企业级 FastAPI 后端代码**

- 会 Python 版的 **分层架构、DTO、Service、统一返回、异常处理**

- 无缝衔接你之前学的 FastAPI 教程

- 彻底摆脱“只会 Java 看不懂 Python”的问题

> （注：部分内容可能由 AI 生成）
