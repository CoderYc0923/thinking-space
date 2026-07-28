# 22. JVM 基础入门（基础面试题）

## 前置总览

1. 什么是 JVM
   - **JVM（Java Virtual Machine，Java 虚拟机）**：一套**虚拟计算机规范**，拥有独立完整的指令集、内存模型、执行引擎，专门用于执行 **Java 字节码 (.class)** 文件
   - 核心特性：**一次编译，到处运行**
     - 源码 `.java` → 编译器编译 → 跨平台统一字节码 `.class`
     - 不同操作系统（Windows/Linux/MacOS）安装对应平台实现的 JVM
     - JVM 屏蔽操作系统、硬件差异，统一解析执行字节码
   - 关键区分：
     - JDK：开发工具包（JRE + 编译工具 javac、调试工具等）
     - JRE：Java 运行环境（JVM + Java 基础类库 rt.jar）
     - JVM：仅负责执行字节码的虚拟机核心
2. JVM 两大分类
   - 标准 Java 虚拟机（HotSpot，主流）
     - Oracle JDK、OpenJDK 默认虚拟机，市面 99% 项目使用，内置成熟垃圾回收器、即时编译器
   - 其他虚拟机实现
     - J9：IBM 开发，多用于大型服务器、云环境
     - GraalVM：新一代高性能虚拟机，支持 Java、JS、Python 多语言混合编译，支持 AOT 静态编译
     - Dalvik/ART：安卓专属虚拟机，非标准 JVM，不执行标准 class，转换 dex 文件

## 一、JVM整体架构（五大核心模块）

完整执行流程：.class字符 -> 类加载子系统 -> 运行时数据区（内存模型） -> 执行引擎 -> 本地方法接口

### 模块1：类加载子系统ClassLoader

负责磁盘 / 网络读取.class字节码文件，校验、解析、初始化类，将类元数据存入方法区

1. **类加载全过程三大阶段**

   - 阶段1：**加载Load**

     - 通过类全限定名读取二进制字节流（本地文件，jar包、网络）
     - 将字节流代表的静态存储结构，转换为方法区运行时数据结构
     - 在堆中生成代表该类的唯一java.lang.Class对象，作为反射入口

   - 阶段2：**链接Link**

     - 验证Verify：字节码安全验证，防止恶意、畸形class文件损坏JVM

       - 文件格式校验：是否标准class文件、版本号是否兼容当前JVM
       - 元数据校验：类继承、访问修饰符合法性
       - 字节码校验：指令逻辑合法，不会栈溢出、非法跳转
       - 符号引用校验：引用的类、方法、字段存在且权限合法

     - 准备Prepare:为静态变量分配内存，赋默认零值

       - ```java
         public static int num = 100;
         //准备阶段：num分配内存，赋值默认0
         //初始化阶段：才会赋值100
         public static final int CONST = 200;
         // static final常量：编译期直接存入常量池，准备阶段直接赋值200
         ```

     - 解析Resolve：将常量池中的符号引用，替换为直接内存地址（直接引用）

       - 符号引用：字符串描述，例如com.demo.User；
       - 直接引用：内存指针、偏移量，可直接定位目标

   - 阶段3：**初始化Initialize**

     - **真正执行类静态逻辑**，按代码顺序执行：
       - 静态变量显式赋值
       - 静态代码块static{}（父类优先初始化，子类初始化前必须完成父类初始化）

