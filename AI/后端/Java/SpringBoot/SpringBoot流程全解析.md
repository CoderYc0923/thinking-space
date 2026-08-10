## SpringBoot 完整宏观生命周期

核心原则：**SpringBoot 本质 = main 方法驱动，创建 Spring IOC 容器，容器走完一套完整生命周期，最后启动 web 服务器。所有注解 (@Service/@Configuration/@Bean/@Transactional) 全部都是生命周期各个阶段被解析执行。**

> IOC：**Inversion of Control，控制反转**
>
> **指对象的创建、依赖装配、生命周期（创建、初始化、销毁）的控制权从业务代码反转交给 Spring IOC 容器（ApplicationContext）**
>
> **把对象的生老病死全部交给容器管，业务代码不负责 new 对象**

阶段拆解：**启动 main → 准备环境 → 扫描解析 Bean 定义 → 实例化 Bean → 依赖注入 DI → Bean 初始化 → AOP 代理替换原始对象 → 容器就绪 (Tomcat 启动) → 运行接收请求 → 程序关闭销毁 Bean**

```java
1. 程序入口 main() 执行 SpringApplication.run();
	↓
2. 准备运行环境：加载配置文件application.yml、环境变量、系统属性;
	↓
3. 扫描解析，生成【Bean定义信息 BeanDefinition】（**还没有创建对象！！只是元数据**）;
	BeanDefinition：描述这个 Bean 的说明书，保存类名、注解信息、作用域、是否单例，此时没有 new 出任何对象。
	↓
4. IOC容器开始实例化Bean（反射new对象，半成品对象）;
	↓
👉实例化完成，立刻往三级缓存存入ObjectFactory
	↓
5. DI依赖注入：给半成品Bean填充依赖属性;
	↓
👉DI过程中遇到循环依赖，触发三级缓存工厂执行，对象提升到二级缓存
	↓
6. Bean初始化阶段（@PostConstruct、InitializingBean、@Bean(initMethod)）;
	↓
7. AOP判断：如果匹配切面切点 → 创建代理对象，**用代理对象替换掉原始Bean存入容器** （循环依赖场景代理可能已经提前生成）;
	↓
8. 全部Bean处理完毕，容器完成刷新 refresh()完成; 移入一级缓存，清空二三级缓存
	↓
9. 启动内置Tomcat/Web服务器，对外提供http服务，容器进入运行期;
	↓
👉【运行时：接收前端http请求，从容器拿Bean执行业务代码】;
	↓
10.程序关闭，容器关闭，执行销毁方法，释放资源;
    
```

> ✨学习方法：以后每写一行注解，就在脑子里定位它属于生命周期哪一步。
>
> 比如写一个`@Service`：哦，阶段 3 被扫描生成 BeanDefinition；阶段 4 反射 new 对象；阶段 5 注入依赖；阶段 6 执行PostConstruct；阶段 7 看是否被 AOP 代理；存入 IOC 容器，请求来的时候拿出来用。



### SpringBoot Bean 的创建方式、区别 + 业务代码示例

> 业务开发日常绝大多数 Bean 来源于两大类：
>
> 1. **@Component 体系（类上注解，由 @ComponentScan 扫描）**
> 2. **@Bean 方法（配置类内方法，手动 new 返回对象）**
>
> 除此之外还有**框架扩展方式**（编程注册，MyBatis Mapper 就是典型），业务编码几乎不手写，了解即可。

1. @Component 体系（类注解方式）

   - `@Component`（根注解）、`@Service`、`@Repository`、`@Controller`、@RestController

     - `@Service / @Repository / @Controller` 都是`@Component`的派生元注解
     - 本质：`@ComponentScan`扫描到该类 → 生成`BeanDefinition` → Spring 通过**反射调用构造方法创建对象**
     - 对象是 Spring 帮你 new，**我们不写 new**

   - ```java
     @Component
     public @interface Service {}
     
     @Component
     public @interface Repository {}
     ```

   - 特点：

     - 注解打在**类上面**

     - 对象实例化：Spring 反射调用构造器

     - 触发：`@ComponentScan`扫描包

     - Bean 名称默认：类名首字母小写

       

