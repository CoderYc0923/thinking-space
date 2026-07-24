## 一、MVC架构和分层模型的关系

1. MVC：

   - Model（模型）承载数据、业务逻辑
   - View（视图）页面展示（前端页面、接口返回 JSON 都算视图）
   - Controller（控制器）中间人，接收请求、调度逻辑、返回视图

2. SpringBoot后端MVC对应分层

   ```
   View（前端页面/接口JSON）
       ↓
   Controller（C 控制器）
       ↓
   Service（业务逻辑，属于 Model）
       ↓
   DAO/Mapper（数据访问，属于 Model）
       ↓
   数据库
       
       
   // MVC 完整数据流转 + 模型对应
   前端 View
       提交参数 → 【入参DTO】
           ↓
   Controller(C)
       调用Service，传递DTO
           ↓
   Service(M 业务层)
       1. DTO → BO（封装业务完整数据）
       2. BO拆解，调用DAO查询数据库得到PO/DO
       3. 业务计算完成，数据组装为VO
           ↓
   DAO(M 数据访问层)
       操作数据库，返回PO/DO
           ↓
   数据库
   
   Controller拿到VO后 → 返回JSON给前端View
   ```

   **PO、DO、DTO、VO、BO、DAO 全部都属于 MVC 里的 M（Model 模型层）**，是 Model 内部细化拆分出来的细分模型。

3. 逐个对应 MVC 三层

   -  Controller（C 控制器）职责：接收前端请求、参数校验、调用 Service、组装数据返回前端
     - 入参 DTO：接收前端提交的表单 / JSON 参数
     - VO：处理完业务后，封装 VO 返回给前端（适配 View 视图）
   - View（V 视图） 
     - **VO 就是专门为 View 而生的模型**，只保留页面需要展示的数据，脱敏、裁剪多余字段
   - Model（M 模型层，核心）
     - Model 包含两大块：**数据访问层 (DAO)** + **业务层 (Service)**
     - DAO（Data Access Object）
       - 属于 Model 的数据访问组件，不是实体类
       - 作用：操作数据库，查询 / 新增 / 修改 PO/DO
     - PO / DO / Entity
       - Model 最底层，直接映射数据库表，DAO 查询数据库返回的原生数据模型
     - BO（Business Object）
       - Service 业务层内部模型，属于 Model
       - 复杂业务聚合多张表 DO 的数据，在 Service 内部流转计算
     - DTO（Data Transfer Object）
       - 跨层传输模型，属于 Model
       - Controller ↔ Service 之间传参
       - 微服务之间远程调用传输数据
       - 分为两种：**入参 DTO（前端传给 Controller）、出参 DTO（Service 内部流转）**

4. 核心关系总结

   - **MVC 是宏观分层思想**（控制器、视图、模型三层）；PO/DO/DTO/VO/BO/DAO 是**Model 层内部微观细分的数据载体**，二者是**整体与局部**的关系

   - 没有 MVC 架构，就不会衍生出这些细分模型：

     - 因为有 **View 视图**，所以需要 VO 适配页面展示
     - 因为有 **Controller 控制器** 做前后端中转，所以需要 DTO 传输参数
     - 因为有 **Model 模型层** 拆分业务层、数据库层，所以区分 BO、PO、DAO

     

## 二、先分清两类概念：**数据对象（实体类）** vs **分层职责（层接口）**

1. **DAO**：不是实体类，是**数据访问层接口 / 层**（操作数据库）
2. PO、DO、Entity、DTO、VO、BO、POJO：都是**Java 实体 Bean（模型类）**，只是对应项目分层不同场景



## 三、逐个详解（带场景、代码示例、使用层级）

1. POJO（Plain Old Java Object）普通 Java 对象

   - **定义**：无任何框架依赖、简单纯 Java 类，只有属性、get/set、构造、toString。

   - **特征**：不继承任何类、不实现接口、无注解。

   - **范围**：PO/DO/DTO/VO 全部都属于 POJO。

   - ```java
     // 标准POJO
     public class User {
         private Long id;
         private String username;
         //get set toString
     }
     ```

   - 

