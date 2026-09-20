# Python 后端专属教程（对标 Java / JS 开发者，极简完整版）

## 0. 前置：Java / Python / JS 核心区别

你会 Java + JS 的话：Python 语感更接近 **JS（动态、脚本、async）**，工程纪律更接近 **Java（注解、分层、强约束习惯）**；但类型软硬程度和 JS 又不一样。

### 0.1 一句话吃透

- **Java：静态强类型**——变量先定类型，编译期拦住大部分类型错误
- **Python：动态强类型**——变量可不写类型，但 `"1" + 2` 会直接报错（不瞎转类型）
- **JS：动态弱类型**——变量可不写类型，且常自动隐式转换（`"1" + 2 === "12"`）

> 强/弱看「会不会偷偷帮你转类型」；静/动态看「类型绑在变量上还是绑在值上、何时检查」。

### 0.2 对照总表（Java / Python / JS）

| 维度 | Java | Python | JS（含 Node） |
|---|---|---|---|
| 类型系统 | 静态强类型 | 动态强类型 | 动态弱类型（TS 可补静态） |
| 类型检查 | `javac` 强制 | 默认运行时；注解 + mypy / Pydantic | 默认运行时；TS 编译期 / JSDoc |
| 执行方式 | 字节码 → JVM | 字节码 → CPython 等 | 引擎 JIT（V8 等）→ 浏览器 / Node |
| 程序入口 | `main` | 自上而下；`if __name__ == "__main__"` | 自上而下；Node 指定入口文件 |
| 结构 | 几乎一切在类里 | 函数/脚本可独立，类可选 | 函数/模块一等公民，class 可选 |
| 代码块 | `{ }` | **缩进**（通常 4 空格） | `{ }` |
| 语句结束 | `;` 必须 | 一般不用 | `;` 可省略（ASI），团队常强制加） |
| 空值 | `null` | `None` | `null` + **`undefined`（两套）** |
| 布尔 | `true` / `false` | `True` / `False` | `true` / `false` |
| 相等比较 | `==` / `equals` | `==`（值）/ `is`（同一对象） | `==` 会强转；**务必用 `===`** |
| 创建对象 | `new User()` | `User()`（无 `new`） | `new User()`（class）；对象字面量 `{}` |
| 当前实例 | `this` | `self`（显式写在参数里） | `this`（绑定规则多，易踩坑） |
| 字符串模板 | `+` / `formatted` | **f-string**：`f"{name}"` | **模板字符串**：`` `${name}` `` |
| 数组/列表 | `List` / `ArrayList` | `list` | `Array` |
| 键值对 | `Map` / `HashMap` | `dict` | `Object` / `Map` |
| 包与模块 | `package` + `import` | 包/模块 + `import` | ESM `import` / CJS `require` |
| 依赖管理 | Maven / Gradle | pip + venv / poetry / uv | npm / pnpm / yarn |
| 后端常见栈 | Spring Boot | FastAPI / Django / Flask | Express / Nest / Koa / Fastify |
| 并发常见模型 | 多线程、线程池、虚拟线程 | **asyncio**；CPU 多用进程 | **事件循环 + Promise/async**（和 Python 很像） |
| 性能体感 | 高、启动偏重 | 开发快；热路径可上扩展/多进程 | Node IO 强；CPU 密集同样别指望单线程 |
| 生态侧重 | 企业后端、Android、大数据 | Web、**AI/数据**、脚本 | 前端为主；Node 全栈、工具链 |

### 0.3 用 JS 经验学 Python：像在哪、坑在哪

**像（可直接迁移直觉）**

| JS | Python |
|---|---|
| `const arr = [1,2]` | `arr = [1, 2]` |
| `obj.a` / `obj["a"]` | `d["a"]`（属性访问更常写成下标；对象用 `obj.a`） |
| `` `hi ${name}` `` | `f"hi {name}"` |
| `async/await` + 事件循环 | `async/await` + asyncio（模型很像） |
| `try/catch/finally` | `try/except/finally` |
| `export` / `import` | `from x import y` |
| `null` | `None`（但 JS 还有 `undefined`） |
| `Array.map/filter` | 列表推导 / 生成器；也有 `map`/`filter`（更常用推导式） |

