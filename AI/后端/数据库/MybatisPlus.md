## MyBatis-Plus 3.5.x 核心用法手册

规范建议：优先使用 Lambda 构造器，杜绝硬编码字符串字段

## 一、BaseMapper<T> Mapper 层基础接口

```java
@Mapper
public interface EmployeeMapper extends BaseMapper<Employee>
```

表格

|           方法            |        功能        |                          注意事项                           |
| :-----------------------: | :----------------: | :---------------------------------------------------------: |
|      selectById(id)       |  根据主键查询单条  |                       无数据返回 null                       |
|    selectBatchIds(ids)    |    主键批量查询    |                    参数：Collection 集合                    |
|    selectOne(Wrapper)     |    条件查询单条    | 查询多条直接抛出`TooManyResultsException`，仅用于唯一键查询 |
|    selectList(Wrapper)    |  条件查询多条数据  |                  Wrapper 为 null 查询全表                   |
|    selectMaps(Wrapper)    | 查询返回 List<Map> |                     无需实体类场景使用                      |
|   selectCount(Wrapper)    |  统计符合条件行数  |                  Wrapper 为 null 统计全表                   |
| selectPage(Page, Wrapper) |      分页查询      |              **必须配置分页插件，否则不生效**               |
|      insert(entity)       |    新增单条记录    |                  实体 null 字段入库为 NULL                  |
|      deleteById(id)       |    根据主键删除    |                              -                              |
|    deleteBatchIds(ids)    |    主键批量删除    |                              -                              |
|      delete(Wrapper)      |      条件删除      |              Wrapper 为空会删除全表，谨慎使用               |
|    updateById(entity)     |    根据主键更新    |                **仅更新实体中非 null 字段**                 |
|  update(entity, Wrapper)  |      条件更新      |           实体填充更新值，Wrapper 设置 where 条件           |

### 代码示例

```java
// 根据用户名查询用户
employeeMapper.selectOne(Wrappers.lambdaQuery(Employee.class)
        .eq(Employee::getUsername, username));

// 条件批量更新
employeeMapper.update(
    new Employee().setStatus(1),
    Wrappers.lambdaUpdate(Employee.class).eq(Employee::getName, "张三")
);
```

## 二、IService + ServiceImpl Service 层封装

### 基础结构

```java
// Service接口
public interface EmployeeService extends IService<Employee>
// 实现类
@Service
public class EmployeeServiceImpl extends ServiceImpl<EmployeeMapper, Employee> implements EmployeeService
```

### 常用方法

#### 查询

```java
getById(id)
getOne(Wrapper)
list(Wrapper)
listByIds(ids)
count(Wrapper)
page(Page, Wrapper)
```

#### 新增

```java
save(entity)
saveBatch(集合)
saveOrUpdate(entity)
saveOrUpdateBatch(集合)
```

#### 删除 & 更新

```java
removeById(id)
removeByIds(ids)
remove(Wrapper)
updateById(entity)
update(entity, Wrapper)
updateBatchById(集合)
```

> 重点区分：BaseMapper 不存在`updateBatchById`，批量更新请使用 Service 层方法

## 三、四大条件构造器

### 1. QueryWrapper<T>

普通构造器，字段使用字符串，容易拼写错误，**不推荐**

```java
new QueryWrapper<Employee>()
        .eq("username", "admin");
```

### 2. LambdaQueryWrapper<T>【查询首选】

方法引用，编译期字段校验

```java
// 两种创建方式
LambdaQueryWrapper<Employee> wrapper = new LambdaQueryWrapper<>();
LambdaQueryWrapper<Employee> wrapper = Wrappers.lambdaQuery();

wrapper.eq(Employee::getUsername, name)
       .like(Employee::getName, keyword)
       .ge(Employee::getCreateTime, start)
       .orderByDesc(Employee::getCreateTime);
```

### 3. LambdaUpdateWrapper<T>【更新首选】

无需传入实体，直接 set 更新字段

```java
LambdaUpdateWrapper<Employee> updateWrapper = Wrappers.lambdaUpdate();
updateWrapper.set(Employee::getStatus, 0)
             .eq(Employee::getDeptId, 100);
employeeMapper.update(null, updateWrapper);
```

### 条件方法对照表

|        方法        |             SQL 语义             |
| :----------------: | :------------------------------: |
|    eq(col,val)     |               `=`                |
|    ne(col,val)     |               `!=`               |
|    gt(col,val)     |               `>`                |
|    ge(col,val)     |               `>=`               |
|    lt(col,val)     |               `<`                |
|    le(col,val)     |               `<=`               |
|   like(col,val)    |          `LIKE '%val%'`          |
| likeLeft(col,val)  |          `LIKE '%val'`           |
| likeRight(col,val) |          `LIKE 'val%'`           |
|   in (col, 集合)   |           `IN (?,?,?)`           |
| notIn (col, 集合)  |         `NOT IN (?,?,?)`         |
|    isNull(col)     |            `IS NULL`             |
|   isNotNull(col)   |          `IS NOT NULL`           |
|        or()        |             OR 条件              |
|       and()        |          嵌套 AND 条件           |
|  orderByAsc(col)   |             升序排序             |
|  orderByDesc(col)  |             降序排序             |
|     last(sql)      | 末尾拼接 SQL，存在注入风险，慎用 |

### 动态条件拼接（高频）

```java
String name = dto.getName();
LambdaQueryWrapper<Employee> wrapper = Wrappers.lambdaQuery();
// 第一个参数true才拼接条件
wrapper.eq(Objects.nonNull(name), Employee::getName, name);
```

## 四、分页功能

### 分页插件配置 (SpringBoot)

```java
@Bean
public MybatisPlusInterceptor mybatisPlusInterceptor() {
    MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
    interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
    return interceptor;
}
```

### 分页代码

```java
// 参数：当前页码，每页条数
Page<Employee> page = new Page<>(pageNum, pageSize);
LambdaQueryWrapper<Employee> wrapper = Wrappers.lambdaQuery();
Page<Employee> resultPage = employeeMapper.selectPage(page, wrapper);

List<Employee> dataList = resultPage.getRecords();
long total = resultPage.getTotal();
```

Service 简化写法：`employeeService.page(page, wrapper)`

## 五、实体类常用注解

```java
@TableName("employee")
public class Employee {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("username")
    private String username;

    @TableField(exist = false)
    private String token;
}
```

主键策略：

- `AUTO`：数据库自增
- `ASSIGN_ID`：雪花算法（默认，分布式推荐）

## 六、常见踩坑清单

1. `selectOne` 匹配多条数据直接抛出异常，不确定条数优先使用`list()`
2. `updateById` 不会更新实体中 null 字段；需要置空字段使用`LambdaUpdateWrapper.set()`
3. `delete(Wrapper)`、`update(entity,wrapper)` 若 Wrapper 为空，会操作全表，生产环境禁止
4. 分页必须注册分页插件，否则不会分页
5. 逻辑删除配置

```yaml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-field: deleted
      logic-delete-value: 1
      logic-not-delete-value: 0
```

## 七、登录场景示例代码

```java
LambdaQueryWrapper<Employee> wrapper = Wrappers.lambdaQuery();
wrapper.eq(Employee::getUsername, loginDTO.getUsername());
Employee employee = employeeMapper.selectOne(wrapper);

if (employee == null) {
    throw new RuntimeException("账号不存在");
}
// 后续密码校验逻辑
```