2. PO（Persistent Object）持久化对象

   - 等价别名：**DO(Data Object)、Entity**（MyBatis/JPA 标准叫法）

   - 层级：**数据库层，DAO 层使用**

   - 特点：字段和数据库表字段一一对应，包含数据库主键、创建时间、删除标记、外键等数据库专属字段

   - 适用：MyBatis 的实体、JPA 的 @Entity 实体

   - ```java
     // PO/DO/Entity 数据库映射实体
     @TableName("t_user")
     public class UserDo {
         private Long id;// 数据库主键
         private String username;
         private String password;
         private LocalDateTime createTime; // 数据库审计字段
         private Integer isDeleted; // 逻辑删除
         // get/set
     }
     ```

   - 

3. DAO（Data Access Object）数据访问对象

   - 不是实体类，是层 / 接口;**职责**：专门负责和数据库交互，CRUD 操作

   - MyBatis：Mapper 接口 = DAO

   - JPA：Repository 接口 = DAO

   - 层级：持久层，上层 Service 调用 DAO 操作 PO/DO

   - ```java
     //DAO（Mapper接口）
     @Mapper
     public interface UserDAO {
         UserDO selectById(Long id);
         void insert(UserDAO userDO);
     }
     ```

   - 

4. DTO（Data Transfer Object）数据传输对象

   - 数据传输载体，用于层与层之间传递数据

   - 使用场景：Service 层 ↔ Controller 层 / 微服务之间远程调用

   - 核心作用：**解耦数据库 PO 和前端数据，按需组装 / 裁剪字段**

     - 不会携带数据库冗余字段（isDeleted、createTime 等）
     - 可以聚合多张表的数据（多表联查结果封装）
     - 微服务 RPC 调用统一传输载体

   - ```java
     // 示例：用户详情需要用户表 + 角色表数据，封装 UserDTO 传给 Controller
     // DTO 服务层传输对象
     public class UserDTO {
         private Long userId;
         private String username;
         private String phone;
         private List<String> roleName; // 关联角色，PO没有这个字段
         // get set
     }
     ```

   - 

5. VO（View Object）视图对象

   - 视图层对象，专门返回给前端页面 / 接口

   - 层级：**Controller 层返回给前端**

   - 和 DTO 区别：

     - DTO：**后端内部流转**（Service 之间、微服务调用）
     - VO：**对外输出给前端**，完全贴合前端页面展示需求
     - VO 可以做字段脱敏（手机号隐藏中间 4 位、密码不返回）
     - VO 字段命名可适配前端（下划线 / 小驼峰按需调整）

   - ```java
     // VO 返回前端视图对象
     public class UserVO {
         private Long id;
         private String username;
         private String phone; // 脱敏后：138****1234
         private List<String> roles;
         // 不传递密码、删除标记等敏感/冗余字段
     }
     ```

   - 

6. BO（Business Object）业务对象

   - 直译：业务对象，封装完整业务逻辑所需数据

   - 层级：**Service 业务层内部使用**

   - 适用场景：复杂业务，需要聚合多个 DO/DTO，封装成一个完整业务实体

   - ```java
     // 举例：创建订单业务，需要订单 DO、商品 DO、地址 DO、用户信息，整合为 OrderBO，在订单 Service 内部流转处理
     // BO 业务层封装对象
     public class OrderBO {
         private OrderDO order;
         private List<OrderItemDO> itemList;
         private AddressDTO address;
         private UserDTO userInfo;
         // 订单计算、校验、入库整套业务使用
     }
     ```



## 四、分层流转完整链路（从数据库到前端）

```java
数据库表
    ↓
PO/DO/Entity（MyBatis实体，映射表）
    ↓
DAO/Mapper（操作数据库，查询返回PO）
    ↓
BO（复杂业务层内部聚合多个DO）
    ↓
DTO（Service层传输，传给Controller）
    ↓
VO（Controller封装，返回前端页面）
```





## 五、快速区分对照表

| 术语         | 全称                   | 所属层级             | 核心作用             | 是否实体类   |
| ------------ | ---------------------- | -------------------- | -------------------- | ------------ |
| POJO         | Plain Old Java Object  | 通用                 | 基础普通 Java 类     | 是（父类）   |
| PO/DO/Entity | Persistent/Data Object | 持久层               | 映射数据库表         | 是           |
| DAO          | Data Access Object     | 持久层               | 数据库 CRUD 接口     | 否（接口层） |
| BO           | Business Object        | 业务 Service 层      | 封装复杂业务聚合数据 | 是           |
| DTO          | Data Transfer Object   | Service ↔ Controller | 后端内部数据传输     | 是           |
| VO           | View Object            | Controller 层        | 封装返回前端视图数据 | 是           |