2. 类加载器**双亲委派**模型

   JVM内置三层系统类加载器，层级自上而下为：

   - Bootstrap ClassLoader 启动类加载器
     - C/C++编写，不属于Java类，无法直接获取实例
     - 加载JVM核心基础类库：rt.jar、java.lang.*、java.util.*等
     - 加载路径：JAVA_HOME/jre/lib
   - Extension ClassLoader 扩展类加载器
     - Java实现，父加载器为启动类加载器
     - 加载扩展包：JAVA_HOME/jre/lib/ext下所有的jar包
   - Application ClassLoader 应用程序类加载器（系统类加载器）
     - Java实现，父加载器为扩展类加载器
     - 加载项目classpath下的自定义类、第三方依赖jar（Maven依赖）
   - 自定义类加载器
     - 开发者继承ClassLoader重写loadClass/findClass实现，用于热加载、加密class、动态加载远程jar

   **双亲委派工作机制**

   - 加载一个类时，子加载器先委派给父加载器，逐层向上，直到启动类加载器；
   - 父加载器无法加载（找不到类）时，才向下交给子加载器加载

   **双亲委派两大核心作用**

   - **安全防护**：防止开发者自定义java.lang.String这类核心类替换原生类，破坏JVM安全
   - **类全局唯一**：保证同一个全限定名的类，在JVM中只加载一次，避免多份Class对象造成类型转换异常

   **破坏双亲委派场景**

   破坏双亲委派 = 打破”先委托父类“这个核心原则，子加载器不向上委派，直接自己加载类

   - 为什么需要破坏双亲委派

     - ```
       双亲委派核心优势是安全、类全局唯一，但存在天然缺陷：上层类加载器无法加载下层类加载器加载的类
       1. Bootstrap、Ext、App是自上而下层级
       2. 父加载器完全看不到子加载器加载的自定义类
       3. 但很多JDK底层工具类（启动类加载器加载）需要调用开发者自定义类（App加载器），形成[父加载器依赖子加载器]。
       ```

   - 四大经典场景

     - 场景1： SPI服务提供者接口（最经典、面试最高频）（TCCL）

       - 什么是SPI

         - ```
           SPI:Service Provider Interface, JDK提供的服务扩展机制
           核心逻辑：JDK核心接口（Bootstrap加载），实现类由第三方 / 开发者提供（App加载器）
           ```

       - 矛盾点（必须破坏双亲委派的根源）

         - ```
           1. SPI接口（如java.sql.Driver）：rt.jar中，由Bootstrap启动类加载器加载
           2. 数据库驱动实现类（如com.mysql.cj.jdbc.Driver）：Maven引入，classpath下，由App应用类加载器拦截加载
           3. 矛盾：Bootstrap是父加载器，它看不到App加载器加载的驱动实现类，默认双亲委派下完全无法实例化驱动
           ```

       - 解决方案：线程上下文类加载器ThreadContextClassLoader(TCCL)

         - ```
           1. 线程默认上下文类加载器 = AppClassLoader（子加载器）
           2. 核心逻辑：父加载器（Bootstrap）通过线程上下文拿到下层子加载器，绕过双亲委派，直接用子加载器加载实现类
           3. 破坏委派行为：没有先向上委托父加载器，直接使用下层加载器加载类，破坏【父优先】规则
           ```

       - JDBC完整执行流程（实例讲解）

         - ```
           1. 代码：Class.forName("com.mysql.cj.jdbc.Driver") //通过反射获取class对象
           2. 早期JDBC：手动加载驱动类，App加载器直接加载，无委派冲突
           3. 现代JDBC4.0+自动注册驱动流程：
           	3.1 DriverManager类由Bootstrap加载
           	3.2 DriverManager内部执行SPI逻辑，获取当前线程上下文类加载器（AppClassLoader）
           	3.3 直接使用AppClassLoader去读META-INF/services/java.sql.Driver文件
           	3.4 文件中写死驱动全类名com.mysql.cj.jdbc.Driver，App加载器直接加载该驱动实现类
           	3.5 整个过程DriverManager（父加载器）没有向上委派，直接调用子加载器加载，破坏双亲委派
           ```

       - 同类框架案例

         - ```
           SLF4J日志门面、Dubbo SPI、SpringBoot自动配置、Java内置JNDI、XML解析器都是用TCCL破坏双亲委派
           ```

     - 场景2：热部署 / 热加载框架（Spring DevTools、JRebel）（重写）

       - 业务需求：开发时修改Java代码，无需重启整个Spring容器，自动重新编译、加载类、实时生效

       - 默认双亲委派的缺陷

         - AppClassLoader加载过一次类后，会缓存Class对象；
         - 按照双亲委派，同一个全限定名类只会加载一次，缓存永久生效，无法重新加载修改后的class文件

       - 破坏双亲委派实现方案

         - ```
           自定义类加载器，重写loadClass()方法，完全放弃向上委派逻辑：
           1. 自定义类加载器不执行父类加载器委派，优先自己读取target/classes下最新编译的class字节码
           2. 每次代码变更，销毁旧自定义类加载器，创建全新自定义类加载器重新加载所有业务类
           3. Spring DevTools 实现细节：
           	3.1 区分两类类：JDK核心类（交给系统加载器正常委派加载）、项目自定义业务类（自定义加载器直接加载，不委派父类）
           	3.2 重写loadClass，对业务类直接调用findClass，跳过双亲委派逻辑
           	3.3 代码改动后，关闭当前自定义加载器，新建加载器，实现类热替换
           ```

       - 破坏行为总结

         - 自定义类加载器收到业务类加载请求，不向上委派父加载器，直接自己加载，彻底打破双亲委派

     - 场景3：模块化容器框架OSGi（自定义网状委派规则）

       - OSGi定位：Java模块化动态容器，将应用拆分为多个Bundle，支持模块动态安装、卸载、启动、停止

       - 双亲委派不适用的矛盾

         - ```
           标准双亲委派是全局单一三层固定层级，所有类加载请求统一向上委派
           但OSGi每个Bundle拥有独立自定义类加载器：
           1. BundleA、BundleB、BundleC是平级模块，互不隶属
           2. BundleA需要引入BundleB中的类，BundleB又依赖BundleC
           3. 固定三层父子委派模型无法实现平级模块相互加载
           ```

       - OSGi破坏双亲委派的自定义委派规则

         - ```
           OSGi实现网状委派模型，完全抛弃JDK默认的树状双亲委派：
           1. 每个Bundle类加载器加载类时，不再固定向上委托Ext/Bootstrap
           2. 优先按照开发者定义的导入导出规则，委派给依赖的其他Bundle加载器（平级委派）
           3. 只有JDK核心类，才委派给系统父加载器
           4. 实现效果：平级模块相互加载、动态卸载模块，默认双亲委派完全做不到
           ```

       - 破坏行为：类加载优先委派给平级Bundle加载器，而非上层父加载器，完全颠覆双亲委派【父优先】核心规则

     - 场景 4：自定义加密 Class 文件、远程动态加载 Jar

       - 业务场景

         - 代码加密：为保护项目源码，编译后的 class 文件做 AES 加密，普通系统类加载器读取字节码会解析失败
         - 远程加载：Jar 包存储在远程服务器，程序运行时通过网络下载字节码，本地无 Jar 文件

       - 双亲委派缺陷

         - 继承 ClassLoader，重写核心两个方法：
           - 重写 `loadClass(String name)`：跳过向上委派逻辑，直接调用自身 findClass
           - 重写 `findClass(String name)`：自定义读取字节码逻辑（本地解密、网络下载字节流），调用 defineClass 生成 Class 对象

       - 简单代码示例（破坏双亲委派的自定义加载器）

         - ```java
           public class EncryptClassLoader extends ClassLoader {
               @Override
               public Class<?> loadClass(String name) throws ClassNotFoundException {
                   // 破坏双亲委派：不再先调用super.loadClass()向上委派
                   // 1. JDK核心类交给父加载器正常加载（规避安全问题）
                   if(name.startsWith("java.") || name.startsWith("javax.")){
                       return super.loadClass(name);
                   }
                   // 2. 自定义加密类，直接自己加载，不委派父类
                   Class<?> clazz = findClass(name);
                   if(clazz == null){
                       throw new ClassNotFoundException(name);
                   }
                   return clazz;
               }
               
               @Override
               protected Class<?> findClass(String name) throws ClassNotFoundException {
                   // 自定义逻辑：读取加密class文件、解密字节码
                   byte[] classBytes = readAndDecryptClassBytes(name);
                   if(classBytes == null){
                       throw new ClassNotFoundException(name);
                   }
                   // 生成Class对象
                   return defineClass(name, classBytes, 0, classBytes.length);
               }
               
               // 模拟读取并解密class字节码
               private byte[] readAndDecryptClassBytes(String className) {
                   // 解密、IO读取逻辑省略
                   return new byte[0];
               }
           }
           ```

       - 破坏行为说明

         - 自定义加载器加载业务类时，直接执行自身 findClass，没有向上委托父加载器，破坏双亲委派模型
         - 仅 JDK 核心类走正常委派流程，兼顾安全

   - 补充：两种破坏双亲委派的实现方式

     - 方式 1：重写 ClassLoader#loadClass ()（彻底破坏，上面 4 个场景主流实现）
       - JDK 默认 ClassLoader 的 loadClass () 原生实现就是双亲委派逻辑：
         - 检查缓存是否已加载；
         - 未加载则调用父加载器 loadClass
         - 父加载器失败，调用自身 findClass
       - 重写 loadClass，删除「调用父加载器」的逻辑，直接自己加载类，直接破坏委派
     - 方式 2：使用线程上下文类加载器（TCCL，SPI 专属，无重写 loadClass）
       - 不修改原生 loadClass 方法，利用线程上下文加载器，让上层父加载器可以获取下层子加载器，间接绕过双亲委派，属于**软性破坏**

   - 破坏双亲委派带来的风险（必记）

     - 双亲委派的核心作用是安全 + 类唯一，破坏后会丢失这两层保障：

       - 类型转换异常风险

         - 同一个全限定名类，被多个不同类加载器加载，会生成多个独立 Class 对象，互相不能强转：ClassCastException: com.demo.User cannot be cast to com.demo.User

       - 安全漏洞风险

         - 若自定义加载器无过滤逻辑，恶意代码自定义`java.lang.String`等核心类，替换原生 JDK 类，篡改底层逻辑。

           解决方案：自定义加载器中过滤`java.*`、`javax.*`包，核心类强制交给父加载器加载

       - 内存泄漏风险

         - 热部署框架频繁创建自定义类加载器，旧加载器、旧 Class、静态对象无法被 GC 回收，长期运行内存持续上涨