2. @Bean 方式（方法级别注册 Bean）

   - 写在**`@Configuration`配置类的方法上**

   - 对象是**我们自己手动 new，return 给 Spring**

   - Spring 解析配置类，读取`@Bean`方法元信息生成`BeanDefinition`，后续调用该方法拿到对象注册为 Bean

   - 适合：**第三方 Jar 包的类，我们不能修改源码，无法在类上加 @Component**

   - ```java
     // 示例 1：注册第三方组件 RedisTemplate
     // RedisTemplate 来自 spring-data-redis jar，源码不能修改，不能加 @Component
     @Configuration // @Configuration本身也是@Component派生注解，会被扫描
     public class RedisConfig {
     
         // @Bean：把方法返回对象注册为IOC Bean
         @Bean
         public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory factory) {
             RedisTemplate<String, Object> template = new RedisTemplate<>();
             template.setConnectionFactory(factory);
             // 可以在这里做大量自定义属性设置
             return template;
         }
     }
     
     
     // 示例 2：自己项目的类，也可以用 @Bean 注册（不推荐，没必要）
     // 自己写的类优先用 @Service/@Component；只有需要复杂构建逻辑时才考虑 @Bean
     @Configuration
     public class AppConfig {
         @Bean
         public UserService userService(){
             UserService userService = new UserService();
             // 可以在这里手动设置一些属性
             return userService;
         }
     }
     ```

     > ⚠️重要提醒：
     >
     > `@Bean`写在普通类（不加 @Configuration）会进入 lite 模式，没有 CGLIB 增强，多次调用该方法会创建多个实例，破坏单例。
     >
     > 所以业务代码中，`@Bean`尽量写在`@Configuration`类内部。

   | 对比项              | @Component 及其派生注解            | @Bean                                     |
   | ------------------- | ---------------------------------- | ----------------------------------------- |
   | 标注位置            | **类上面**                         | **方法上面（@Configuration 类内）**       |
   | 对象由谁 new        | Spring 容器反射创建                | **开发者手动 new，return 返回**           |
   | 触发来源            | @ComponentScan 包扫描              | 解析配置类，执行 @Bean 方法               |
   | 适用场景            | 自己项目源码，可以修改类，业务分层 | 第三方 jar 类、复杂对象构建，无法修改源码 |
   | BeanDefinition 生成 | 扫描 class 自动生成                | 解析方法元信息生成                        |

   > 两者最终效果完全一致：都会产出 Bean 放入 IOC 容器，可以被 @Autowired 注入、参与完整生命周期、可以被 AOP 代理

3. 框架扩展：编程式注册 Bean（业务几乎不手写，了解概念）

   > 既没有 @Component，也没有 @Bean。
   >
   > 通过 Spring 扩展接口，手动构造`BeanDefinition`注册进注册表
   >
   > 典型代表：**MyBatis @MapperScan**
   >
   > Mapper 接口没有任何注解，MyBatis 扫描 Mapper 接口，动态生成 BeanDefinition 注册到 IOC 容器

   ```java
   // 伪代码示意（仅理解逻辑，不要复制写业务）
   // ImportBeanDefinitionRegistrar，框架底层扩展点
   public class MyMapperRegistrar implements ImportBeanDefinitionRegistrar {
       @Override
       public void registerBeanDefinitions(AnnotationMetadata metadata, BeanDefinitionRegistry registry) {
           // 手动构建BeanDefinition，注册Mapper代理Bean
           registry.registerBeanDefinition("userMapper", beanDefinition);
       }
   }
   ```

   



## 总结：

1. **启动的时候，先收集全部 Bean 说明书 BeanDefinition，之后才批量创建对象，不是扫描一个就 new 一个**
2. IOC = 整个这套生命周期容器；DI 只是生命周期中的其中一步（填充依赖）；AOP 是 Bean 初始化之后，替换代理对象。三者不是并列简单概念，是生命周期不同环节。
3. `@Service/@Configuration`只是标记元数据；**真正干活是 Spring 在生命周期各个阶段解析这些标记。注解本身不会执行任何逻辑**
4. 我们开发写代码，本质就是给 Spring 容器写各种 “说明书”，告诉容器：要创建什么对象，依赖什么，要做什么增强，什么时候初始化、销毁。



## 阶段 1：入口 main 执行 SpringApplication.run ()

