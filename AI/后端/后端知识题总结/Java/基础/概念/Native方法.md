- Java中，native方法是一种特殊类型的方法，它**允许java代码调用外部的本地代码**，即用C、C++或其他语言编写的代码。

- native关键字是java语言中的一种声明，用于标记一个方法的实现将在外部定义，没有实际的实现代码。

  - ```java
    public class NativeExample {
        public native void nativeMethod();
    }
    ```

- **实现**：

  - **生成JNI头文件**：使用`javac -h <dir>`选项从Java类生成C/C++的头文件，这个头文件包含了所有native方法的原型（旧的独立工具`javah`自`java9`废弃，改用`javac -h`）
  - **编写本地代码**：使用C/C++编写本地方法的实现，并确保方法签名与生成的头文件中的原型匹配。
  - **编译本地代码**：将C/C++代码编译成动态链接库（DDL，Windows上），共享库（SO，在Linux上）
  - **加载本地库**：在Java程序中，使用`System.loadLibrary()`方法来加载编译好的本地库，这样JVM就能找到并调用native方法的实现了。