### 模块2：运行时数据区（JVM内存模型，面试核心）

JVM 启动后操作系统分配的内存空间，线程私有区 + 线程共享区两大类

| 内存区域                               | 线程私有 / 共享 | 内存溢出异常                          | 生命周期               |
| -------------------------------------- | --------------- | ------------------------------------- | ---------------------- |
| 程序计数器 PC 寄存器                   | 线程私有        | 无，唯一无 OOM 区域                   | 随线程创建销毁         |
| Java 虚拟机栈 虚拟机栈                 | 线程私有        | StackOverflowError / OutOfMemoryError | 随线程创建销毁         |
| 本地方法栈 Native 栈                   | 线程私有        | StackOverflowError / OutOfMemoryError | 随线程创建销毁         |
| 堆 Heap                                | 线程共享        | OutOfMemoryError Java heap space      | JVM 启动创建，关闭销毁 |
| 方法区 Method Area（元空间 Metaspace） | 线程共享        | OutOfMemoryError Metaspace            | JVM 启动创建，关闭销毁 |

1. 程序计数器（PC寄存器）

   - 作用：存储当前线程正在执行的字节码指令行号，字节码执行引擎根据计数器读取下一条指令
   - 多线程场景：CPU时间片切换时，保存线程执行断点，线程恢复后从断点继续执行
   - 唯一特性：JVM规范中唯一没有规定内存溢出的区域

2. Java虚拟机栈（虚拟机栈）

   - 每个java线程创建时，同步创建一个独立虚拟机栈，栈内存存储栈帧（Stack Frame）
   - 栈帧：方法调用的最小单位。每调用一个方法，就压入一个新栈帧；方法执行完毕后，栈帧弹出销毁
     - 栈帧内部包含5部分：
       - **局部变量表 Local Variable Table**：
         - 存储方法局部变量、方法参数，基础类型直接存值，引用类型存对象堆地址
         - 容量编译期确定，不动态扩容
       - **操作数栈 Operand Stack**
         - 字节码运算临时存储区，算术运算、对象方法传参都基于操作数栈
       - **动态链接 Dynamic Linking**
         - 存储运行时常量池符号引用，动态解析为方法直接引用
       - **方法返回地址 Return Address**
         - 方法执行结束后，回到调用该方法的代码行位置
       - **附加信息（异常表、锁记录等）**
   - 两种栈异常：
     - StackOverflowError：栈帧过多（无限递归），栈内存容量耗尽
     - OutOfMemoryError：虚拟机栈支持动态扩容，内存不足无法扩容抛出 OOM

3. 本地方法栈 Native Stack

   - 功能和虚拟机栈几乎完全一致，区别：

     - 虚拟机栈：执行 Java 字节码方法

     - 本地方法栈：执行`native`本地方法（C/C++ 编写底层方法，如`Object.wait()`、`System.arraycopy()`）。

       同样会抛出栈溢出、内存溢出异常