**做什么**：整个 SpringBoot 程序的起点

```java
@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        // 一切从这里开始
        SpringApplication.run(MyApplication.class, args);
    }
}
```

- `@SpringBootApplication` 是组合注解，包含三个：
  1. `@Configuration`：当前启动类本身也是一个配置 Bean
  2. `@EnableAutoConfiguration`：开启 SpringBoot 自动配置（SpringBoot 核心能力） 导入第三方自动配置类 ([见Spring全套核心注解分类详解](./Spring全套核心注解分类详解.md))
  3. `@ComponentScan`：**组件扫描，指定扫描包，默认扫描当前启动类所在包及其子包**
- 业务场景坑：
  1. 你的 service、mapper 放在启动类包外面，`@ComponentScan`扫不到，后续不会生成 BeanDefinition，直接报`NoSuchBeanDefinitionException`。
- 当前阶段：**还没有 IOC 容器对象，仅仅是初始化运行上下文**

此阶段常用注解

1. @SpringBootApplication
   - 标记启动类，开启扫描、自动配置





## 阶段 2：准备运行环境

**做什么**：把外部配置全部加载进来。

Spring 动作：

- 加载 `application.yml / application.properties`
- 读取操作系统环境变量、jvm 启动参数
- 处理 profile 环境（dev/test/prod）

```yaml
# application.yml
server.port=8080
spring.datasource.url=xxx
```

此时：**还没有创建任何业务 Bean 对象，只是把配置数据放到环境对象 Environment 中保存，后面创建 Bean 的时候会读取这些配置**。





## 阶段 3：扫描解析，生成 BeanDefinition（重点！只有说明书，没有实例）

> 📌 本阶段**不会 new 任何对象**！只是收集 “要创建哪些对象” 的元数据说明书 BeanDefinition。

Spring 动作：

- `@ComponentScan`开始扫描包路径下所有 class
- 识别带有 `@Component/@Service/@Repository/@Controller` 的类；每识别一个类，就生成一份 BeanDefinition；
- 解析所有被`@Configuration`标记的配置类；
- 遍历配置类内部所有 `@Bean` 方法，**也生成 BeanDefinition**

示例业务代码 1：业务 Service

```java
// @Service 是 @Component 的派生注解，这里被扫描到 → 生成BeanDefinition说明书
@Service
public class UserService {
    private UserMapper userMapper;
}
```

示例业务代码 2：配置类 @Configuration + @Bean

```java
@Configuration
public class ThirdPartyConfig {
    // 这个方法上的@Bean，会被解析生成BeanDefinition
    @Bean
    public RedisUtil redisUtil(){
        // 这里代码现在**不会执行！！只是记录一份说明书**
        return new RedisUtil();
    }
}
```

⚠️重要误区：`@Bean`修饰的`redisUtil()`方法，**阶段 3 不会执行**！只是记录：后续实例化这个 Bean 的时候，调用这个方法拿到对象

本阶段产出：一堆 BeanDefinition 说明书，存放在容器中，记录所有需要交给 Spring 管理的类

此阶段常用注解：

1. @ComponentScan
   - 扫描包，收集 BeanDefinition 说明书
2. @Service/@Component/@Repository
   - 被扫描，生成 BeanDefinition
3. @Configuration
   - 标记配置类，解析内部 @Bean 方法，CGLIB 增强配置类
4. @Bean
   - 注册第三方组件 Bean
   - 此阶段生成 BeanDefinition





## 阶段 4：实例化 Bean —— 根据 BeanDefinition，反射 new 出半成品对象

Spring 动作：

- 读取 BeanDefinition 说明书，利用 Java 反射机制，调用类构造方法，new 出来原始 Java 对象
- 此时对象仅仅完成构造，**内部成员变量全部是 null，半成品，依赖还没有赋值**

```java
@Service
public class UserService {
    private UserMapper userMapper; // 此时还是null！！

    // 构造方法被反射调用 new UserService()
    public UserService(UserMapper userMapper){
        this.userMapper = userMapper;
    }
}
```

- 如果是构造器注入：实例化阶段就会尝试去找依赖，直接进入 DI。
- 如果是字段注入：new 完对象，userMapper=null，等到阶段 5 再赋值
- 注意：这里 new 出来是原生对象，还不是代理对象，AOP 还没上场。