**不像（别按 JS 惯性写）**

1. **弱类型没有了**：Python 不会 `"1" + 2`；JS 会变成 `"12"`。
2. **只有一个「空」**：`None`，没有 `undefined`。
3. **缩进是语法**，不能靠 `{}` 定块。
4. **`this` vs `self`**：Python 方法里必须写 `self` 参数；没有 JS 那种 `this` 绑定漂移（反而更死板、更好懂）。
5. **布尔字面量**：`True`/`False`，不是 `true`/`false`。
6. **dict 键通常要加引号**：`{"id": 1}`；JS 对象键常可写标识符 ` { id: 1 }`。
7. **没有 `===`**：`==` 比的是值相等；比「是不是同一个对象」用 `is`（尤其 `is None`）。

### 0.4 Java / JS 同学一起容易踩的 Python 坑

1. **没有 Java 编译期护栏**：类型注解默认不强制；写错可能运行到才炸（FastAPI/Pydantic 校验是另一层）。
2. **缩进就是语法**：错了直接 `IndentationError`。
3. **`list.remove(2)` 按值删**，不是 Java 按下标删，也不是 JS `splice`。
4. **`async/await` ≠ Java 线程池**：和 **Node 事件循环**一类——适合 IO，不是多开 OS 线程。
5. **GIL（CPython）**：同进程多线程难吃满多核；CPU 密集常用**多进程**（Node 也常靠 worker / 多进程）。
6. **可变默认参数**：`def f(a=[])` 危险（多次调用共享同一个 list）；应用 `None` 再在函数里新建。
7. **没有 Java 式 `private`**：`_name` 只是约定；JS 的 `#private` / TypeScript `private` 也不要直接对号入座。

### 0.5 学 Python 后端怎么迁移心智

| Java | JS / Node | Python / FastAPI |
|---|---|---|
| Controller | Router / Controller（Nest） | `APIRouter` / 路由函数 |
| Service | Service 层 | service 模块/类 |
| DTO + 校验注解 | class-validator / Zod | **Pydantic `BaseModel`** |
| Spring DI | Nest DI / 手动注入 | FastAPI **`Depends`** |
| `Optional<T>` | `T \| null \| undefined` | `T \| None` |
| 接口 + 实现类 | interface / type | 常先函数；需要时再用 Protocol |
| Maven 多模块 | monorepo + npm workspaces | 包/目录分层 + 虚拟环境 |

写 FastAPI 后端用到的 Python，**本教程覆盖主路径语法**；进阶细节（装饰器原理、元类、多进程等）可后补。

## 1. 变量与数据类型（对标 Java / JS）

### 1.1 变量定义

- Java：必须写类型  
- JS：`let` / `const`，类型靠值；TS 才写类型  
- Python：**赋值时不用声明类型**；可加注解（像 TS，但默认运行时不强制）

| | Java | Python 注解 | JS / TS |
|---|---|---|---|
| 何时检查 | 编译期强制 | 默认运行时不强制（IDE / mypy / Pydantic） | JS 运行时；TS 编译期 |
| 写错会怎样 | 编译失败 | 普通脚本可能仍能跑；FastAPI 入参会校验 | JS 可能静默异常结果；TS 编译报错 |

```python
# 无注解（像 JS：let name = "张三"）
name = "张三"
age = 20
score = 99.5
is_ok = True

# 有注解（像 TS：let name: string = "张三"；后端推荐）
name: str = "张三"
age: int = 20
score: float = 99.5
is_ok: bool = True
```

### 1.2 常用类型三栏对照

| Java | Python | JS | 说明 |
|---|---|---|---|
| int / Integer | int | number | Python int 无长度上限；JS number 是双精度浮点 |
| double / float | float | number | JS 没有单独 int 类型（BigInt 另说） |
| boolean | bool | boolean | Python 必须 `True`/`False` 大写 |
| String | str | string | 都不可变（JS 字符串也不可变） |
| List / ArrayList | list | Array | 都可变、有序 |
| Map / HashMap | dict | Object / Map | JS 普通对象 ≈ dict；真 Map 更少用一点 |
| Set / HashSet | set | Set | 去重 |
| null | None | null / **undefined** | JS 两套空值，Python 只有 None |