4. Java 堆 Heap（GC 核心区域）

   - 唯一目的：存放**所有 Java 对象实例、数组**
   - 线程共享，JVM 启动时创建，是垃圾回收器管理的核心区域，也叫 GC 堆
   - 堆细分模型（HotSpot 分代收集模型）
     - **新生代 Young Gen**：
       - 新创建对象存放区，分为 Eden 伊甸区、Survivor0（From）、Survivor1（To）
       - 对象优先分配 Eden，Eden 满触发 Minor GC，存活对象复制到空闲 Survivor
     - **老年代 Old Gen**：
       - 长期存活对象，多次 GC 未回收的对象晋升到老年代；
       - 空间不足触发 Major GC/Full GC
     - **元空间 Metaspace**：
       - JDK8 替换永久代 PermGen，属于本地内存，不再占用堆内存，存储类元数据

5. 方法区 Method Area

   - 线程共享区域，存储所有已加载类的**元数据**：类结构信息、常量池、静态变量、即时编译器编译代码

6. JDK 版本重大变更

   - JDK7 及更早：**永久代 PermGen**，放在堆内存，容易 OOM
   - JDK8 及以后：移除永久代，替换为**元空间 Metaspace**，直接使用操作系统本地内存，默认无上限，可通过`-XX:MaxMetaspaceSize`限制大小

7. 运行时常量池

   - 属于方法区子区域，每个类 class 文件自带常量池，类加载后存入运行时常量池
   - 存储字面量（字符串、数字）、符号引用
   - JDK7 优化：字符串常量池从方法区移至堆中

### 模块3：执行引擎 Execution Engine

类加载完成后，字节码交由执行引擎逐条解释执行，HotSpot 引擎包含三大执行模式：

1. 解释器 Interpreter
   - 逐行解释字节码，启动速度快，无需预热；缺点：重复执行代码会反复解释，性能差
2. 即时编译器 JIT Just-In-Time
   - 运行时监控代码执行频率，**热点代码**（循环、频繁调用方法）编译为本地机器码缓存，后续直接执行机器码，速度接近原生 C++
   - HotSpot 内置两套 JIT 编译器：
     - C1 编译器（客户端编译器）：编译速度快，优化简单，适合桌面程序
     - C2 编译器（服务端编译器）：深度优化，生成高性能机器码，后端服务器默认启用
3. 模板解释器 + 分层编译
   - JDK 默认分层编译：先 C1 快速编译，代码热度提升后交由 C2 深度优化，平衡启动速度和运行性能

### 模块4：本地方法接口JNI

JNI（Java Native Inteface），作为 Java 层与底层操作系统 C/C++ 代码的桥梁

作用：

1. 调用操作系统底层硬件资源、系统 API
2. 实现`native`本地方法，例如线程操作、文件 IO、内存操作、垃圾回收底层逻辑
3. 支持 C/C++ 调用 Java 代码，双向互通

### 模块5：本地方法库Native Library

操作系统动态链接库（Windows dll、Linux so、Mac dylib），存放所有 native 方法底层 C/C++ 实现，由本地方法接口调用

## 二、垃圾回收GC（JVM核心重难点）

### GC核心目标

自动识别堆中**死亡对象**（无任何有效引用指向），释放堆内存，无需开发者手动释放内存（对比 C/C++ malloc/free）

### 对象存活判定算法

1. 引用计数算法（主流 JVM 不使用）
   - 原理：每个对象维护引用计数器，引用 + 1，引用失效 - 1；计数器 = 0 判定为死亡
   - 致命缺陷：**循环引用无法回收**，两个对象互相持有引用，计数器永远不为 0，内存泄漏
2.  可达性分析算法（HotSpot 默认）
   - 核心概念：**GC Roots 根对象**，作为存活对象起点，从 GC Roots 向下遍历引用链，能遍历到的对象判定存活；无任何引用链连通 GC Roots 的对象判定死亡，可回收
   - 可作为 GC Roots 的对象类型：
     - Java 虚拟机栈中局部变量表引用的对象（线程局部对象）
     - 本地方法栈 JNI 引用的本地对象
     - 方法区中静态变量引用对象、常量引用对象
     - 运行中活跃线程 Thread
     - 同步锁`synchronized`持有的监视器对象
     - JVM 内部全局引用（Class 对象、异常对象）

### 对象引用四大分类（强/弱/软/虚引用）

1. 强引用 Strong Reference（默认引用）

   - 普通对象赋值：`User u = new User();`

   - 代码中最普通的对象赋值，只要引用存在，GC**永远不会回收**该对象；内存溢出也不会回收

   - 手动置空引用 `obj = null`，切断所有强引用链，下次 GC 回收

   - ```java
     public class StrongRefDemo {
         public static void main(String[] args) {
             // 强引用
             User user = new User("张三");
             
             // 触发GC
             System.gc();
             System.runFinalization();
             
             // 引用还在，对象不会被回收，不为null
             System.out.println(user);
             
             // 切断强引用
             user = null;
             System.gc();
             System.runFinalization();
             
             // 引用置空，无任何强引用，对象被回收
             System.out.println(user); // null
         }
     }
     
     class User {
         private String name;
         
         public User(String name) {
             this.name = name;
         }
         
         // 对象被回收时执行
         @Override
         protected void finalize() throws Throwable {
             System.out.println("User对象被GC回收：" + name);
         }
         
         @Override
         public String toString() {
             return "User{name='" + name + "'}";
         }
     }
     ```

   - 适用场景:普通业务对象、全局变量、集合存储对象，日常 99% 代码都是强引用

