## 一、演进路线概览

1. JDBC原生 -> yml配置化 -> MyBatis -> MyBatis-Plus ->完整三层架构
2. 每一层的升级都不是为了”少写代码“这么简单，而是对职责边界的重新划分



## 二、JDBC阶段：理解一切的基石

1. 核心认知：
   - JDBC让你直面最原始的问题：
     - 连接从哪里来 ？DriverManager.getConnection()
     - SQL怎么执行？PreparedStatement
     - 结果怎么处理？手动ResultSet遍历 + 字段映射
     - 资源怎么关闭？finally或者try-with-resources
2. 这一阶段的价值：
   - 手写JDBC的最大意义不在于”学会怎么查数据库“，而在于你必须亲自处理每一个环节。
   - 连接管理、SQL执行、结果映射、异常转换，都是你一手包办。这种”全链路掌控感“是后续学习任何ORM框架的地基。
3. 实际问题：
   - 连接创建开销大，并发性能差
   - 大量重复模板代码
   - SQL与Java代码强耦合
   - 异常体系复杂，需要手动处理SQLException



## 三、yml + DataSource：连接管理的专业化

1. 架构变化：
   - 引入Spring Boot + HikariCP后，连接管理从”每次现建“变成”池化管理“
2. 关键认知：
   - DataSource不是MySQL的东西，是Java标准库javax.sql定义的接口。
   - MySQL驱动里虽有实现，但Spring Boot默认用的是HikariCP。
   - 你@Autowired DataSource拿到的永远是连接池的实现类，不是驱动层的对象
3. 资源关闭的误区：
   - 错以为conn.close()是断开连接，但实际是归还连接池，TCP连接并未断开。这一点在理解连接池工作机制时至关重要



## 四、MyBatis：DAO层的质变

1. 从类到接口，MyBatis带来的最大变化不是少写代码，而是DAO的存在形态发生了根本改变
   - JDBC阶段的DAO形态是：class，自己写实现
   - MyBatis阶段的DAO形态是：interface，框架生成代理，只声明需求
     - 你定义一个接口，加一个@Select注解，MyBatis在运行时用动态代理生成实现类。你从”怎么干“中解脱出来，只关心”干什么“
2. 实体类的角色
   - 实体类始终是class，不能是interface。
     - 因为MyBatis需要反射newInstance()创建对象并填充字段。接口没有构造器，也没有字段存储空间，天然无法承担数据容器的角色
3. 无参构造的重要性
   - MyBatis通过无参构造创造对象，再通过setter填充数据。如果实体类只有全参构造而缺失无参构造，启动直接失败。这是Lombok使用中最容易被忽略的坑



## 五、Mybatis-Plus：Service层的进一步解放

1. IService + ServiceImpl的意义

   - MyBatis解决了DAO层的模板代码，但Service层仍然充斥着大量的CRUD转发代码。

   - MyBatis-Plus的IService和ServiceImpl把这一层也标准化了：

     - ```java
       public interface StudentService extends IService<Student>{}
       
       @Service
       public class StudentServiceImpl extends ServiceImpl<StudentMapper, Student> implements StudentService {}
       ```

     - 继承ServiceImpl后，17个常用CRUD方法全部内置，单表操作一个字都不用写。

2. baseMapper的来源

   - ServiceImpl内部已经完成了Mapper的注入：

     - ```java
       public class ServiceImpl<M extends BaseMapper<T>, T> {
           @Autowired
           protected M baseMapper; //父类注入，子类直接用
       }
       ```

     - 因此Service实现类中不需要、也不应该再手动写@Autowired注入Mapper。重复注入不仅是冗余，还会让人误以为MP的继承机制需要手动配合

3. 自定义SQL的定位

   - BaseMapper解决不了的场景（多表联查、复杂动态条件）才需要自定义SQL。此时在Mapper中用注解或XML编写，Service中直接调用即可。自定义方法与MP内置方法共存，互不干扰。



## 六、Controller层：接口标准化

1. 分层职责

   - Controller：接请求、验参数、包结果
   - Service：业务逻辑编排
   - Mapper：数据访问

   Controller永远不直接调用Mapper。事务、缓存、权限等业务横切关注点都在Service层统一管理

2. 统一返回体的必要性

   - 裸返回List<Student>看似简洁，但前端无法区分成功与失败。统一包装后：

     - ```json
       {
           "code":200,
           "msg":"success",
           "data": [...]
       }
       ```

     - 前端通过code判断状态，通过data取数据，通过msg展示提示，三者职责清晰

3. 构造器注入优于字段注入

   - ```java
     @RestController
     @RequiredArgsConstructor
     public class StudentController {
         private final StudentService studentService;
     }
     ```

   -  final + 构造器注入的好处：

     - 依赖不可变，防止运行时意外修改
     - 便于单元测试（直接new即可注入mock）
     - Spring官方推荐方式



## 七、实际落地中遇到的关键问题

1. JDK版本与工具链兼容性

   - JDK21搭配旧版Lombok时出现编译期内部API错误。根本原因时Lombok通过字节码操作直接访问javac的内部结构，而这些结构在JDK21中发生了变化。降级到JDK17后问题彻底消失。

2. 包扫描路径配置

   - Spring Boot默认扫描启动类所在包以及其子包。如果启动类直接放在src/main/java根目录，而业务代码在dao\pojo等平级目录中，组件将无法被扫描到，导致@Autowired失败
   - 解决：建立统一的父包（如org.demo），将所有业务包作为其子包

3. 实体类的多重角色，在实际项目中，实体类会根据使用场景拆分：

   - Entity：数据库映射，与表结构一一对应
   - DTO：入参接收，承载前端提交的字段
   - VO：出参封装，控制返回给前端的字段范围

   



