流程：

- 业务代码`throw BizException`，不写一堆`try-catch`，`Spring MVC`调到`@ExceptionHandler`转成统一`JSON`，前端看`code/messgae`

实现：

- 先自定义业务异常（一般继承`RuntimeException`）
- 全局`@RestControllerAdvice`统一转成接口返回

```java
// 自定义业务异常
@Getter
public class BizException extends RuntimeException {
    private final int code; //业务错误码
    
    public BizException(int code, String message) {
        super(message);
        this.code = code;
    }
}

// 用RuntimeException：业务层不用到处写throws，抛出去由全局处理器接收
```

```java
// 错误码枚举
@Getter
public emun ErrorCode {
   USER_NOT_FOUND(40001, "用户不存在"),
    STOCK_NOT_ENOUGH(40002, "库存不足");
    
    private final int code;
    private final String message;
    
    private ErrorCode(code, message) {
        this.code = code;
        this.message = message;
    }
}
```

```java
// 创建统一返回体
public class Result<T> {
    private int code;
    private String message;
    private T data;
    
    public static <T> Result<T> fail(int code, String message) {
        Result<T> r = new Result<>();
        r.code = code;
        r.message = message;
        return r;
    }
}
```

```java
// 全局异常处理
@RestControllerAdvice
public class GlobalExceptionHandler {
    // 捕获BizException统一处理
    @ExceptionHandler(BizException.class)
    public Result<Void> handleBiz(BizException e) {
        return Result.fail(e.getCode(), e.getMessage());
    }
    
    // 其他异常处理
    @ExceptionHandler(Exception.class)
    public Result<Void> handleOther(Exception e) {
        // 未知异常：打日志，别把堆栈直接给前端
        // log.error("系统异常", e);
        return Result.fail(50000, "系统繁忙，请稍后重试");
    }
}
```

```java
// 业务里怎么用 / 怎么「包装」
// 直接抛业务异常
if (user == null) {
    throw new BizException(40001, "用户不存在");
}
// 包装底层异常（保留 cause）
try {
    payClient.pay(order);
} catch (IOException e) {
    throw new BizException(50001, "支付调用失败", e);
}
```

