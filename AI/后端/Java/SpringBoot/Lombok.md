## 一、什么是 Lombok

1. Lombok 是一款 **Java 编译期代码生成工具**。
2. 通过注解，在 `javac` 编译阶段自动生成样板代码（getter、setter、构造器、toString、equals、hashCode 等），**不需要手写模板代码，减少冗余**。
3. ⚠️ 核心关键点：代码不是运行时生成，是**编译期生成**；class 文件里存在完整方法，IDE 需要安装 Lombok 插件才能识别代码提示。

## 二、环境集成

1. Maven 依赖

   - ```xml
     <!-- Lombok 依赖 scope 必须是 provided -->
     <dependency>
         <groupId>org.projectlombok</groupId>
         <artifactId>lombok</artifactId>
         <version>1.18.30</version>
         <scope>provided</scope>
     </dependency>
     ```

2. Gradle

   - ```xml
     compileOnly 'org.projectlombok:lombok:1.18.30'
     annotationProcessor 'org.projectlombok:lombok:1.18.30'
     ```

3.  IDEA 必备操作

   - 安装插件：Lombok

   - 开启设置：`Settings -> Build,Execution,Deployment -> Compiler -> Annotation Processors`

     ✅ 勾选 **Enable annotation processing**

     不开启会出现：代码报红、找不到 get/set 方法，但项目能正常编译运行。

## 三、核心注解大全（高频使用）

1. @Data【最常用】

   - 等价组合：`@Getter + @Setter + @ToString + @EqualsAndHashCode + @RequiredArgsConstructor`

   - ```java
     import lombok.Data;
     
     @Data
     public class User {
         private Long id;
         private String username;
         private Integer age;
     }
     ```

   - 编译后自动生成：

     - 所有字段 getter /setter
     - toString ()（包含所有字段）
     - equals()、hashCode()
     - 无参构造？❌ **不会生成无参构造！**

   - 坑点提醒：

     - `@Data` 生成的 equals/hashCode 使用**所有字段**；如果实体有循环引用（一对多）会栈溢出
     - 如果使用 MyBatis-Plus / JPA 实体，慎用！如果有父类属性，默认不会纳入 equals
     - 想要无参构造，额外加 `@NoArgsConstructor`

2. @Getter / @Setter

   - 单独使用，灵活控制

   - ```java
     @Getter //所有属性get
     public class User {
         private Long id;
         @Setter // 仅username生成set
         private String username;
     }
     ```

   - 可选参数：`@Getter(AccessLevel.PRIVATE)`：控制方法访问权限

3. 构造器注解

   - @NoArgsConstructor

     - 生成**无参构造函数**：MyBatis、反射、序列化框架（Jackson）很多场景强制要求无参构造！

   - @AllArgsConstructor

     - 生成全参构造函数

   - @RequiredArgsConstructor

     - 生成包含final / @NonNull修饰字段的构造器

     - Spring推荐构造器注入经常搭配这个！

     - ```java
       @RequestArgsConstructor
       public class UserService {
           private final UserMapper userMapper; // final字段会进入构造参数
       }
       ```

   - 组合经典写法（后端实体标准写法）

     - ```java
       @Data
       @NoArgsConstructor
       @AllArgsConstructor
       public class User {}
       ```

4. @ToString

   - 自动生成toString

   - ```java
     @ToString(exclude = {"password"}) //排除密码字段
     public class User {
         private Long id;
         private String password;
     }
     // @ToString(callSuper = true) 把父类字段加入toString（重要！）
     ```

5. @EqualsAndHashCode

   - 生成equals()和hashCode()

   - ```java
     // 只使用id判断相等，排除其他字段
     @EqualsAndHashCode(onlyExpliccitlyIncluded = true)
     public class User {
         @EqualsAndHashCode.Include
         private Long id;
         private String name;
     }
     ```

   - @Data 默认自动包含所有字段，存在风险，复杂实体建议手动使用 `@EqualsAndHashCode`

6. @NonNull

   - 空值校验，编译后在方法开头增加空判断，空抛出 `NullPointerException`

   - ```java
     @Data
     public class User {
         @NonNull
         private String username;
     }
     // setUsername时，如果传入null直接抛异常
     ```

7. @Builder【建造者模式｜超级常用】

   - 快速实现建造者模式，链式创建对象

   - ```java
     @Builder
     @Data
     @NoArgsConstructor
     @AllArgsConstructor
     public class User {
         private Long id;
         private String username;
     }
     
     // 使用
     User user = User.builder().id(1L).username('张三').build();
     ```

   - ⚠️ **重大坑：**

     - 单独 `@Builder` 默认只会生成**全参构造**，不会有无参构造

     - 如果框架需要无参构造（Mybatis、JSON 反序列化），必须同时添加：@NoArgsConstructor` + `@AllArgsConstructor

     - 并且注意：**@NoArgsConstructor 和 @Builder 共存时，部分版本需要添加 `@Builder.Default` 处理默认值**

       - ```java
         @Builder
         @NoArgsConstructor
         @AllArgsConstructor
         @Data
         public class User {
             @Builder.Default
             private Integer age = 18; // 设置默认值
         }
         ```

