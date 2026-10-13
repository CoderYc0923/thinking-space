# OOM 相关面试题

## 1. `OutOfMemoryError: Java heap space` 和 `Metaspace` 的区别？

| | **Java heap space** | **Metaspace** |
|--|---------------------|---------------|
| 爆的是哪块内存 | **堆 Heap** | **元空间 Metaspace**（JDK8+ 方法区实现，本地内存） |
| 存什么 | 对象实例、数组等业务数据 | 类的元数据：Class 结构、方法信息、常量池、注解等 |
| 典型原因 | 内存泄漏（集合/缓存只增不减）、堆过小、大对象/一次加载过多 | 类加载过多且无法卸载：动态代理、热部署、CGLIB、脚本引擎反复生成类；或 `MaxMetaspaceSize` 过小 |
| 常见参数 | `-Xms` / `-Xmx` | `-XX:MetaspaceSize` / `-XX:MaxMetaspaceSize` |
| 排查重点 | Heap Dump（`.hprof`）→ MAT 看 Dominator Tree、Path to GC Roots | 类直方图、ClassLoader 是否泄漏；不一定靠普通业务对象 dump 一眼看穿 |
| 和本次 lab 关系 | diagnostic-lab 的 memory 场景就是这种 | lab 未覆盖；要用动态生成类等方式另造 |

**一句话**：  
`Java heap space` = **对象太多/收不掉**；`Metaspace` = **类元数据太多/卸不掉**。  
堆里对象再多，一般也不会直接打出 Metaspace OOM；反过来，Metaspace 满了，堆可能看起来还很空。

**口述补充**：

- JDK7 及以前方法区多用永久代 `PermGen`，报错常是 `PermGen space`；JDK8 起换成 Metaspace，移出堆，用本地内存，默认可随需要扩张，但仍可被 `MaxMetaspaceSize` 限制，也可能把机器物理内存吃光。
- 看到 OOM 先读完整异常名，再决定是抓堆 dump，还是查类加载/ClassLoader 泄漏。

---

## 2. 为什么 dump 比「把 `-Xmx` 调大」更重要？

（待补）

## 3. GC Roots 有哪些？

（待补：栈局部变量、静态变量、活跃线程等）
