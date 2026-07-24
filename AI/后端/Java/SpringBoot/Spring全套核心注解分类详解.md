按使用场景分为 6 大类：

- 组件注册注解（把类交给 Spring 容器管理）
- 配置类相关注解（@Configuration / @Bean 等）
- 依赖注入 / 自动装配注解（@Autowired、@Resource、@Value）
- AOP 切面注解
- 事务相关注解
- Web / SpringMVC 注解

## 一、组件注册注解（标记类，自动创建 Bean）

1. @Component

   - 通用组件注解，所有交给 Spring 管理的类都可以使用，其他注解都是它的派生

   - ```java
     @Component
     public class CommonUtil {}
     ```

2. @Service（业务层专用）

   - 派生自 `@Component`，语义化，写在 Service 业务类上

   - ```java
     @Service
     public class OrderService {}
     ```

3. @Repository（持久层Mappe/DAO专用）

   - 派生自 `@Component`

   - 作用：

     - 语义区分 DAO 层
     - 数据库异常自动转为 Spring 统一 `DataAccessException`

   - ```java
     @Repository
     public interface OrderMapper {}
     ```

4. @Controller（普通控制器）

   - 派生自 `@Component`，用于 MVC 控制器，接收前端请求，返回页面

   - ```java
     @Controller
     public class PageController {}
     ```

5. @RestController（前后端分离接口控制器）

   - 组合注解：`@Controller + @ResponseBody`

   - 接口返回值直接转为 JSON，不跳转页面

   - ```java
     @RestController
     @RequestMapping("/user")
     public class UserController {}
     ```



## 二、配置类核心注解（@Configuration、@Bean、@Primary 等）

1. @Configuration

   - 标记当前类为**配置类**，替代 xml 配置，内部`@Bean`方法会被 CGLIB 代理，调用方法直接取容器单例。

   - ```java
     @Configuration
     public class DataSourceConfig {}
     ```

2. @Bean

   - 写在**方法上**，将方法返回对象注册为 Spring Bean

   - 适用场景：第三方类（Druid、Mybatis 动态数据源）无法加 @Component，只能用 @Bean 创建

   - 默认 bean 名称 = 方法名;`@Bean("customName")` 自定义 bean 名称

   - ```java
     @Bean("master")
     public DataSource masterDataSource(){
         return new DruidDataSource();
     }
     ```

3. @Primary

   - 同一个接口存在多个实现类 / 多个同类型 Bean 时，**优先被自动注入**，多数据源场景必备

   - ```java
     @Bean
     @Primary
     public DataSource dynamicDataSource(){
         return new DynamicDataSource();
     }
     ```

4. @Scope

   - 指定 Bean 的作用域，常用取值：

     - `singleton`（默认）：全局单例，容器仅创建一次
     - `prototype`：每次注入 / 获取都会新建对象
     - `request`：web 项目，每次 http 请求一个实例
     - `session`：web 项目，每个用户 session 一个实例

   - ```java
     @Bean
     @Scope("prototype")
     public User getUser(){
         return new User();
     }
     ```

5. @Lazy

   - 懒加载：容器启动时不实例化 Bean，**第一次使用时才创建**

   - ```java
     @Bean
     @Lazy
     public BigDataUtil util(){}
     ```





## 三、依赖注入 / 自动装配注解

1. @Autowired（Spring 官方推荐）

   - 自动根据**类型**匹配 Bean 完成注入

   - 可以写在成员变量、构造方法、set 方法上

   - 匹配不到 Bean 抛异常；`@Autowired(required = false)` 找不到不报错

   - ```java
     @Service
     public class OrderService {
         // 根据类型OrderMapper自动注入
         @Autowired
         private OrderMapper orderMapper;
     }
     ```

2. @Qualifier

   - 配合`@Autowired`使用，**同类型多个 Bean 时，通过 Bean 名称精准匹配**

   - ```java
     @Autowired
     @Qualifier("slave")
     private DataSource dataSource;
     ```

3. @Resource（JSR 标准，Java 原生）

   - 优先**按名称**匹配，名称匹配不到再按类型

   - 不需要搭配 Qualifier，`@Resource(name = "xxx")` 直接指定名称

   - ```java
     @Resource(name = "master")
     private DataSource dataSource;
     ```

4. @Value

   - 读取配置文件（application.yml/application.properties）中的值，注入变量

     - 普通字符串：`@Value("${spring.datasource.master.url}")`
     - 固定常量：`@Value("100")`

   - ```java
     @Component
     public class ConfigUtil {
         @Value("${server.port}")
         private Integer port;
     }
     ```

5. @ConfigurationProperties

   - 批量绑定配置文件前缀下的所有属性，搭配`@Component`或`@EnableConfigurationProperties`使用，适合封装配置实体

   - ```yaml
     # yml
     thread:
       core: 10
       max: 50
     ```

   - ```java
     @Component
     @ConfigurationProperties(prefix = "thread")
     public class ThreadPoolConfig {
         private Integer core;
         private Integer max;
         // getter setter
     }
     ```





