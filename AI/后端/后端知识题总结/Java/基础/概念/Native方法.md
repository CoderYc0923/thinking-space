- Java 中，`native` 方法允许 Java 代码调用外部本地代码（C/C++ 等）。

- `native` 关键字只做声明，方法体在外部实现：

  ```java
  public class NativeExample {
      public native void nativeMethod();
  }
  ```

- **实现步骤**

  1. **生成 JNI 头文件**：`javac -h <dir>`（旧工具 `javah` 自 Java 9 废弃）
  2. **编写本地代码**：C/C++ 实现，签名与头文件一致
  3. **编译本地库**：Windows → `.dll`，Linux → `.so`，macOS → `.dylib`
  4. **加载本地库**：`System.loadLibrary(...)`，JVM 才能找到并调用 native 实现

- 和 JNI 的关系：`native` 是语言层声明；**JNI** 是 JVM 规定的、Java 与本地代码互调的官方接口规范。
