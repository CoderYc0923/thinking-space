## SpringBoot启动到接收HTTP请求完整全流程

## 一、启动流程

1. 启动入口，@SpringBootApplication标注的Main类
2. @SpringBootApplication复合注解是@Configuration @EnableAutoConfiguration @ComponentScan的组合
   - @Configuration：标识当前类为配置类，可以被@Bean注册Bean
   - @EnableAutoConfiguration：自动扫描当前包以及其子包下@Component/@Controller/@Service/@Repository
   - @ComponentScan：开启自动装配，导入AutoConfigurationImportSelector，读取META-INF/spring.factories自动配置类
3. new SpringApplication() 实例构建
   - 记录主启动类 primarySources
   - 推断应用类型：WebApplicationType
     - SERVLET：存在DispatcherServlet -> 传统Tomcat web 应用
     - REACTIVE：WebFlux响应式
     - NONE：普通JAVA程序，不启动web容器
   - 加载ApplicationContextInitalizer初始化器(spring.factories)
   - 加载ApplicationListener事件监听器(spring.factories)
   - 推断main方法所在类
4. SpringApplication.run方法启动
   - prepareEnvironment 准备环境
     - 加载配置：application.yml/application.properties 、系统环境变量、JVM参数、命令行参数
     - ApplicationEnvironmentPreparedEvent 构建 Environment
     - `@ConfigurationProperties`配置绑定基础
   - createApplicationContext 创建容器
     - web servlet类型创建：AnnotationConfigServletWebServerApplicationContext
     - 非web：AnnotationConfigApplicationContext
   - prepareContext 准备上下文，注册启动类为配置类
     - 将Environment注入容器
     - 执行所有ApplicationContextInitializer#initialize()
     - 将主启动类作为配置类载入容器
     - 发布ApplicationContextPreparedEvent
   - refreshContext(context) -> 调用AbstractApplicationContext.refresh() 执行 IoC 容器刷新 `refresh()`【核心】
     - 准备刷新
     - `obtainFreshBeanFactory`：创建 BeanFactory（DefaultListableBeanFactory）
     - invokeBeanFactoryPostProcessors:
       - `ConfigurationClassPostProcessor` 解析配置类、`@ComponentScan`包扫描、`@EnableAutoConfiguration`
       - 自动装配：读取`META-INF/spring.factories`加载自动配置类，条件注解`@Conditional`按需创建 Bean
     - `registerBeanPostProcessors`：注册 Bean 后置处理器；`AutowiredAnnotationBeanPostProcessor`提供`@Autowired`注入
     - **onRefresh ()【SpringBoot 扩展点】**：启动内置 Tomcat 容器
     - `finishBeanFactoryInitialization`：实例化所有非懒加载单例 Bean
       - 完成 Service、Controller、Mapper 代理对象创建；执行`@PostConstruct`初始化方法
5. 容器刷新完成，Tomcat 启动监听端口
   - 执行 `ApplicationRunner / CommandLineRunner`（项目启动后执行自定义逻辑）
   - 发布 `ApplicationReadyEvent` → 项目正式就绪，可以接收请求

## 二、请求处理流程

1. 整体链路

   - 浏览器 → Tomcat → Filter 过滤器链 → DispatcherServlet → SpringMVC 调度 → 业务代码 → 结果序列化 → 响应返回

2. Tomcat 接收 Socket 请求

   - Tomcat 的 NIO 线程处理 TCP 连接，封装 HttpServletRequest、HttpServletResponse 对象，转发给 Spring 注册的`DispatcherServlet`
     - DispatcherServlet 由`DispatcherServletAutoConfiguration`自动配置注册

3. 执行 Filter 过滤器链（Servlet 规范，Tomcat 层）

   - `@WebFilter` / Spring 中`OncePerRequestFilter`，例如 CORS 跨域过滤器、登录拦截过滤器

     过滤器执行完毕，请求进入 DispatcherServlet#doDispatch ()