此阶段常用注解：

1. @Bean
   - 注册第三方组件 Bean
   - 调用方法 new 对象



## 循环依赖 & 三级缓存

> 发生位置：Bean 生命周期 **阶段 4【实例化】结束，阶段 5【DI 依赖注入】开始的间隙**
>
> 场景：两个 Bean 互相依赖，A 要 B、B 要 A。
>
> 前提：只针对**单例 Bean**；**原型 (prototype) 不支持循环依赖**，直接抛异常。

```java
@Service
public class AService {
    private final BService bService;
    // 构造器注入
    public AService(BService bService) {
        this.bService = bService;
    }
}

@Service
public class BService {
    private final AService aService;
    public BService(AService aService) {
        this.aService = aService;
    }
}
```

1. 会出现什么问题

   - 阶段 4：反射 new 出 Bean 原始对象（半成品，成员变量全部 null）
   - 紧接着进入阶段 5：给半成品做 DI 填充依赖。
   - 当两个**单例 Bean 互相依赖**（A 需要 B，B 又需要 A），就出现**循环依赖问题**：
     - 实例化 A → new 出半成品 A；
     - DI 给 A 赋值，发现 A 依赖 B，去创建 B；
     - 实例化 B → new 出半成品 B；
     - DI 给 B 赋值，B 又依赖 A；
     - 此时 A 仅仅只是 new 出来，**DI、初始化、AOP 代理全部没做完，还没进入最终单例池**；B 拿不到 A，程序直接报错
   - 核心矛盾：**对象已经 new 出来有引用，但对象还不完整，不能对外作为成熟 Bean 使用；可是另一个 Bean 现在就必须拿到这个对象引用才能完成自己的 DI。**

2. 为了解决这个矛盾，Spring 设计了三级缓存，三个缓存都是 Map，各司其职

   - **一级缓存 singletonObjects**：存放完全就绪的单例 Bean（实例化 + DI + 初始化 + 代理全部完成），对外正常获取 Bean 的池子。

   - **二级缓存 earlySingletonObjects**：存放实例化完成，但还没完成 DI 的对象（原始 / 已经生成好的代理对象）。作用：避免重复执行代理逻辑。

   - **三级缓存 singletonFactories**：存对象工厂`ObjectFactory`，**延迟生成代理**。只有别的 Bean 需要该对象引用时，才执行工厂判断是否创建代理。

     > 关键：三级缓存不存对象，存的是一个回调函数。目的：没人需要引用就不提前生成代理，节约开销。

3. 完整执行流程（A 依赖 B，B 依赖 A，字段 /@Autowired 注入）

   - 阶段 4 实例化 A，new 得到半成品原始 A 对象。

   - A 实例化完毕，立刻把 A 的代理工厂放入**三级缓存**。此时一、二级缓存没有 A。

   - 进入阶段 5 DI，A 需要 B，容器没有 B，触发创建 B。

   - 阶段 4 实例化 B，new 得到半成品原始 B 对象。

   - B 实例化完毕，把 B 的代理工厂放入**三级缓存**。

   - 进入阶段 5 DI，B 需要 A；去容器查找 A：

     - 一级缓存：没有 A；
     - 二级缓存：没有 A；
     - 执行**三级缓存的 A 工厂**：判断 A 是否需要 AOP 代理，需要则生成代理对象，不需要返回原始对象
     - 将得到的对象放入**二级缓存**，删除三级缓存里 A 的工厂

   - B 拿到对象引用，B 完成 DI 填充

   - B 走完初始化、AOP 代理，B 变成完整 Bean，移入**一级缓存**，清理二三级缓存 B 的数据

   - 回到 A 的 DI 流程，拿到完整 B，A 完成 DI

   - A 走完初始化、AOP 代理，A 变成完整 Bean，移入**一级缓存**，清理二三级缓存 A 的数据

     > 特殊点：
     >
     > 正常流程 AOP 代理在【阶段 7】生成；**循环依赖场景，如果被别的 Bean 提前引用，代理会在三级缓存工厂提前生成，不再等到阶段 7**。

