```java
前端HTTP请求
    │
    ▼
【Controller层】 <─── 接收 DTO (Data Transfer Object)
   loginRequestDto          比如 dto/request/LoginRequestDto
    │
    ├── 参数校验
    └── 调用 Service
            │
            ▼
【Service 层】  <─── 业务编排，使用 Entity 与 DB 交互
     │ 
     ├── 调用 Mapper
     │       │
     │       ▼
     │   【Mapper/Dao层】  <─── 执行SQL，映射结果
     │      UserMapper         返回 user/pojo/entity/UserEntity
     │       │
     │       └── 返回 Entity
     │
     ├── 组合/处理 Entity 数据
     ├── 组装 VO (View Object)
     │      比如 vo/response/LoginResponseVo
     └── 返回 VO 给 Controller
            │
            ▼
【Controller层】
    │
    ├── 接收 VO
    └── 封装为统一响应体 (如 ApiResponse)
            │
            ▼
      返回 JSON 给前端
```



| 目录名                     | 全称/含义           | 核心职责                                                  | 所在层     |
| -------------------------- | ------------------- | --------------------------------------------------------- | ---------- |
| **controller**             | 控制器              | 接收HTTP请求，参数校验，调用Service，返回响应             | 表现层     |
| **service**                | 业务服务            | 编写核心业务逻辑，管理事务，编排多个Mapper/Dao            | 业务层     |
| **mapper / dao**           | 数据访问对象        | 与数据库交互，执行SQL（MyBatis用Mapper，JPA用Repository） | 持久层     |
| **entity / pojo / domain** | 实体/数据库映射对象 | 与数据库表结构一一对应，最简单的数据容器                  | 持久层模型 |
| **dto**                    | 数据传输对象        | 在不同层或服务间传输数据，解耦表现层和持久层              | 跨层模型   |
| **vo**                     | 视图对象            | 专门为前端展示而定制的数据模型（如加减字段、格式化日期）  | 表现层模型 |
| **common / util**          | 公共/工具类         | 存放全局工具类、常量、异常定义、通用配置                  | 基础设施   |
| **config / framework**     | 配置/框架           | Spring配置类、拦截器、过滤器、全局异常处理器等            | 基础设施   |



- **POJO (Plain Old Java Object)：** 最纯粹的概念，只是一个没有继承、没有实现接口的简单Java对象。`entity`、`dto`、`vo` 都可以叫做 POJO。有些项目专门建`pojo`目录，其实就等同于`entity`。
- **Entity：** 与数据库表严格映射，是ORM框架管理的对象。
- **Domain：** 领域模型。在复杂的领域驱动设计（DDD）中，`domain`对象不仅有数据，还有自己的行为方法。**初学者先按 `entity` = `pojo` = `domain` 来理解即可。**



- **DAO (Data Access Object)：** 是通用概念，指操作数据库的类。
- **Mapper：** 是MyBatis框架对DAO的具体称呼，通过XML或注解定义SQL。**当你用MyBatis时，就叫mapper。**
- **Repository：** 是Spring Data JPA对DAO的称呼，提供了很多现成的CRUD方法。**当你用JPA时，就叫repository。** 你只能三选一，不能混用。



- **DTO (Data Transfer Object)：** 用于**服务端内部**各层或不同服务之间的传输。例如：从Controller传给Service的叫`LoginRequestDto`，从Service传给远程支付接口的叫`PayRequestDto`。**它关注的是“传输了什么数据”。**
- **VO (View Object)：** 专门为**前端视图**设计，从后端返回给前端。**它关注的是“视图需要展示什么数据”。** 例如，数据库的`create_time`是Date，但VO里的`createTime`可以是格式化好的String。同一个Entity，可能根据不同页面需求生成不同的VO。



- **common/util：** 放你自己写的、和业务无关的工具类（如`JwtUtil`, `StringUtils`）、全局常量、基础异常类。

- **framework/config：** 放Spring框架的配置（如`WebMvcConfig`用于配置拦截器）、全局异常处理器（`GlobalExceptionHandler`）、切面（AOP）等。这是对整个框架进行定制的目录。