2. 弱引用 WeakReference

   - WeakReference<T>

   - 只要触发 GC，无论内存是否充足，都会直接回收弱引用对象

   - ```java
     // 示例 1：基础弱引用演示
     import java.lang.ref.WeakReference;
     
     public class WeakRefDemo {
         public static void main(String[] args) {
             User user = new User("弱引用用户");
             WeakReference<User> weakRef = new WeakReference<>(user);
             
             // 切断强引用，仅保留弱引用
             user = null;
             
             System.out.println("GC前：" + weakRef.get());
             
             // 只要执行GC，弱引用直接被回收
             System.gc();
             System.runFinalization();
             
             System.out.println("GC后：" + weakRef.get()); // null
         }
     }
     ```

   - ```java
     // 示例 2：WeakHashMap 实战（开发高频场景）
     import java.util.WeakHashMap;
     
     public class WeakHashMapDemo {
         public static void main(String[] args) throws InterruptedException {
             WeakHashMap<User, String> weakMap = new WeakHashMap<>();
             User key = new User("缓存Key");
             
             // 存入map，key是弱引用
             weakMap.put(key, "缓存数据");
             System.out.println("GC前集合大小：" + weakMap.size()); // 1
             
             // 切断强引用，只剩WeakHashMap内部弱引用
             key = null;
             
             System.gc();
             Thread.sleep(1000);
             
             // key被回收，entry自动清除，size变为0
             System.out.println("GC后集合大小：" + weakMap.size()); // 0
         }
     }
     ```

   - 适用场景：`WeakHashMap`（key 为弱引用，key 无其他引用时自动清除键值对）、临时缓存

3. 软引用 SoftReference

   - SoftReference<T>

   - 内存充足时不回收；

   - 堆内存即将溢出 OOM 前，触发 GC 回收所有软引用对象

   - 搭配 `ReferenceQueue` 可以监听对象回收状态

   - ```java
     import java.lang.ref.ReferenceQueue;
     import java.lang.ref.SoftReference;
     
     public class SoftRefDemo {
         public static void main(String[] args) {
             User user = new User("软缓存用户");
             ReferenceQueue<User> queue = new ReferenceQueue<>();
             
             // 创建软引用，绑定引用队列
             SoftReference<User> softRef = new SoftReference<>(user, queue);
             
             // 切断强引用，只剩软引用
             user = null;
             
             // 内存充足，GC不会回收
             System.gc();
             System.out.println("GC后获取软引用对象：" + softRef.get());
             
             // 模拟内存吃满，触发OOM前回收软引用
             try {
                 // 疯狂创建大对象占满堆内存
                 byte[] bigMem = new byte[1024 * 1024 * 1024];
             } catch (OutOfMemoryError e) {
                 System.out.println("内存溢出，软引用对象已被回收");
             }
             
             // 内存不足，软引用对象被回收，get()返回null
             System.out.println("内存耗尽后获取软引用对象：" + softRef.get());
     
         }
     }
     ```

   - 适用场景：缓存（图片缓存、本地数据缓存），内存够用就保留，内存不够自动清空缓存防止 OOM

4. 虚引用 PhantomReference

   - PhantomReference<T>

   - 最弱引用，无法通过虚引用获取对象实例，`get()` 方法永远返回 `null`，**无法获取到原对象**

   - 必须配合 `ReferenceQueue` 使用，无队列则无任何意义

   - 唯一作用：对象被 GC 回收时，会把虚引用放入绑定的 `ReferenceQueue`，开发者可以收到回收通知

   - ```java
     import java.lang.ref.PhantomReference;
     import java.lang.ref.Reference;
     import java.lang.ref.ReferenceQueue;
     
     public class PhantomRefDemo {
         public static void main(String[] args) throws InterruptedException {
             User user = new User("虚引用对象");
             ReferenceQueue<User> queue = new ReferenceQueue<>();
             
             // 创建虚引用，必须绑定队列
             PhantomReference<User> phantomRef = new PhantomReference<>(user, queue);
             
             // 虚引用get永远返回null，无法拿到对象
             System.out.println("虚引用get()：" + phantomRef.get()); // null
             
             // 切断强引用
             user = null;
             
             // 触发GC
             System.gc();
             System.runFinalization();
             Thread.sleep(500);
             
             // 从队列取出虚引用，代表对象已经彻底被回收
             Reference<?> ref = queue.poll();
             if (ref != null) {
                 System.out.println("收到对象回收通知，可释放堆外资源");
             }
         }
     }
     ```

   - 适用场景：堆外内存（DirectBuffer）回收监控、资源释放监听、对象销毁后置处理

### 分代垃圾回收机制

HotSpot 根据对象存活生命周期不同，将堆划分为新生代、老年代，使用不同回收算法，提升 GC 效率

1. 新生代 Young Gen
   - 绝大多数对象朝生夕灭，生命周期极短；采用**复制算法**，内存划分为一块 Eden、两块相等 Survivor（From/To）
   - 新对象全部分配 Eden 区
   - Eden 空间占比 80%，两个 Survivor 各 10%
   - Minor GC：Eden 填满触发，存活对象复制到空闲 To Survivor，清空 Eden 和原 From 区
   - 对象年龄：每熬过一次 Minor GC 年龄 + 1，年龄阈值（默认 15）晋升老年代
2. 老年代 Old Gen
   - 存放长期存活、大体积数组 / 对象；对象存活率高，复制算法开销巨大，采用**标记 - 清除、标记 - 整理**算法
   - Major GC：老年代内存不足触发，回收整个老年代
   - Full GC：新生代 + 老年代 + 元空间全部回收，STW 停顿时间最长，生产环境尽量避免

### 三大垃圾回收基础算法