8. @Slf4j【日志注解，项目高频】

   - 自动生成日志对象 `log`

   - ```java
     import lombok.slf4j.Slf4j;
     
     @Slf4j
     public class UserService {
         public void test(){
             log.info("测试日志");
         }
     }
     ```

   - 等价代码

     - ```java
       private static final org.slf4j.Longger log = org.slf4j.LonggerFactory.getLogger(UserService.class);
       ```

   - 同类日志注解：

     - `@Log4j2`：适配 log4j2
     - @CommonsLog

9. @Accessors 链式 setter

   - 让 set 方法支持链式调用

   - ```java
     @Data
     @Accessors(chain = true)
     public class User {
         private Long id;
         private String name;
     }
     // 使用
     User user = new User().setId(1L).setName("test");
     ```

   - 参数：fluent = true`：set 方法不带 set 前缀 `name("xxx")

10. @SneakyThrows

    - 自动捕获受检异常，不需要 try-catch，**开发工具慎用，掩盖异常**

    - ```java
      @SneakyThrows
      public void readFile(){
          FileReader r = new FileReader("a.txt");
      }
      ```

11. @Cleanup

    - 自动资源关闭（替代 try-with-resources）

    - ```java
      @Cleanup InputStream in = new FileInputStream("a.txt");
      ```

12. @Value

    - 不可变对象，替代 `@Data`：所有字段默认 `final`；只生成 get，无 set；生成全参构造；适合值对象 VO

    - ```java
      @Value
      public class UserVO {
          Long id;
          String name;
      }
      ```



## 四、生产环境避坑清单【面试高频考点】

1. 坑 1：@Data + 父类实体

   - ```java
     class BaseEntity {
         private Long createTime;
     }
     
     @Data
     public User extends BaseEntity {
         private Long id;
     }
     ```

   - 默认 `equals/hashCode` **不会包含父类字段**！

   - 解决方案：

   - ```java
     @Data
     @EqualsAndHashCode(callSuper = true)
     @ToString(callSuper = true)
     ```

2. 坑 2：@Builder 缺少无参构造导致序列化 / Mybatis 报错

   - ✅ 标准实体搭配：

   - ```java
     @Data
     @Builder
     @NoArgsConstructor
     @AllArgsConstructor
     @EqualsAndHashCode(callSuper = true)
     @ToString(callString = true)
     public User Extends BaseEntity {}
     ```

3. 坑 3：循环引用导致栈溢出

   - 一对多实体，双方都使用`@Data`，调用 equals、toString 会无限递归 StackOverflowError
   - 解决方案：
     - `@ToString(exclude = "list")` 排除关联字段
     - 不要直接用 @Data，手动使用 @Getter/@Setter

4. 坑 4：序列化问题

   - Lombok 生成方法和手写一致，**普通序列化无问题**；
   - 但是使用一些特殊序列化框架、Redis 序列化时，注意无参构造必须存在。

5. 坑 5：不要在接口、静态变量乱用注解

   - 注解只作用在实例字段。



## 五、项目最佳实践规范

1. DB 数据库实体（Mybatis/MP）

   - ```java
     @Data
     @NoArgsConstructor
     @AllArgsConstructor
     @ToString(callSuper = true)
     @EqualsAndHashCode(callSuper = true)
     public class User extends BaseEntity {}
     ```

   - 不推荐默认加 @Builder，DB 实体很少使用建造者；VO/DTO 可以用 @Builder

2. VO、DTO（接口出参入参）

   - ```java
     @Data
     @Builder
     @NoArgsConstructor
     @AllArgsConstructor
     public class UserVO {}
     ```

3. Service 层

   - 只使用 `@Slf4j`，不要给 service 加 @Data



## 面试常见问题汇总

1. Lombok 原理？
   - 基于 JSR269 注解处理器，编译期 AST 抽象语法树修改，生成字节码，不属于运行时反射
2. @Data 和 @Value 区别？
   - @Value：字段 final、无 setter、不可变类
   - @Data 可变类
3. @RequiredArgsConstructor 什么时候用？
   - Spring 构造器注入，注入 final 成员变量，推荐替代 @Autowired
4. @Builder 有什么缺陷？
   - 默认无无参构造；和父类搭配需要额外处理；默认不支持字段默认值，需要`@Builder.Default`