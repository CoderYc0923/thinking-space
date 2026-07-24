# 17. 注解 Annotation

1. 本质：

   - 附加在类、方法、变量、参数上的标记（标签），格式@xxx
   - 本身不直接执行业务逻辑，仅给程序提供元数据，在编译期 / 运行时通过反射读取
   - 框架核心（Spring）

2. 作用：

   - 编辑校验：@Override、@Deprecated，编译器检查语法
   - 生成代码：Lombok @Data 编译自动生成get/set
   - 运行时解析：Spring @Controller、@Autowired，框架反射读取注解实现功能

3. 内置基础注解

   - @Override：

     - 标记当前方法是重写父类 / 接口方法；编译器校验签名是否一致，写错直接报错。

   - @Deprecated：

     - 标记类 / 方法 / 字段**已过时**，调用时编译器给出警告。

   - @SuppressWarnings：

     - 压制编译器警告，消除黄色波浪线。

     - `unchecked`：泛型未指定类型警告

     - `rawtypes`：原始类型集合警告

     - `all`：压制所有警告

     - ```java
       @SuppressWarnings("unchecked")
       List list = new ArrayList();
       ```

   - @SafeVarargs (Java7)

     - 消除可变泛型参数的 unchecked 警告。

   - @FunctionalInterface (Java8)

     - 标记函数式接口：接口**只能有一个抽象方法**，配合 Lambda 使用，编译器校验。

     - ```java
       @FunctionalInterface
       pubnlic interface Func {
           void test();
       }
       ```

4. 元注解（修饰注解的注解，自定义注解必学）

   - 元注解用来规定**自定义注解能写在哪、存活到哪个阶段**，共 5 个，常用 4 个：

     - @Target：指定注解能标注的位置（必填）

       - 取值枚举ElementType

         | 枚举值          | 可标注位置     |
         | --------------- | -------------- |
         | TYPE            | 类、接口、枚举 |
         | FIELD           | 成员变量       |
         | METHOD          | 方法           |
         | PARAMETER       | 方法参数       |
         | CONSTRUCTOR     | 构造方法       |
         | LOCAL_VARIABLE  | 局部变量       |
         | ANNOTATION_TYPE | 注解本身       |

         示例

         ```java
         // 注解只能打在方法上
         @Target(ElementType.METHOD)
         public @interface Log {};
         
         
         // 多位置用数组
         @Target({ElementType.METHOD, ElementType.TYPE})
         ```

         

     - @Retention：注解生命周期（必填）

       - 枚举 `RetentionPolicy`，决定注解保留到哪个阶段：

         | 枚举值  | 作用                                                         |
         | ------- | ------------------------------------------------------------ |
         | SOURCE  | 仅源码阶段，编译后丢弃，仅编译器使用（如 @Override）         |
         | CLASS   | 保留到字节码 class 文件，运行时 JVM 丢弃（默认策略）         |
         | RUNTIME | 运行时依旧存在，**可通过反射读取**（Spring、自定义业务注解必用） |

         ```java
         @Retention(RetentionPolicy.RUNTIME)
         ```

     - @Documented

       - 生成 JavaDoc 文档时，把注解一同写入文档，不加则文档不显示注解。

     - @Inherited

       - 注解具备继承性：子类会自动继承父类上的该注解
       - 仅对 `TYPE`（类）生效，方法 / 字段无效

5. 自定义注解完整案例（开发常用）

   - 语法规则

     - 定义关键字

     - 内部定义属性，格式：类型 属性名() default 默认值

     - 特殊：只有一个属性且名字叫value,使用时可省略属性名

       ```java
       //示例：自定义日志注解@Log
       import java.lang.annotation.*;
       
       // 可标注类、方法
       @Target({ElementType.TYPE,ElementType.METHOD})
       // 运行时保留
       @Retention(RetentionPolicy.RUNTIME)
       // 写入文档
       @Documented
       public @interface Log {
           // 操作描述，默认空字符串
           String value() defalut "";
           // 操作类型，默认0
           int type() default 0;
       }
       
       
       
       // 使用
       // 只传value,可省略属性名
       @Log("查询用户列表")
       public List<User> getUserList() {
           return new ArrayList<>();
       }
       
       //多个属性赋值
       @Log(value = "新增用户", type = 1)
       public void addUser(){}
       ```

     - 通过反射读取注解（框架底层原理）

       ```java
       import java.lang.reflect.Method;
       
       public class TestAnnotation {
           public static void main(String[] args) throws Exception {
               Class<?> clazz = UserController.class;
               Method method = clazz.getDeclaredMethod("getUserList");
               
               // 判断方法上是否有@Log注解
               if (Method.isAnnotationPresent(Log.class)) {
                   Log log = method.getAnnotation(Log.class);
                   //获取注解属性
                   String desc = log.value();
                   int type = log.type();
                   System.out.println("操作描述：" + desc);
                   System.out.println("操作类型：" + type);
               }
           }
       }
       ```

6. 注解属性支持的数据类型

   - 自定义注解内部属性只能使用以下类型，不能用自定义对象：

     - 基本类型：byte/short/int/long/float/double/char/boolean
     - String
     - Class<?>
     - 枚举 Enum
     - 注解类型
     - 以上类型的一维数组

   - ```java
     @interface Role {
         String[] roles() default {"user"};
     }
     // 使用
     @Role(roles = {"admin","super"})
     ```

7. 主流框架常用注解（面试高频）

   - Lombok（简化实体类）
     - @Data: 自动生成get/set/toString/equals/hashCode
     - @NoArgsConstructor: 无参构造
     - @AllArgsConstructor:全参构造
     - @Builder: 构建者模式

   - SpringMVC/Web
     - @Controller / @RestController: 标识控制器
     - @RequestMapping / @GetMapping / @PostMapping：接口路由
     - @RequestParam/@RequestBody/@PathVariable: 参数绑定

   - Spring IOC依赖注入
     - @Component/@Service/@Repository: 注册Bean
     - @Autowired: 自动注入对象
     - @Value:读取配置文件值

   - 事务
     - @Transactional：声明式事务

8. 注解核心特点 & 面试题总结

   - 特点
     - 注解本身无业务逻辑，必须配合**编译器 / 反射**才能生效
     - 生命周期由`@Retention`控制，运行时注解才能反射解析
     - 自定义注解不能有方法体，只有属性定义
     - 注解不影响程序原有执行流程，属于增强型元数据

   - 高频面试简答
     - 元注解有哪些？各自作用？
       - `@Target`（标注位置）、`@Retention`（生命周期）、`@Documented`（文档）、`@Inherited`（继承）
       - SOURCE/CLASS/RUNTIME 三者区别？
         - SOURCE：编译丢弃；CLASS：字节码保留运行丢弃；RUNTIME：运行存在，可反射读取

       - @Override 为什么不能运行时读取？
         - 它是 SOURCE 级别，编译完成就删除，仅用于编译校验

       - 自定义注解使用流程？
         - ①定义注解 + 元注解；②代码上使用注解；③反射解析注解属性实现业务

       - 注解和注释 ///*/*的区别？
         - 注释仅给人看，编译器直接忽略；注解是代码标记，程序可读取处理