1. 复制算法 Copying
   - 将内存对半划分，仅使用其中一块；GC 时存活对象复制到空白区域，清空使用区；无内存碎片；代价：浪费一半内存，适合低存活新生代。
2. 标记 - 清除 Mark-Sweep
   - 第一步标记死亡对象；第二步统一清除回收；优点：无需内存复制；缺点：产生大量不连续内存碎片，大对象无法分配
3. 标记 - 整理 Mark-Compact
   - 标记死亡对象后，将所有存活对象向内存一端压缩移动，清空边界外内存；无内存碎片，适合老年代；缺点：移动对象成本高，STW 停顿更长

### HotSpot主流垃圾收集器

1. 新生代收集器
   - Serial：串行单线程收集器，GC 时暂停所有用户线程（STW），客户端小程序使用
   - Parallel Scavenge：并行多线程新生代收集器，侧重**吞吐量**（运行代码时间 / 总时间），后端服务器默认搭配 Parallel Old 老年代收集器
   - ParNew：并行新生代收集器，侧重低停顿，唯一可与 CMS 老年代收集器配合
2. 老年代收集器
   - Serial Old：串行老年代收集器，单线程标记整理
   - Parallel Old：并行老年代收集器，搭配 Parallel Scavenge，吞吐量优先
   - CMS（Concurrent Mark Sweep 并发标记清除）
     - 第一款并发低停顿收集器，GC 大部分阶段与用户线程并发执行，减少 STW
     - 缺陷：标记清除产生内存碎片、并发浮动垃圾、内存占用高，JDK14 正式废弃
   - G1（Garbage-First 垃圾优先收集器，JDK9 默认）
     - 分区式收集器，将整个堆划分为多个相等独立 Region，不再严格区分新生代老年代
     - 可自定义预期停顿时间，优先回收垃圾最多的 Region
     - 兼顾吞吐量与低停顿，替代 CMS
   - ZGC / Shenandoah 低延迟收集器（JDK11+）
     - 几乎无 STW（亚毫秒级停顿），超大堆内存场景（TB 级堆）使用，金融、低延迟系统专用

### STW Stop-The-World世界暂停

GC 执行期间，**所有 Java 用户线程全部冻结暂停**，只有 GC 线程工作，这个现象称为 STW

1. Serial/Parallel 收集器全程 STW
2. CMS/G1/ZGC 仅初始标记、最终标记短暂 STW，其余阶段并发执行，大幅降低停顿时间
3. 生产调优核心目标：减少 STW 停顿时长、降低 Full GC 频率



## 三、类加载、内存、GC 配套调优参数（常用 JVM 参数）

1. 堆内存基础参数

   ```java
   -Xms2g  // 堆初始内存2G
   -Xmx2g  // 堆最大堆内存2G，Xms=Xmx避免运行时扩容抖动
   -Xmn500m // 新生代总内存500M
   -XX:SurvivorRatio=8 // Eden:Survivor比例8:1:1
   ```

2. 元空间参数

   ```java
   -XX:MetaspaceSize=128m // 元空间初始容量
   -XX:MaxMetaspaceSize=512m // 元空间最大上限
   ```

3. GC 收集器切换参数

   ```java
   -XX:+UseParallelGC // Parallel Scavenge + Parallel Old
   -XX:+UseParNewGC -XX:+UseConcMarkSweepGC // ParNew + CMS
   -XX:+UseG1GC // 启用G1收集器（JDK9默认）
   -XX:+UseZGC // JDK11+ ZGC低延迟收集器
   ```

4. GC 日志调试参数

   ```java
   -XX:+PrintGCDetails  // 打印GC详细日志
   -XX:+PrintGCTimeStamps // 打印GC时间戳
   -Xloggc:/logs/gc.log // GC日志输出文件路径
   ```

   

## 四、JVM 完整代码执行链路演示

1. 开发者编写User.java源码
2. javac User.java编译为跨平台User.class字节码
3. Java程序启动，JVM调用Application类加载器加载User等
4. 类加载执行加载、链接、初始化三步，静态变量、静态代码块执行
5. 主线程执行new User()，对象分配至堆Eden区，栈帧局部变量表存储对象引用
6. 调用对象方法，虚拟机栈压入新栈帧，执行字节码
7. Eden内存占满触发MinorGC，可达性分析标记存活对象，复制至Survivor区，清空Eden
8. 长期存活对象晋升老年代，老年代空间不足触发Full GC,STW暂停业务线程回收内存
9. 程序运行结束，JVM进程退出，操作系统回收全部JVM内存资源

## 五、JVM 经典高频面试核心问题总结

1. JVM 运行时数据区分哪几块，哪些线程私有、共享？各自 OOM 类型？

   ```
   分为五大块：程序计数器、虚拟机栈、本地方法栈、Java堆、方法区（元空间）；
   1. 程序计数器：PC寄存器，线程私有，无OOM，JVM中唯一不会内存溢出的空间
   2. Java虚拟机栈：线程私有，StackOverflowError（栈帧过多，栈容量固定耗尽，无限递归）和OutOfMemoryError（虚拟机栈支持动态扩容，操作系统无剩余内存分配栈）
   3. 本地方法栈：线程私有，和虚拟机栈完全一致（StackOverflowError, OOM）
   4. Java堆Heap:线程共享，OutOfMemoryError（Java heap space，堆内存耗尽无法创建对象）
   5. 方法区（JDK8 元空间Metaspace）： 线程共享，OutofMemoryError: Metaspace（存储类元数据内存耗尽）
   ```

   