## 2. 字符串操作（对标 Java String）

Python 字符串操作更短，切片半开区间和 Java `substring` 类似。

```python
s: str = "hello python"

# 长度
len(s)

# 包含（对标 contains）
"python" in s

# 截取：s[start:end]，含 start、不含 end（和 Java substring(start, end) 一样）
s[0:5]   # "hello"
# 另：Python 还支持 s[:5]、s[-6:] 等，Java 没有这种写法

# 拼接（推荐 f-string）
name = "李四"
info = f"姓名：{name}"

# 转大小写、去除空格
s.upper()
s.lower()
s.strip()
```

## 3. 容器类型（后端最常用，对应 Java List/Map/Set）

### 3.1 list 列表（对应 Java ArrayList）

```python
arr: list[int] = [1, 2, 3, 4]

# 增删改查
arr.append(5)    # 末尾添加
arr.pop()        # 删除并返回末尾元素；pop(i) 按索引删
arr.remove(2)    # 按【值】删除第一次出现的 2（不是按下标！）
del arr[0]       # 按【下标】删除（对标 list.remove(index)）
arr[0] = 100     # 修改

# 遍历（对标增强 for）
for item in arr:
    print(item)
```

> Java 注意点：`list.remove(2)` 若 2 是 `int`，重载的是**按下标删**；Python 的 `remove(2)` 永远是**按值删**。按索引请用 `pop(i)` 或 `del arr[i]`。

### 3.2 dict 字典（对应 Java HashMap）

**后端高频，等价 Java Map。**

```python
user: dict[str, object] = {
    "id": 1,
    "username": "张三",
    "age": 20,
}

# 取值：[] 键不存在会 KeyError；get 更安全
user["username"]
user.get("age")
user.get("missing", 0)  # 默认值

# 新增/修改
user["email"] = "test@qq.com"

# 删除
del user["age"]
```

### 3.3 set 集合（去重）

```python
s = {1, 2, 2, 3}
# 自动去重 → {1, 2, 3}
```

## 4. 运算符、判断、循环（对标 Java）

### 4.1 条件判断（if / else if / else）

区别：**条件外层常省略括号；没有大括号，靠缩进**；`else if` 写成 `elif`。

```python
age: int = 20

if age < 18:
    print("未成年")
elif age < 60:
    print("成年")
else:
    print("老年")
```

### 4.2 循环

```python
# 1. for-each（最常用）
nums = [1, 2, 3]
for n in nums:
    print(n)

# 2. 区间：range(10) → 0..9（不含 10）
for i in range(10):
    print(i)

# 3. while
i = 0
while i < 5:
    i += 1
```

## 5. 函数（对标 Java Method）

Python 函数 ≈ Java 方法，可写参数注解、默认值、返回值注解。

```python
# 无参无返回
def hello() -> None:
    print("hello")

# 有参有返回（后端常用写法）
def get_user_name(uid: int) -> str:
    if uid == 1:
        return "admin"
    return "user"
```

关键点：`->` 表示**返回值类型注解**，对标 Java 方法返回类型；同样默认不在运行时强制检查。

## 6. 面向对象 OOP（对标 Java Class）

FastAPI 的 DTO（Pydantic 模型）、Service 会用到类；整体像 Java，但**没有** Java 那种强制访问修饰符 / 方法重载，别当成「完全一致」。

### 6.1 定义类、构造方法

```python
class User:
    # 构造方法 ≈ Java 构造器
    def __init__(self, id: int, username: str):
        self.id = id
        self.username = username

    # 实例方法：第一个参数必须是 self（≈ this）
    def get_info(self) -> dict:
        return {"id": self.id, "username": self.username}

# 创建对象：没有 new
user = User(1, "张三")
print(user.get_info())
```

重点：**`self` 等价 Java `this`**，调用时不用自己传，解释器自动传入。