## 四、AOP 切面全套注解

1. @Aspect

   - 标记当前类为**切面类**，专门存放切点、通知逻辑

   - ```java
     @Aspect
     @Component
     public class DataSourceAspect {}
     ```

2. @Pointcut

   - 定义切点表达式，匹配需要拦截的方法

   - 常用表达式：`execution(* com.xxx.service.*.*(..))`

   - ```java
     @Pointcut("@annotation(com.xxx.annotation.DataSource)")
     public void dataSourcePoint(){}
     ```

3. 通知注解（切面执行时机）

   - `@Before`：目标方法**执行之前**执行

   - `@After`：目标方法**执行完毕后**执行（无论是否异常）

   - `@AfterReturning`：方法**正常返回**后执行（可获取返回值）

   - `@AfterThrowing`：方法**抛出异常**时执行

   - `@Around`：环绕通知，包裹目标方法，可控制方法是否执行、修改入参 / 返回值（功能最强）

   - ```java
     @Before("dataSourcePoint()")
     public void before(JoinPoint point){}
     
     @After("dataSourcePoint()")
     public void after(){}
     ```





## 五、事务管理注解

1. @Transactional（声明式事务）

   - 写在类 / 方法上，开启事务管理：

     - 写在类：类中所有 public 方法都开启事务
     - 写在方法：仅当前方法生效

   - 常用属性：

     - `propagation`：事务传播行为（REQUIRED、REQUIRES_NEW 等）
     - `isolation`：事务隔离级别
     - `rollbackFor`：指定出现什么异常回滚，例rollbackFor = Exception.class
     - `readOnly = true`：只读事务，查询接口优化性能

   - ```java
     @Service
     public class OrderService {
         @Transactional(rollbackFor = Exception.class)
         public void createOrder(){}
     }
     ```

2. @EnableTransactionManagement

   - 开启 Spring 事务管理功能，写在启动类 / 配置类。

   - ```java
     @SpringBootApplication
     @EnableTransactionManagement
     public class Application {}
     ```





## 六、SpringMVC / Web 注解

1. @RequestMapping

   - 通用请求映射，标记类 / 方法，指定访问路径、请求方式

   - 属性：`value`路径、`method`请求方式（RequestMethod.GET/POST）

   - ```java
     @RestController
     @RequestMapping("/order")
     public class OrderController {
         @RequestMapping("/list")
         public List<Order> list(){}
     }
     ```

2. 派生请求注解（简化 @RequestMapping）

   - `@GetMapping` = @RequestMapping(method = GET)

   - `@PostMapping` = @RequestMapping(method = POST)

   - `@PutMapping` = PUT 修改

   - `@DeleteMapping` = DELETE 删除

   - ```java
     @PostMapping("/add")
     public AjaxResult add(){}
     ```

3. @ResponseBody

   - 将方法返回值直接序列化为 JSON 返回前端，不跳转页面；`@RestController`内置此注解

4. @RequestBody

   - 接收前端**JSON 请求体**，将 json 自动转为实体类，POST 接口专用

   - ```java
     @PostMapping("/add")
     public AjaxResult add(@RequestBody OrderDTO dto){}
     ```

5. @RequestParam

   - 接收普通表单参数、url 拼接参数（?id=1）；

   - ```java
     @GetMapping("/detail")
     public Order detail(@RequestParam Long id){}
     ```

6. @PathVariable

   - 接收路径变量，如 `/order/{id}` 中的 id

   - ```java
     @GetMapping("/{id}")
     public Order detail(@PathVariable Long id){}
     ```





## 七、SpringBoot 启动 / 开关注解

1. @SpringBootApplication

   - SpringBoot 启动类核心组合注解，等价于三个注解合并

   - ```java
     @SpringBootApplication
     public class RuoYiApplication {}
     ```

2. @ComponentScan

   - 自动扫描指定包下带 @Component/@Service/@Controller 的类，注册为 Bean
   - 启动类默认扫描当前包及所有子包

3. @EnableAutoConfiguration

   - 开启 SpringBoot 自动装配，根据项目引入的依赖自动创建对应的 Bean（如 Mybatis、Tomcat、Redis）

4. @EnableWebMvc

   - 全面接管 SpringMVC 配置，关闭 SpringBootWeb 自动配置，自定义拦截器、视图解析器时使用





## 八、补充高频实用注解

1. `@NonNull`：参数 / 变量非空校验

2. `@Slf4j`（Lombok）：自动生成日志对象 log

3. `@Data`（Lombok）：自动生成 get/set/toString/equals/hashCode

4. `@PreAuthorize`（SpringSecurity）：接口权限校验

   - ```java
     @PreAuthorize("@ss.hasPermi('system:user:list')")
     @GetMapping("/list")
     public TableDataInfo list(){}
     ```

   - 