2. 双亲委派模型工作流程、作用，哪些场景会破坏双亲委派？

   ```
   工作流程：
       1. 子加载器收到类加载请求，不会自行加载，优先向上委派给父加载器
       2. 父加载器持续向上委派，知道顶层的Bootstrap启动类加载器
       3. Bootstrap尝试加载类，加载成功直接返回Class对象
       4. 顶层父加载器找不到目标，请求逐层退回，由发起请求的子加载器自行加载
       
   两大核心作用：
   	1. 安全防护：防止自定义java.lang.String等JDK核心类覆盖原生类，篡改底层逻辑
   	2. 保证类全局唯一：同一个全限定名类仅加载一次，避免多个Class对象引发ClassCastException类型转换异常
   	
   四大破坏场景：
   	1. SPI机制（JDBC、SLF4J）:上层Bootstrap加载的接口需要调用下层App加载器的实现类，父加载器看不到到子加载器；通过TCCL（线程上下文类加载器）绕过委派，直接使用子加载器加载实现类
   	2. 热部署框架（Spring DevTools、JRebel）：AppClassLoader会缓存加载过的类，无法重复加载修改后的class;自定义类加载器重写loadClass，业务类不向上委派，直接读取最新字节码，销毁重建加载器实现热替换
   	3. OSGi模块化容器：OSGi多个Bundle为平级模块，互相依赖调用；放弃树状双亲委派，使用网状委派，优先委派给以来的平级Bundle加载器
   	4. 加密class / 远程Jar自定义加载器：class加密、远程网络读取Jar，系统加载器无法处理；重写loadClass，业务类跳过父加载器委派，自定义解密 / 网络IO读取字节码
   ```

   

3. CMS 和 G1 收集器的区别，CMS 存在什么缺陷？

   ```
   一、CMS 与 G1 核心区别
   1. 堆内存模型
   	CMS：严格划分新生代、老年代连续内存
   	G1：将整个堆切分为多个大小相等的 Region，不再严格区分新生代老年代，Region 可动态充当新生代 / 老年代
   2. 回收策略
   	CMS：只回收老年代，新生代必须搭配 ParNew 使用
   	G1：统一回收整个堆，可独立完成新生代 + 老年代回收
   3. 停顿控制
   	CMS：停顿时间不可控，老年代越大，STW 停顿越长
   	G1：支持用户设置预期最大停顿时间，优先回收垃圾占比最高的 Region，可控低延迟
   4. 内存碎片处理
   	CMS：标记 - 清除算法，全程不移动对象，长期运行产生大量内存碎片
   	G1：每次 GC 会对存活对象局部压缩整理，减少内存碎片
   5. Full GC 触发概率
   	CMS：极易因并发失败、内存碎片分配失败触发 Full GC
   	G1：碎片少、分区分配灵活，Full GC 触发频率大幅降低
   	
   二、CMS 四大核心缺陷
   1. 产生大量内存碎片：采用标记清除算法，不会移动压缩对象，老年代碎片化严重，大对象无法分配，频繁触发 Full GC
   2. 存在浮动垃圾：并发标记阶段用户线程同时创建新对象，新产生的垃圾本轮 GC 无法回收，只能留到下一次 GC
   3. 并发模式失败：并发清除阶段，老年代剩余空间不足以存放并发过程中新生成的对象，JVM 直接停止并发，触发单线程 Full GC，长时间 STW
   4. 堆内存占用高：CMS 预留一部分内存用于并发阶段新对象分配，不能等到老年代完全占满才 GC，内存利用率低于 G1
   ```

   

4. 可达性分析 GC Roots 包含哪些对象？

   ```
   可达性分析是 HotSpot 判断对象存活的算法，从 GC Roots 向下遍历引用链，能到达的对象存活。
   可作为 GC Roots 的对象：
   	1.Java 虚拟机栈中局部变量表引用的对象（线程局部变量、方法参数）
   	2.本地方法栈中 JNI（Native 方法）引用的对象
   	3.方法区中静态变量、常量引用的对象
   	4.当前 JVM 内所有活跃运行的 Thread 线程
   	5.synchronized 同步锁持有的监视器（锁）对象
   	6.JVM 内部全局引用：Class 类对象、系统异常对象、内置类加载器等
   ```

   

5. 四种引用区别，各自使用场景？

   ```
   1.强引用 StrongReference
   	规则：普通对象赋值引用，只要强引用链存在，GC 永远不会回收对象，内存溢出也不会清理
   	场景：日常业务中 99% 普通对象、局部变量、全局实体对象
   2.弱引用 WeekReference
   	规则：只要触发 GC（无论堆内存是否充足），弱引用指向的对象立刻被回收
   	场景：WeakHashMap（key 为弱引用，key 无外部强引用自动清理键值对）、短期临时缓存
   3.软引用 SoftReference
   	规则：内存充足时 GC 不回收；堆内存即将 OOM、内存耗尽前，一次性回收所有软引用对象；可搭配引用队列监听回收
   	场景：图片缓存、本地临时数据缓存，内存够用保留缓存，内存不足自动释放防止 OOM
   4.虚引用 PhantomReference
   	规则：get()方法永远返回 null，无法获取原始对象；唯一作用：对象被彻底回收后，虚引用会进入绑定的ReferenceQueue，程序可收到对象销毁通知；必须配合引用队列使用；
   	场景：堆外内存 DirectBuffer 资源释放监控、对象销毁后的后置资源清理。
   ```

   

