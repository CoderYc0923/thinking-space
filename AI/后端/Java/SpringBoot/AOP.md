# AOP 是什么（通俗易懂 + 代码示例）

## 一、全称与定义

**AOP = Aspect Oriented Programming 面向切面编程**

- OOP（面向对象）：纵向拆分业务，按**类、对象**划分（用户类、订单类）。
- AOP（面向切面）：横向抽取通用逻辑，解决**重复代码散落各处**的问题。

### 核心一句话

把**日志、权限校验、事务、接口耗时统计、异常捕获**这类和核心业务无关、到处重复的代码抽成独立切面，不用改业务代码就能插入执行。

## 二、核心术语（Spring AOP 标准）

1. 切面 Aspect

   

   封装通用逻辑的类（日志类、事务管理类）。

2. 连接点 JoinPoint

   

   程序中可以切入的位置：方法执行、异常抛出、字段赋值等；Spring AOP 只支持

   方法执行

   。

3. 切点 Pointcut

   

   筛选匹配哪些连接点（用表达式匹配类 / 方法，如所有 

   ```
   service
   ```

    层方法）。

4. 通知 Advice

   

   切面在切点处执行的逻辑，分 5 种：

   - `@Before`：方法执行前执行
   - `@AfterReturning`：方法正常返回后执行
   - `@AfterThrowing`：方法抛出异常时执行
   - `@After`：方法结束（无论正常 / 异常）执行
   - `@Around`：包裹目标方法，可手动控制目标方法何时执行、修改入参 / 返回值

5. 目标对象 Target

   

   被切面增强的原始业务类。

6. 代理 Proxy

   

   Spring 自动生成代理对象，替代原对象执行，实现切面插入。

## 三、解决什么痛点（举实际开发场景）

### 痛点：重复代码满天飞

订单、用户、商品三个 Service 每个方法都写：打印入参、记录耗时、异常打印日志

```
// 每个方法都重复这堆日志代码
public void createOrder(){
    log.info("方法入参：xxx");
    long start = System.currentTimeMillis();
    try{
        // 核心业务：创建订单
    }catch(Exception e){
        log.error("异常：",e);
        throw e;
    }finally{
        log.info("方法耗时：{}ms",System.currentTimeMillis()-start);
    }
}
```

### AOP 方案：只写一次切面，全部方法自动生效

只写一个日志切面，通过切点匹配所有 Service 方法，**业务代码完全干净，没有任何日志代码**。

## 四、SpringBoot AOP 最简代码示例

### 1. 引入依赖

```
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-aop</artifactId>
</dependency>
```

### 2. 日志切面类（Aspect）

```
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Aspect // 标记为切面
@Component
public class LogAspect {
    private static final Logger log = LoggerFactory.getLogger(LogAspect.class);

    // 切点表达式：匹配service包下所有类的所有方法
    @Around("execution(* com.demo.service.*.*(..))")
    public Object recordLog(ProceedingJoinPoint point) throws Throwable {
        // 1. 方法执行前
        String methodName = point.getSignature().getName();
        log.info("开始执行方法：{}", methodName);
        long start = System.currentTimeMillis();

        Object result;
        try {
            // 2. 执行原始业务方法
            result = point.proceed();
            // 3. 方法正常返回后
            log.info("方法{}执行完成，返回值：{}", methodName, result);
        } catch (Throwable e) {
            // 4. 异常时执行
            log.error("方法{}发生异常", methodName, e);
            throw e;
        } finally {
            // 5. 方法结束
            long cost = System.currentTimeMillis() - start;
            log.info("方法{}执行耗时：{}ms", methodName, cost);
        }
        return result;
    }
}
```

### 3. 业务 Service（完全无日志代码）

```
@Service
public class OrderService {
    public void createOrder() {
        // 纯核心业务逻辑
        System.out.println("创建订单业务");
    }
}
```

调用 `createOrder()` 时，切面自动执行日志逻辑，业务代码零侵入。

## 五、AOP 常见业务使用场景

1. **日志管理**：记录接口入参、出参、耗时、异常堆栈
2. **事务控制**：Spring 事务 `@Transactional` 底层就是 AOP
3. **权限校验**：接口执行前校验登录状态、角色权限
4. **接口限流、防重复提交**
5. **统一异常处理**
6. **数据脱敏**：返回前端时自动脱敏手机号、身份证
7. **缓存处理**：方法执行前查缓存，无缓存再执行业务

## 六、AOP 底层实现（Spring）

两种动态代理：

1. **JDK 动态代理**：目标类**实现接口**时使用，基于接口生成代理类
2. **CGLIB 代理**：目标类**没有实现接口**，通过继承目标类生成子类代理

Spring 会自动选择代理方式，开发者无需手动处理。

## 七、OOP vs AOP 对比

|   维度   |              OOP 面向对象              |           AOP 面向切面           |
| :------: | :------------------------------------: | :------------------------------: |
| 拆分思路 | 纵向分层，按业务模块拆分（用户、订单） |   横向抽取通用功能，跨模块复用   |
| 代码侵入 |    通用逻辑散落在各个类中，重复冗余    |    完全不修改业务代码，低侵入    |
| 适用场景 |            核心业务逻辑封装            | 通用辅助逻辑（日志、权限、事务） |