4. 三级缓存能解决什么，不能解决什么

   - ✅可以解决：**单例 Bean，字段注入 /set 方法注入 的循环依赖**
   - ❌不能解决：
     - **构造器注入循环依赖**：实例化 new 对象的时候构造函数就需要依赖，半成品对象都还没生成，根本没有机会存入三级缓存，直接抛异常。
     - **prototype 多例 Bean**：多例不使用三级缓存，遇到循环依赖直接报错

5. 常见面试小问题：为什么不能只用两级缓存？

   - 如果去掉三级缓存，实例化完直接把对象放入二级缓存，会出现Bean 刚 new 完成，**不管有没有别的 Bean 需要引用，都必须立刻判断并生成代理对象**。三级缓存的工厂实现延迟代理，只有真正被别人依赖的时候，才执行代理创建，减少不必要性能消耗



## 阶段 5：DI 依赖注入，给半成品 Bean 填充依赖（Dependency Injection）

Spring 动作：

- 拿到半成品对象，分析这个 Bean 需要哪些依赖
- 去 IOC 容器查找对应已经实例好的 Bean，赋值

```java
// 方式1：构造器注入（推荐，实例化时直接注入）
@Service
public class UserService {
    private final UserMapper userMapper;
    public UserService(UserMapper userMapper) {
        this.userMapper = userMapper;
    }
}

// 方式2：字段注入（不推荐）
@Service
public class UserService {
    @Autowired
    private UserMapper userMapper; // 阶段5，容器找到UserMapper，给这个变量赋值
}
```

这里抛出经典异常：`UnsatisfiedDependencyException`，含义：Bean 本身可以 new 出来，但是它需要的依赖在容器找不到，DI 填充失败。

完成本阶段之后：Bean 内部所有依赖全部赋值完毕，对象可用，但还没有执行初始化方法。

此阶段常用注解：

1. @Autowired
   - 给 Bean 填充依赖对象





## 阶段 6：Bean 初始化（执行初始化回调逻辑）

DI 完成之后，执行 Bean 的自定义初始化逻辑

三种初始化方式，**执行顺序固定**：

- `@PostConstruct`注解方法
- `InitializingBean#afterPropertiesSet()`接口
- `@Bean(initMethod = "init")`指定初始化方法

```java
@Service
public class UserService {

    @PostConstruct
    public void postConstruct(){
        // DI完成之后执行这里，可以做资源初始化，加载缓存等
        System.out.println("@PostConstruct 执行");
    }
}

@Configuration
public class ThirdPartyConfig {
    @Bean(initMethod = "init")
    public RedisUtil redisUtil(){
        return new RedisUtil();
    }
}
```

场景：**连接池、SDK**，在初始化方法里面建立连接。此时 Bean 已经完整，但是还没做 AOP 代理。

此阶段常用注解：

1. @PostConstruct
   - DI 完成后执行自定义初始化逻辑



## 阶段 7：AOP 切面处理，生成代理对象，替换容器中的原始 Bean（非常关键）

Spring 动作：

- 遍历已经初始化完成的 Bean；
- 判断当前 Bean 是否匹配 AOP 的切点表达式。
  1. 如果**不匹配切点**：保留原始对象，直接存入 IOC 容器 Map；
  2. 如果**匹配切点**：Spring 结合配置参数`proxy‑target‑class`做判断，配置为 true 则直接选用 **CGLIB 代理**；配置为 false 时再根据目标类是否实现接口，有接口使用 **JDK 动态代理**，无接口**降级 CGLIB 代理**，生成代理对象，**把代理对象放进 IOC 容器 Map，原始对象被包装，不再对外暴露**

> 后续 @Autowired 拿到的，是代理对象，不是原生对象

