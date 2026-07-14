# Java & Spring 学习路线图（前端工程师转型版）

> **适用人群**：前端开发工程师转型后端/全栈，有 JavaScript/TypeScript 编程基础  
> **目标方向**：Java 全栈开发 + 制造业 IT 场景 + AI Agent 时代适配  
> **预计总时长**：3~6 个月（业余学习）

---

## 目录

1. [学习前提与心态准备](#1-学习前提与心态准备)
2. [总览路线图](#2-总览路线图)
3. [第一阶段：Java 基础（4~6 周）](#3-第一阶段java-基础46-周)
4. [第二阶段：数据库与持久层（2~3 周）](#4-第二阶段数据库与持久层23-周)
5. [第三阶段：Spring 全家桶核心（6~8 周）](#5-第三阶段spring-全家桶核心68-周)
6. [第四阶段：工程化与运维（2~3 周）](#6-第四阶段工程化与运维23-周)
7. [第五阶段：微服务与进阶（4~6 周）](#7-第五阶段微服务与进阶46-周)
8. [前端对照表：JS/TS → Java 速查](#8-前端对照表jsts--java-速查)
9. [项目实战建议](#9-项目实战建议)
10. [学习资源推荐](#10-学习资源推荐)

---

## 1. 学习前提与心态准备

### 你已经具备的优势 🎯

| 前端经验 | 在 Java 后端的对应 |
|----------|-------------------|
| JavaScript 异步编程（Promise/async-await） | Java 多线程、CompletableFuture、响应式编程 |
| TypeScript 类型系统 | Java 强类型、泛型、接口 |
| Node.js npm 包管理 | Maven / Gradle 依赖管理 |
| HTTP 协议、RESTful API 设计 | Spring MVC 控制器 |
| JSON 序列化/反序列化 | Jackson / Gson / Fastjson |
| 前端路由 | Spring MVC 路由映射 |
| 状态管理 | 数据库事务、Redis 缓存 |
| ESLint / Prettier | Checkstyle / SpotBugs |

### 需要适应的地方 ⚠️

1. **编译型语言**：每次改代码需要重新编译运行（不过 IDE 已经让这几乎无感）
2. **面向对象深入人心**：一切皆类，设计模式无处不在
3. **配置繁琐但现代化**：传统 Spring 配置多，但 Spring Boot 已极大简化
4. **启动慢**：Java 应用启动比 Node.js 慢，但 JVM 预热后性能强劲
5. **内存占用大**：JVM 起步内存比 V8 大，但可通过 JVM 参数调优

---

## 2. 总览路线图

```
┌─────────────────────────────────────────────────────────────┐
│                    Java & Spring 学习路线                     │
├───────────┬───────────┬───────────────┬───────────┬─────────┤
│  第一阶段  │  第二阶段  │    第三阶段    │  第四阶段  │ 第五阶段 │
│  Java基础  │ 数据库持久 │ Spring全家桶   │ 工程化运维 │ 微服务进阶│
│  4~6周    │  2~3周    │    6~8周      │  2~3周    │  4~6周   │
├───────────┼───────────┼───────────────┼───────────┼─────────┤
│ • JDK安装  │ • MySQL    │ • Spring Boot │ • Docker   │ • Spring │
│ • 基础语法  │ • JDBC     │ • Spring MVC  │ • Linux    │   Cloud  │
│ • OOP     │ • MyBatis  │ • Spring Data │ • CI/CD   │ • Nacos  │
│ • 集合框架  │ • JPA     │   JPA        │ • 监控     │ • 消息队列│
│ • 异常处理  │ • Redis   │ • Spring      │ • 安全     │ • 分库分表│
│ • IO/线程  │ • 事务管理 │   Security   │ • 部署     │ • 性能优化│
│ • Maven   │           │ • 参数校验    │           │         │
└───────────┴───────────┴───────────────┴───────────┴─────────┘
```

---

## 3. 第一阶段：Java 基础（4~6 周）

> **目标**：能用 Java 写 CRUD 程序，理解 OOP 与 JS 的区别

### 第 1 周：环境搭建 & 基础语法

| 主题 | 内容 | JS/TS 对比 |
|------|------|-----------|
| **JDK 安装** | JDK 17/21 LTS，配置 JAVA_HOME | 类比 nvm 管理 Node 版本 |
| **IDE** | IntelliJ IDEA Community（免费） | 类比 VS Code + 插件 |
| **Hello World** | 理解 `public static void main` | Node 里直接跑脚本，Java 需要入口类 |
| **变量与类型** | `int, long, double, boolean, char, String` | JS 弱类型 vs Java 强类型，`const` ≈ `final` |
| **运算符** | 算术、比较、逻辑、三元 | 基本一致，注意 Java 的 `/` 整数除法 |
| **控制流** | `if-else, switch, for, while, for-each` | 多了 `for-each`（类似 `for...of`） |
| **数组** | `int[] arr = new int[5]` | `const arr = new Array(5)`，Java 数组长度固定 |

**📌 实战练习**：写一个命令行程序，输入数字输出九九乘法表

### 第 2 周：面向对象编程（重点！）

| 主题 | 内容 | JS/TS 对比 |
|------|------|-----------|
| **类与对象** | `class Person { }`，`new Person()` | ES6 class 就是借鉴 Java 的！语法很像 |
| **封装** | `private/default/protected/public` | TS 有 `private/public`，Java 更严格 |
| **继承** | `class Dog extends Animal` | 都是单继承，JS class 也是单继承 |
| **多态** | 方法重写 `@Override`、方法重载 | JS 没有重载，靠参数判断 |
| **接口** | `interface` + `implements` | 和 TS interface 概念一致 |
| **抽象类** | `abstract class` | TS 也有 `abstract class` |
| **静态成员** | `static` 修饰 | 和 JS `static` 一致 |
| **内部类** | 成员内部类、静态内部类、匿名内部类 | 前端少见，相当于回调/闭包的另一种写法 |

**📌 实战练习**：设计一个「员工管理系统」的类结构（Employee、Manager、Department）

### 第 3 周：Java 核心 API

| 主题 | 内容 | JS/TS 对比 |
|------|------|-----------|
| **String** | `StringBuilder`、字符串方法 | JS 的 String 方法很丰富，Java 也不差 |
| **集合框架** | `List`（ArrayList/LinkedList） | 类比 JS Array |
| | `Set`（HashSet/TreeSet） | 类比 JS Set |
| | `Map`（HashMap/TreeMap） | 类比 JS Map / Object |
| **泛型** | `<T>` 类型参数 | TS 的泛型就是从 Java/C# 来的，基本一样！ |
| **包装类** | `Integer, Long, Double` 等 | JS 自动装箱拆箱，Java 需要手动或自动 |
| **枚举** | `enum` | TS 的 `enum`，几乎一模一样 |
| **日期时间** | `LocalDate, LocalDateTime, Instant` | 类比 `dayjs` / `date-fns`，Java 8+ 的 API 很好用 |
| **Optional** | 避免 null 判断 | 类比 TS 的 `?.` 可选链 + `??` |

**📌 实战练习**：用集合框架实现一个简易「购物车」，支持增删改查和去重

### 第 4 周：异常处理 & IO 流

| 主题 | 内容 | JS/TS 对比 |
|------|------|-----------|
| **异常处理** | `try-catch-finally`、`throws` | JS 也有 try-catch，但 Java 强制检查型异常 |
| **自定义异常** | `extends Exception/RuntimeException` | `extends Error` |
| **File IO** | `Files`, `Path`, `BufferedReader` | 类比 Node.js `fs` 模块 |
| **序列化** | `Serializable` 接口 | 类比 `JSON.stringify/parse`，但 Java 有二进制序列化 |
| **NIO** | Channel、Buffer 概念（了解即可） | 类比 Node.js Stream |

### 第 5~6 周：多线程 & Lambda & 构建工具

| 主题 | 内容 | JS/TS 对比 |
|------|------|-----------|
| **Lambda 表达式** | `(x) -> x * 2` | 几乎就是 JS 箭头函数 `(x) => x * 2` |
| **Stream API** | `list.stream().filter().map().collect()` | JS 数组链式调用 `.filter().map().reduce()`，**超级像！** |
| **函数式接口** | `Function<T,R>`, `Predicate<T>`, `Consumer<T>` | TS 里 `(x: T) => R` 类型定义 |
| **线程基础** | `Thread`、`Runnable` | JS 是单线程，这是新概念，注意理解 |
| **线程池** | `ExecutorService` | 类比 Node.js `worker_threads` 池 |
| **CompletableFuture** | 异步编排 | 相当于 `Promise.all().then()`，语法不同但思想一致 |
| **Maven** | `pom.xml`、依赖管理、生命周期 | 相当于 `package.json` + `npm install` + webpack |
| **Gradle** | 了解即可，Maven 为主 | 更现代的构建工具，类似 Vite 对比 webpack |

**📌 阶段项目**：用纯 Java 写一个「命令行 TODO 应用」，支持增删改查、持久化到文件、多线程批量导入

---

## 4. 第二阶段：数据库与持久层（2~3 周）

> **目标**：掌握 MySQL 基本操作和 Java 数据库访问

### MySQL 基础

| 主题 | 内容 |
|------|------|
| 安装 | Docker 安装 MySQL 8.x（你已有 Docker 经验） |
| DDL | `CREATE TABLE`、数据类型、主键、索引 |
| DML | `INSERT/UPDATE/DELETE/SELECT` |
| 查询 | `WHERE`、`JOIN`（INNER/LEFT/RIGHT）、`GROUP BY`、`HAVING` |
| 索引 | B+Tree 索引原理、联合索引、最左前缀 |
| 事务 | ACID、隔离级别、`BEGIN/COMMIT/ROLLBACK` |

### JDBC 基础

| 主题 | 内容 |
|------|------|
| 连接 | `DriverManager`、连接字符串 |
| Statement | `Statement`、`PreparedStatement`（防 SQL 注入） |
| ResultSet | 结果集遍历 |
| 连接池 | HikariCP（Spring Boot 默认） |

### MyBatis / MyBatis-Plus

| 主题 | 内容 |
|------|------|
| 核心概念 | `SqlSessionFactory`、Mapper 接口、XML 映射 |
| 注解方式 | `@Select`、`@Insert`、`@Update`、`@Delete` |
| 动态 SQL | `<if>`, `<foreach>`, `<where>` |
| MyBatis-Plus | 增强工具，内置 CRUD、分页、条件构造器 |

### Spring Data JPA

| 主题 | 内容 |
|------|------|
| 核心概念 | Entity、Repository、JPQL |
| 方法命名查询 | `findByXxxAndYyy` 自动解析 |
| 关联映射 | `@OneToMany`、`@ManyToOne`、`@ManyToMany` |
| 对比选型 | MyBatis 灵活 vs JPA 规整，制造业常用 MyBatis |

**📌 阶段项目**：设计一个「物料管理系统」的数据库，用 MyBatis-Plus 实现 CRUD API

---

## 5. 第三阶段：Spring 全家桶核心（6~8 周）

> **目标**：能用 Spring Boot 搭建企业级后端服务

### 第 1~2 周：Spring Boot 入门

| 主题 | 内容 | Node.js 类比 |
|------|------|-------------|
| **Spring 框架理念** | IoC 控制反转、DI 依赖注入 | Node.js 里很少见，这是 Java 核心思想 |
| **Spring Boot 项目结构** | `src/main/java`、`resources`、`application.yml` | 类比 Express 项目结构 |
| **启动类** | `@SpringBootApplication` | 类比 `app.listen()` |
| **Bean 管理** | `@Component`、`@Service`、`@Repository`、`@Autowired` | 服务层组件化 |
| **配置** | `application.yml`、`@Value`、`@ConfigurationProperties` | 类比 `.env` + `process.env` |
| **Profile** | 多环境配置 `application-dev.yml` | 类比 `NODE_ENV` |
| **Lombok** | `@Data`、`@Builder`、`@Slf4j` | 减少样板代码的神器 |

### 第 3~4 周：Spring MVC（Web 层）

| 主题 | 内容 | Node.js 类比 |
|------|------|-------------|
| **控制器** | `@RestController`、`@RequestMapping` | Express Router |
| **请求映射** | `@GetMapping`、`@PostMapping`、`@PutMapping`、`@DeleteMapping` | `router.get/post/put/delete` |
| **参数接收** | `@RequestParam`、`@PathVariable`、`@RequestBody` | `req.query`、`req.params`、`req.body` |
| **响应封装** | 统一返回格式 `Result<T>` | 中间件统一包装响应 |
| **全局异常处理** | `@RestControllerAdvice` + `@ExceptionHandler` | Express 错误中间件 |
| **拦截器** | `HandlerInterceptor` | Express 中间件 |
| **过滤器** | `Filter` | 和中间件机制类似 |
| **跨域** | `@CrossOrigin` / `CorsFilter` | `cors()` 中间件 |
| **文件上传** | `MultipartFile` | `multer` |

### 第 5 周：参数校验 & 安全

| 主题 | 内容 |
|------|------|
| **Bean Validation** | `@NotNull`、`@NotBlank`、`@Size`、`@Email` 等 |
| **分组校验** | 新增/修改不同校验规则 |
| **自定义校验** | 自定义注解 + Validator |
| **Spring Security** | 认证（Authentication）与授权（Authorization） |
| **JWT 认证** | 无状态 Token 认证方案（你之前学过相关概念） |
| **方法级安全** | `@PreAuthorize`、`@Secured` |

### 第 6 周：缓存 & 定时任务 & 邮件

| 主题 | 内容 |
|------|------|
| **Spring Cache** | `@Cacheable`、`@CacheEvict`、`@CachePut` |
| **Redis 集成** | Spring Data Redis、`RedisTemplate` |
| **定时任务** | `@Scheduled`、Cron 表达式 |
| **异步任务** | `@Async` + `@EnableAsync` |
| **邮件发送** | JavaMailSender |

### 第 7~8 周：整合实战

| 主题 | 内容 |
|------|------|
| **日志** | SLF4J + Logback，日志级别、输出格式 |
| **Swagger/Knife4j** | API 文档自动生成 |
| **单元测试** | JUnit 5 + Mockito |
| **集成测试** | `@SpringBootTest`、Testcontainers |

**📌 阶段项目**：搭建一个「制造业设备巡检系统」后端——设备管理、巡检计划、巡检记录、异常上报

---

## 6. 第四阶段：工程化与运维（2~3 周）

> **目标**：能独立部署一个 Spring Boot 应用到服务器

| 主题 | 内容 | 你已有的优势 |
|------|------|-------------|
| **Maven 多模块** | 父 POM、模块拆分 | 类比 monorepo |
| **Docker 化** | 写 Dockerfile、docker-compose | **你已经很熟！** |
| **JVM 参数** | `-Xmx`、`-Xms`、GC 选择 | 新知识 |
| **应用监控** | Actuator + Prometheus + Grafana | 概念是通用的 |
| **Nginx 反代** | 负载均衡、SSL 终止 | 已有 Nginx 基础 |
| **Linux 命令** | `ps`、`top`、`tail`、`journalctl` | 你正在学这个 |
| **systemd** | 服务管理 | 你正在学这个 |
| **宝塔面板部署** | 一键部署 Java 项目 | **你的环境！** |

**📌 实战**：把第三阶段的项目 Docker 化，部署到你的 Linux 服务器上

---

## 7. 第五阶段：微服务与进阶（4~6 周）

> **目标**：理解微服务架构，能参与企业级项目

| 主题 | 内容 |
|------|------|
| **微服务概念** | 服务拆分原则、CAP 理论 |
| **Spring Cloud** | 全家桶概览：Gateway、Nacos、Feign、Sentinel |
| **服务注册与发现** | Nacos / Consul / Eureka |
| **配置中心** | Nacos Config |
| **服务调用** | OpenFeign 声明式调用 |
| **网关** | Spring Cloud Gateway |
| **熔断降级** | Sentinel |
| **消息队列** | RabbitMQ / RocketMQ 基础 |
| **分布式事务** | Seata 或最终一致性方案 |
| **分库分表** | ShardingSphere（你之前学过，正好衔接！） |

---

## 8. 前端对照表：JS/TS → Java 速查

### 语法速查

| JavaScript/TypeScript | Java |
|----------------------|------|
| `const name = 'Alice'` | `final String name = "Alice";` |
| `let age = 25` | `int age = 25;` 或 `var age = 25;`（Java 10+） |
| `const arr = [1, 2, 3]` | `int[] arr = {1, 2, 3};` 或 `List<Integer> list = List.of(1, 2, 3);` |
| `arr.push(4)` | `list.add(4);` |
| `arr.map(x => x * 2)` | `list.stream().map(x -> x * 2).toList()` |
| `arr.filter(x => x > 2)` | `list.stream().filter(x -> x > 2).toList()` |
| `arr.find(x => x === 3)` | `list.stream().filter(x -> x == 3).findFirst().orElse(null)` |
| `{...obj, name: 'Bob'}` | 需要手动 set 或用 MapStruct 映射 |
| `?.` 可选链 | `Optional.ofNullable(x).map(...)` |
| `??` 空值合并 | `Objects.requireNonNullElse(x, defaultValue)` |
| `typeof x` | `x.getClass().getSimpleName()` |
| `'hello'.toUpperCase()` | `"hello".toUpperCase()` |
| `` `Hello ${name}` `` | `"Hello " + name` 或 `String.format("Hello %s", name)` |
| `JSON.stringify(obj)` | `new ObjectMapper().writeValueAsString(obj)`（Jackson） |
| `JSON.parse(str)` | `new ObjectMapper().readValue(str, Class.class)` |
| `async/await` | `CompletableFuture` 链式调用 |
| `export default` | `public class` + import |
| `interface User { }` | `interface User { }`（几乎一样！） |
| `type Result<T> = { }` | `class Result<T> { }` |

### 项目结构对照

| Node.js 项目 | Spring Boot 项目 |
|-------------|-----------------|
| `package.json` | `pom.xml` |
| `node_modules/` | `~/.m2/repository/`（Maven 本地仓库） |
| `src/index.ts` | `src/main/java/.../Application.java` |
| `src/routes/` | Controller 类（`@RestController`） |
| `src/services/` | Service 类（`@Service`） |
| `src/models/` | Entity 类（`@Entity`）或 DTO |
| `src/middleware/` | Filter / Interceptor |
| `.env` | `application.yml` |
| `tsconfig.json` | `pom.xml` 中的编译配置 |

---

## 9. 项目实战建议

### 制造业 IT 方向推荐项目

| 项目名称 | 难度 | 涉及技术 |
|----------|------|---------|
| **物料管理系统** | ⭐⭐ | Spring Boot + MyBatis-Plus + MySQL + RBAC 权限 |
| **设备巡检系统** | ⭐⭐⭐ | Spring Boot + JPA + Redis + 定时任务 + 文件导出 |
| **生产报工系统** | ⭐⭐⭐ | Spring Boot + 工作流引擎 + 消息队列 |
| **质量追溯系统** | ⭐⭐⭐⭐ | Spring Cloud + ShardingSphere + ES + 多服务 |
| **MES 简化版** | ⭐⭐⭐⭐⭐ | 微服务全家桶 + 实时数据处理 |

### 通用练习项目

| 项目名称 | 难度 | 涉及技术 |
|----------|------|---------|
| **RESTful API 脚手架** | ⭐ | Spring Boot + JPA + Swagger + 统一返回 |
| **RBAC 权限系统** | ⭐⭐ | Spring Boot + Security + JWT + Redis |
| **博客系统** | ⭐⭐ | Spring Boot + MyBatis + Thymeleaf/前后分离 |
| **文件管理服务** | ⭐⭐ | Spring Boot + MinIO/OSS + 分片上传 |

---

## 10. 学习资源推荐

### 书籍

| 书名 | 说明 |
|------|------|
| 《Java 核心技术 卷 I》 | Java 基础圣经，挑重点看，无需通读 |
| 《Effective Java》 | Java 最佳实践，有一定经验后读 |
| 《Spring 实战》第 6 版 | Spring Boot 入门好书 |
| 《深入理解 Java 虚拟机》 | JVM 进阶，面试必备 |
| 《阿里巴巴 Java 开发手册》 | 编码规范，**必看！** |

### 在线教程

| 资源 | 说明 |
|------|------|
| [Baeldung](https://www.baeldung.com/) | 最好的 Java/Spring 教程网站，英文 |
| [廖雪峰 Java 教程](https://www.liaoxuefeng.com/wiki/1252599548343744) | 中文入门首选 |
| [Spring 官方文档](https://spring.io/guides) | 官方 Guides 很友好 |
| [MyBatis-Plus 官方文档](https://baomidou.com/) | 中文文档质量高 |
| [Hutool 工具类库](https://hutool.cn/) | Java 界的 lodash |
| [若依 RuoYi-Vue](https://gitee.com/y_project/RuoYi-Vue) | 知名开源后台管理系统 |

### 视频

| 资源 | 说明 |
|------|------|
| B 站「尚硅谷」Spring Boot 教程 | 免费全套 |
| B 站「黑马程序员」Java 路线 | 体系完整 |

---

## 附录：每周学习节奏建议

```
周一~周五：每天 1~2 小时学习视频/文档 + 写代码
周六：4~6 小时集中实战项目
周日：复习 + 笔记整理 + 休息
```

### 里程碑检查点

- [ ] **第 4 周**：能用 Java 写命令行工具，理解 OOP 四大特性
- [ ] **第 8 周**：能用 MyBatis 操作数据库，理解事务
- [ ] **第 14 周**：能用 Spring Boot 搭建 RESTful API，有完整 CRUD
- [ ] **第 18 周**：能集成 Security + JWT，实现登录鉴权
- [ ] **第 22 周**：能 Docker 部署应用到服务器
- [ ] **第 26 周**：理解微服务架构，能拆分简单服务

---

> 💡 **核心建议**：不要试图看完所有东西再动手。每学完一个小节就立刻写代码。前端转 Java 的最大优势是你已经懂编程思维了，缺的只是语法习惯和生态熟悉度。**写完第一个 Spring Boot 项目，后面的路就顺了。**

*生成于 2026-07-13 · 为你量身定制 · 持续更新中*
