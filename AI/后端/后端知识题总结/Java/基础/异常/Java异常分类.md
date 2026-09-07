![](https://cdn.xiaolincoding.com//picgo/1720683900898-1d0ce69d-4b5d-41a6-a5df-022e42f8f4c5.webp)



**总览**

|             |             |                    |                                  | 含义         |
| ----------- | ----------- | ------------------ | -------------------------------- | ------------ |
| `Throwable` |             |                    |                                  |              |
|             | `Error`     |                    |                                  |              |
|             |             |                    | `OutOfMemoryError`               | 内存溢出     |
|             |             |                    | `StackOverflowError`             | 栈溢出       |
|             |             |                    | `NoClassDefFoundError`           | 类找不到     |
|             | `Exception` |                    |                                  |              |
|             |             | `RuntimeException` |                                  |              |
|             |             |                    | `NullPointerException`           | 空指针       |
|             |             |                    | `ArrayIndexOutOfBoundsException` | 数据越界     |
|             |             |                    | `ClassCastException`             | 类型强转异常 |
|             |             |                    | `ArithmeticException`            | 算数异常     |
|             |             |                    | `IllegalArgumentException`       | 参数非法     |
|             |             | 受检异常           |                                  |              |
|             |             |                    | `IOException`                    | IO读写异常   |
|             |             |                    | `SQLException`                   | 数据库异常   |
|             |             |                    | `FileNotFoundException`          | 文件不存在   |
|             |             |                    | `ParseException`                 | 日期解析异常 |



- Java的异常体系主要基于`Throwable`及其子类
- 其中有两个重要的子类`Error`和`Exception`
  - `Error`错误（非受检）：代表运行环境的错误，错误是程序无法处理的严重问题，比如虚拟机错误、动态链接库失效等
    - 程序不应该尝试捕获这类错误
    - 例如`OutOfMemoryError`,`StackOverflowError`等
  - `Exception`异常：表示程序本身可以处理的异常。分非运行时异常（受检异常）和运行时异常（非受检异常）
    - **非运行时异常（受检异常）**
      - 在**编译时**就必须被捕获或声明抛出
      - 通常是外部错误，如文件不存在`FileNotFoundException`、类未找到`ClassNotFoundException`等。
      - 需要强制处理这些可能出现的问题，增强程序的健壮性
    - **运行时异常（非受检异常）**
      - 特指`RuntimeException`及其子类
      - 运行时异常由程序逻辑错误抛出，如空指针访问`NullPointerException`、数组越界`ArrayIndexOutofBoundsException`等
      - 运行时异常不需要在编译时强制捕获或声明。