### 6.2 静态方法（对标 Java static）

```python
class UserService:
    @staticmethod
    def get_list() -> list[int]:
        return [1, 2, 3]

# 调用：UserService.get_list()
```

> 另有 `@classmethod`（第一个参数是 `cls`，表示类本身），和 Java static 不完全一样；入门先会 `@staticmethod` 即可。

## 7. 异常处理（对标 Java try-catch）

`catch` → `except`；可捕获具体异常，不必总抓最宽的 `Exception`。

```python
try:
    num = 1 / 0
except ZeroDivisionError as e:
    print("除零：", e)
except Exception as e:
    print("其他异常：", e)
finally:
    print("最终执行")
```

## 8. 模块与包（对标 Java package / import）

- Java：包路径 + `import`
- Python：一个 `.py` 文件 = 模块；文件夹（通常含 `__init__.py`）= 包

```python
# 从 routers 包导入 user 模块里的 router
from routers.user import router

# 从 models.user 导入 UserDTO
from models.user import UserDTO
```

## 9. 类型注解（后端必须掌握）

写 FastAPI 建议加注解：请求体/查询参数靠它做校验和生成 OpenAPI 文档。

**Python 3.9+** 直接用内置泛型即可（推荐，和本教程前面的 `list[int]` 一致）：

```python
a: int = 1

# 对标 Java List<String>、Map<String, Integer>
names: list[str] = ["张三", "李四"]
map_data: dict[str, int] = {"age": 20}

# 可为空（对标 Integer 可为 null）
# int | None 需要 Python 3.10+；更老版本用 Optional[int]
age: int | None = None
```

> 旧写法 `from typing import List, Dict, Optional` 在 3.8 及以前常见；新项目优先 `list[str]` / `dict[str, int]` / `int | None`。

## 10. 异步语法 async/await（FastAPI 核心）

对你这种会 JS 的人：**Python asyncio ≈ Node 事件循环 + Promise/async**，都不是 Java 那种线程池并行。

| | Java 常见异步 | Python `async/await` | JS / Node `async/await` |
|---|---|---|---|
| 模型 | 多线程 / 线程池 | **单线程事件循环** | **单线程事件循环** |
| 适合 | CPU + IO（看写法） | 高并发 IO | 高并发 IO |
| CPU 密集 | 线程 / 并行流 | 多进程 / 扩展 | Worker Threads / 多进程 |

```python
# 异步函数：遇到 await 让出事件循环（直觉同 JS async function）
async def async_task() -> str:
    return "异步执行完成"

# FastAPI 接口可以直接声明 async
# app = FastAPI() 需先创建
@app.get("/async")
async def demo():
    res = await async_task()
    return res
```

## 11. Java ↔ Python ↔ JS 速查对照表（开发必看）

| Java | Python | JS |
|---|---|---|
| String | str | string |
| int / Integer | int / int \| None | number / null \| undefined |
| boolean | bool（True/False） | boolean（true/false） |
| List\<T\> | list\[T\] | Array / T\[\]（TS） |
| Map\<K,V\> | dict\[K, V\] | Object / Map |
| null | None | null / undefined |
| this | self | this |
| static | @staticmethod | static |
| try-catch-finally | try-except-finally | try-catch-finally |
| 方法返回值类型 | -> 注解 | TS: `: T` / JSDoc |
| for-each | for x in ... | for...of / forEach |
| else if | elif | else if |
| new User() | User() | new User() |
| `"a" + b` 拼接 | f"{a}{b}" | `` `${a}${b}` `` |
| equals | == / is | ===（别用 ==） |

## 12. 你学完这套能做什么？

- 看懂、写出常见 **FastAPI 后端代码** 里的 Python 语法
- 用 **Java 的分层习惯 + JS 的 async 直觉** 快速上手 Python 后端
- 对接 **DTO / Service / 统一返回 / 异常处理** 写法
- 衔接后续 FastAPI 实战教程

> （注：部分内容可能由 AI 生成；本版已按常见事实错误做过校对，并加入 JS 三栏对照。）