6. Minor GC、Major GC、Full GC 三者区别，触发条件？

   ```
   1.Minor GC（新生代 GC）
   	范围：仅回收 Eden 区 + Survivor 新生代
   	触发条件：Eden 区域内存填满，自动触发
   	特点：回收速度快，STW 停顿时间短，频繁执行
   2.Major GC（老年代 GC）
   	范围：只回收老年代；
   	触发条件：老年代内存空间不足
   	特点：停顿时间远长于 Minor GC，通常伴随一次 Minor GC 一起执行
   3.Full GC（整堆完全回收）
   	范围：回收新生代 + 老年代 + 元空间，整堆回收
   	触发条件：
   		1.手动调用System.gc()
   		2.老年代内存耗尽
   		3.元空间 Metaspace 内存占满
   		4.CMS 并发模式失败、内存碎片导致空间分配担保失败
   	特点：全局长时间 STW，业务线程全部暂停，生产环境需要极力避免
   ```

   

7. 标记清除、复制、标记整理三种 GC 算法优缺点、适用区域？

   ```
   1.复制算法 Copying
   	实现：将内存划分为两块同等大小空间，仅使用其中一块；GC 时把存活对象复制到空白区域，清空当前使用内存
   	优点：无内存碎片，回收效率高
   	缺点：永久浪费 50% 堆内存，内存利用率低
   	适用区域：新生代（对象存活率极低，复制成本小）
   2.标记 - 清除 Mark-Sweep
   	实现：第一步标记所有死亡对象；第二步统一清除回收死亡对象
   	优点：无需复制移动对象，内存利用率 100%
   	缺点：回收完成后产生大量不连续内存碎片，大对象无法分配
   	适用区域：老年代（CMS 收集器使用）
   3.标记 - 整理 Mark-Compact
   	实现：先标记死亡对象；再将全部存活对象向内存一端移动压缩，清空边界外空闲内存
   	优点：无内存碎片，不存在大对象分配失败问题
   	缺点：移动大量存活对象，开销极大，STW 停顿时间很长
   	适用区域：老年代（Serial Old、Parallel Old 收集器使用）
   ```

   

8. JDK8 永久代替换元空间的原因？

   ```
   1.永久代存在固定内存上限，极易 OOM
   	JDK7 及之前 PermGen 永久代属于堆内存一部分，有固定上限；大量类、动态代理、反射场景会持续占用永久代内存，频繁抛出java.lang.OutOfMemoryError: PermGen space
   	元空间使用操作系统本地内存，默认无上限，大幅减少元数据内存溢出
   2.简化 JVM 内存模型，降低调参难度
   	永久代需要单独配置-XX:PermSize/-XX:MaxPermSize；JDK8 移除永久代后，仅需配置元空间参数，内存划分逻辑更简洁
   3.类元数据生命周期更贴合本地内存
   	类元数据仅加载类时使用，生命周期和堆中业务对象完全无关；放到操作系统本地内存，堆内存仅存储业务对象，内存隔离，互不挤占
   4.JDK7 铺垫优化，字符串常量池移出永久代
   	JDK7 已经将字符串常量池从永久代移至 Java 堆，永久代功能持续弱化，JDK8 彻底删除永久代，统一使用 Metaspace 存储类元数据
   ```

   

9. STW 是什么，哪些 GC 阶段会产生 STW？

   ```
   STW 定义：
   	STW 全称 Stop-The-World（世界暂停），GC 执行过程中，所有 Java 业务用户线程全部冻结暂停，只有 GC 专用线程运行，业务代码完全停止执行。STW 时间越长，接口、业务响应延迟越高
   	
   各收集器 STW 分布：
   	1.Serial/Parallel 收集器：GC 全过程全程 STW，所有阶段暂停用户线程
   	2.CMS 收集器四阶段 STW
   		2.1 初始标记：短暂 STW，标记 GC Roots 直接关联对象
   		2.2 并发标记：无 STW，GC 与用户线程并发执行
   		2.3 重新标记：短暂 STW，修正并发标记期间引用变更产生的标记误差
   		2.4 并发清除：无 STW，后台清理死亡对象
   	3.G1/ZGC 低延迟收集器
   		仅初始标记、重新标记极短时间 STW，其余 GC 阶段均和业务线程并发，亚毫秒级停顿
   ```

   

10. JIT 即时编译器原理，分层编译作用？

    ```
    JIT 即时编译器原理：
    	JIT 全称 Just-In-Time 即时编译
    	HotSpot 执行字节码有两套执行单元：解释器、JIT 编译器：
    		1.程序启动初期，解释器逐行解释字节码执行，启动速度快
    		2.JVM 持续监控代码执行热度，循环、频繁调用的方法会被判定为热点代码
    		3.JIT 编译器将热点字节码编译为当前操作系统、CPU 适配的本地机器码
    		4.编译后的机器码缓存，后续再次执行该方法时，直接运行机器码，无需重复解释，执行速度接近原生 C/C++ 程序
    		
    	HotSpot 两套 JIT 编译器：
    		1.C1（客户端编译器）：编译速度快，基础优化，适合桌面程序
    		2.C2（服务端编译器）：编译耗时更长，深度全局优化，生成高性能机器码，后端服务默认启用
    		
    分层编译作用：
    	分层编译是 JDK 默认开启的编译策略，融合解释器、C1、C2 编译器，平衡启动速度和长期运行性能，解决单一编译器短板：
    		1.第 0 层：解释器直接执行字节码，快速启动程序，同时采集代码执行统计数据
    		2.第 1 层：C1 简单编译，轻度优化，响应中等热度代码，停顿短
    		3.第 2/3 层：C1 采集更多性能统计信息，为深度优化提供数据
    		4.第 4 层：代码达到极高热度，使用 C2 编译器深度优化，生成极致高效的机器码
    		
    	分层编译优势：
    		1.避免纯 C2 编译启动慢的问题，程序冷启动速度快
    		2.低热度代码仅轻度编译，节省编译 CPU 资源
    		3.高频热点代码深度优化，长期运行吞吐量极高
    ```

    

