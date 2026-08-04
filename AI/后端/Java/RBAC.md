# Java RBAC 权限模型

## 一、概念

RBAC（Role-Based Access Control）基于角色的访问控制，是 Java 后端管理系统主流权限模型。

核心链路：**用户 → 角色 → 权限**

权限不直接绑定用户，先将权限分配给角色，再为用户分配角色，实现权限解耦管理。

## 二、RBAC96 四层标准模型

### RBAC0（基础模型｜项目最常用）

基础三要素：用户、角色、权限，两张多对多中间表，无角色继承。

### RBAC1（角色继承）

支持角色层级继承，子角色自动拥有父角色全部权限。

示例：超级管理员 → 部门管理员 → 普通员工

### RBAC2（约束模型）

增加业务约束规则：

1. 互斥角色：同一用户不能同时拥有互斥角色（财务制单 / 财务审核）
2. 角色基数限制：一个用户最多绑定 N 个角色
3. 会话激活限制：登录会话可启用 / 禁用指定角色

### RBAC3（统一模型）

RBAC1 + RBAC2，包含继承与约束，适用于政务、大型 OA 复杂系统。

## 三、数据库通用表结构（RBAC0）

共 5 张核心表

1. `sys_user` 用户表
2. `sys_role` 角色表
3. `sys_permission` 权限表
4. `sys_user_role` 用户 - 角色中间表（多对多）
5. `sys_role_permission` 角色 - 权限中间表（多对多）

关系说明：

- 一个用户可分配多个角色
- 一个角色可分配给多个用户
- 一个角色拥有多条权限
- 一条权限可归属多个角色

## 四、权限标识规范

### 1. 标识符格式（主流）

格式：`模块:资源:操作`

```java
user:list
user:add
user:edit
user:delete
system:dict:query
```

适配：SpringSecurity、Sa-Token、Shiro 注解鉴权

```java
@PreAuthorize("hasPermission('user:list')")
```

### 2. URL 匹配模式

适用于简易系统，直接匹配请求路径，精细化控制较弱。

## 五、RBAC 能力边界

1. RBAC 负责**功能权限**：能否访问接口、展示按钮、访问菜单
2. **原生不支持数据权限**

> 数据权限：用户能够查询哪些业务数据（按部门、创建人、数据范围过滤），需要额外开发实现。

## 六、优缺点

### 优点

1. 权限集中维护，新增用户仅分配角色，无需逐个配置权限
2. 修改角色权限，所有绑定该角色的用户自动生效
3. 模型成熟，适配绝大多数后台、ERP、SaaS 系统

### 缺点

1. 缺少天然数据隔离能力，需扩展开发数据权限
2. 极致复杂组织机构场景下，单纯 RBAC 灵活性不足，可引入 ABAC 补充

## 七、常见 Java 权限框架

1. Spring Security：SpringBoot 生态官方方案，功能全面
2. Apache Shiro：老牌轻量框架，旧项目广泛使用
3. Sa-Token：国产轻量化权限框架，API 简洁，上手门槛低

## 八、RBAC vs ACL

- ACL（访问控制列表）：用户直接绑定权限。用户量大时维护成本极高，适合小型系统。
- RBAC：用户通过角色间接关联权限，企业级系统标准方案。

## 九、简易核心代码模型

```java
class User {
    Long id;
    List<Role> roles;
}

class Role {
    Long id;
    List<Permission> permissions;
}

class Permission {
    String permKey; // 权限标识 user:list
}

/**
 * 权限校验逻辑
 */
public boolean hasPermission(User user, String requiredPerm) {
    return user.getRoles().stream()
            .flatMap(role -> role.getPermissions().stream())
            .anyMatch(perm -> perm.getPermKey().equals(requiredPerm));
}
```

## 十、面试高频考点

1. RBAC 五张表结构以及表之间关系
2. RBAC0~RBAC3 模型区别
3. RBAC 能否实现数据权限？答：不能，仅管控功能权限
4. RBAC 与 ACL 的区别
5. 权限字符串规范以及注解鉴权使用方式