> 两种代理实现细节
>
> 1. JDK 动态代理
>    - 底层：JDK 自带`java.lang.reflect.Proxy`，不需要额外依赖包
>    - 硬性前提：目标类必须实现至少一个接口
>    - 原理：**生成一个实现目标接口的代理类**，代理类和目标类是**实现同一个接口的平级关系，不是继承关系**
>    - 限制：**只能拦截接口中声明的方法；类里面 public 但不在接口中的方法，无法被增强；final 方法无法拦截**
> 2. CGLIB 代理（Code Generation Library）
>    - 底层：动态生成字节码，创建目标类的子类
>    - **硬性前提：目标类不能是 final；要增强的方法不能是 final**（final 不能被重写）
>    - 原理：动态生成**目标类的子类**，代理对象继承目标类，重写非 final 方法；在重写的方法内部植入 AOP 增强逻辑
>    - 不需要实现任何接口，普通业务 Service 没有接口也可以做增强
>
> SpringBoot 的默认选择 & 手动切换配置
>
> 1. SpringBoot2.x 及以上，**AOP 默认使用 CGLIB 代理**（`proxy‑target‑class=true`）
>
> 2. ```yaml
>    # application.yml 配置切换代理模式
>    spring:
>      aop:
>        # true：使用CGLIB代理（默认）
>        # false：优先使用JDK动态代理，要求目标必须实现接口
>        proxy-target-class: true
>    ```
>
> 3. ```java
>    // 定义接口
>    public interface OrderApi {
>        void createOrder();
>    }
>       
>    @Service
>    public class OrderServiceImpl implements OrderApi {
>       
>        @Override
>        @Transactional
>        public void createOrder() {
>            System.out.println("创建订单");
>        }
>    }
>       
>    // 如果配置proxy‑target‑class:false：使用JDK 动态代理，代理对象实现OrderApi接口
>    // 如果配置proxy‑target‑class:true：使用CGLIB 代理，代理对象继承OrderServiceImpl
>    ```
>
> 4. 
>
> 5. | 对比项             | JDK 动态代理             | CGLIB 代理                                       |
>    | ------------------ | ------------------------ | ------------------------------------------------ |
>    | 底层来源           | JDK 原生反射 API         | 动态生成子类字节码                               |
>    | 必要条件           | 目标类**必须实现接口**   | 目标类不能 final，增强方法不能 final，不需要接口 |
>    | 代理与目标关系     | 代理实现目标接口（平级） | 代理继承目标类（父子关系）                       |
>    | SpringBoot2.x 默认 | 不默认                   | ✅默认启用                                        |
>    | 能增强的范围       | 仅接口定义的方法         | 类中所有非 final public/protected 方法           |

​	

```java
@Service
public class OrderService {
    // @Transactional就是AOP切面的标记，会匹配切点
    @Transactional
    public void createOrder(){
        // 业务代码
    }
}
```

- 当这个类被 AOP 切到，IOC 容器中存的不再是原始`OrderService`对象，而是 CGLIB 生成的代理子类对象。
- 调用 createOrder ()，先走代理的环绕通知：**开启事务，执行业务，异常回滚，成功提交**
- 坑：同一个类内部方法调用，`this.xxx()`不走代理，事务失效！因为 this 是原生对象，不是容器里的代理 Bean

👉到此为止：**一个完整可用的 Bean 正式就绪，放入 IOC 容器 Map**。

此阶段常用注解：

1. @Transactional
   - 匹配切点，生成代理对象，实现事务





## 阶段 8：容器刷新完成 refresh () 结束，所有单例 Bean 全部处理完毕

所有单例 Bean：实例化 → DI →初始化→AOP 代理，全部走完。

IOC 容器`ApplicationContext`彻底就绪。





## 阶段 9：启动内置 Tomcat，进入运行期

SpringBoot 启动内置 web 服务器（Tomcat），监听端口。

从这一刻开始接收前端 http 请求。

运行期业务场景：http 请求进来之后发生什么？

- 请求到达 Tomcat；
- SpringMVC 分发，找到对应的`@RestController` Bean（从 IOC 容器 Map 取出代理 Bean）
- 调用 controller 方法，controller 内部注入的 service，同样从容器取出 Bean 执行业务
- 返回响应给前端





## 阶段 10：程序关闭，容器销毁阶段

程序停止（关闭服务）

Spring 执行 Bean 销毁回调，释放资源

销毁三种方式，顺序：

- @PreDestroy
- `DisposableBean#destroy()`接口
- @Bean(destroyMethod = "close")

```java
@Service
public class UserService {
    @PreDestroy
    public void destroy(){
        // 服务关闭的时候执行，关闭连接，释放资源
    }
}
```

此阶段常用注解：

1. @PreDestroy
   - 服务关闭执行资源释放