4. DispatcherServlet.doDispatch () 核心调度

   - ```sql
     //1. HandlerMapping 根据URL匹配Controller方法，生成HandlerExecutionChain（handler + Interceptor拦截器）
     HandlerExecutionChain mappedHandler = getHandler(request);
     //2. 获取适配器 RequestMappingHandlerAdapter
     HandlerAdapter ha = getHandlerAdapter(mappedHandler.getHandler());
     //3. 拦截器 preHandle()，返回false直接终止请求
     if (!mappedHandler.applyPreHandle(request, response)) return;
     
     // ===================== 核心分界线 =====================
     // ha.handle() 内部包含：参数解析 → 执行业务代码 → 返回值处理
     ModelAndView mv = ha.handle(request, response, mappedHandler.getHandler());
     // =====================================================
     
     //4. 拦截器 postHandle()（Controller执行完，结果渲染前）
     mappedHandler.applyPostHandle(request, response, mv);
     //5. 处理异常、视图渲染、最终输出响应
     processDispatchResult();
     ```

   - 参数解析阶段【框架代码，还没进入 Controller 方法】

     - `HandlerMethodArgumentResolver`参数解析器工作
     - `@RequestBody`：读取请求体 JSON → 反序列化为 **入参 DTO**
     - `@RequestParam / @PathVariable` 解析普通参数
     - 参数带有`@Valid`：**此处触发 JSR303 参数校验**
     - 校验失败直接抛出异常，不会进入 Controller 方法，由`@ControllerAdvice`全局异常捕获

   - 反射调用 Controller 方法【正式进入你编写的业务代码】

     - ```java
       @PostMapping("/user/add")
       public Result<UserVO> addUser(@Valid @RequestBody UserDTO dto){
           // 业务代码起点
           // 1. 调用Service
           UserEntity entity = userService.createUser(dto);
           // 2. 数据库实体Entity → 对外VO转换
           UserVO vo = convert(entity);
           return Result.success(vo);
       }
       ```

     - Controller → Service

       - Service 是 IoC 中的 Bean；如果方法标注`@Transactional`，Service 是 AOP 代理对象
       - 调用时 AOP 拦截：开启事务、业务异常回滚、正常执行提交事务
       - ⚠️ Service 内部 this 调用本类方法，会绕过 AOP，事务失效

     -  Service → Mapper（MyBatis）

       - `@MapperScan`生成 Mapper 动态代理对象
       - mapper 方法调用底层：SqlSession → Executor → JDBC 执行 SQL
       - 查询结果集 ResultSet，由 MyBatis 自动映射 → **Entity 数据库实体**
       - Entity 返回 Service，逐层向上传递到 Controller

     -  Entity 转换 VO

       - Controller / 转换层完成内部实体 Entity → 前端出参 VO 封装
       - 规范：禁止直接返回 Entity，防止敏感字段外泄

     - 支持的核心注解：

       - `@RequestParam`：普通请求参数
       - `@PathVariable`：路径变量 `/user/{id}`
       - `@RequestBody`：读取请求体 JSON，依靠 **MappingJackson2HttpMessageConverter**
       - `@RequestHeader`：获取请求头
       - `@CookieValue`：获取 Cookie
       - `@Valid` / `@NotBlank`：参数校验

   - Controller 方法执行完毕，退出业务代码，回到框架层

     - 拿到方法返回值（VO）

   -  返回值处理阶段【框架代码】

     - HandlerMethodReturnValueHandler
     - 存在`@ResponseBody`（`@RestController`复合注解自带）
     - 使用`MappingJackson2HttpMessageConverter`，将 VO 对象序列化为 JSON 字符串，写入 response 输出流

   - 后续流程

     - 执行拦截器`postHandle()`
     - `processDispatchResult`：统一处理异常（`@ExceptionHandler`全局异常处理器生效）
     - 响应数据原路返回：DispatcherServlet → Filter → Tomcat → 浏览器



完整时许流程图

```java
【启动阶段】
main() → SpringApplication.run()
→ 准备环境Environment
→ 创建ApplicationContext容器
→ refresh()刷新IoC容器
    → 扫描Bean、自动配置加载
    → Bean实例化、依赖注入
    → onRefresh()启动内置Tomcat
→ 启动完成，就绪等待请求

【请求阶段】
HTTP请求
→ Tomcat
→ Filter链
→ DispatcherServlet#doDispatch
    → HandlerMapping匹配URL找到Controller方法
    → RequestMappingHandlerAdapter
        1. 参数解析器：JSON→DTO，@Valid校验
        2. 反射调用Controller【业务代码开始】
            Controller(DTO) → Service(@Transactional AOP)
            → Mapper(MyBatis执行SQL) → ResultSet映射Entity
            → Entity转为VO 【业务代码结束】
        3. 返回值处理器：VO → JSON（HttpMessageConverter）
    → Interceptor拦截器postHandle
→ 响应输出 → 客户端
```





## 三、配套核心注解归类

1. 启动 / IoC 相关
   - @SpringBootApplication
   - @Configuration
   - @ComponentScan
   - @EnableAutoConfiguration
   - @Bean
   - @Service/@Controller/@Repository/@Component
   - @Autowired
   - @Value
   - @ConfigurationProperties
   - @PostConstruct
   - @Transactional
2. SpringMVC Web 注解
   - @RestController
   - @RequestMapping/@GetMapping
   - @RequestBody
   - @RequestParam
   - @PathVariable
   - @Valid
   - @ControllerAdvice
   - @ExceptionHandler



## 四、高频易混考点总结

1. DTO 参数校验：**进入 Controller 之前**，框架层抛出异常，Controller 内部 try-catch 抓不到
2. `@Transactional`生效时机：调用 Service 代理方法时，业务代码执行区间
3. Entity 由 MyBatis 在 Mapper 调用过程中生成，属于业务代码内部
4. VO 序列化为 JSON：Controller 执行完成之后，框架层处理，不在业务代码中
5. Interceptor 在 DispatcherServlet 内部；Filter 在 Tomcat 层面，早于 DispatcherServlet



