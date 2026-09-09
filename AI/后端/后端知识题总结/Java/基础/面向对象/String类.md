- 基本特性
  - `String`**是`fianl`类，不能继承**
  - 不可变：**改内容实际是新建对象**，原对象不变
  - 底层：`Java9`以前多是`char[]`，`Java9+`多为`byte[]` + `coder(Latin-1 / UTF-16)`
  - 比内容用`equals`
  
- 创建方式

  - ```java
    String a = "abc"; //字面量创建，走字符串常量池
    String b = new String("abc"); // 堆上创建新对象，常量池里可能还有一份字面量。
    ```

- 字符串常量池

  - 字面量`abc`优先复用常量池中已有对象，省内存
  - `new String("abc")`一般会多一个堆对象
  - `JDK7+`常量池在**堆（不在永久代）**；和`IntegerCache`不是一回事，但都是**缓存复用**的思路

- `String `/ `StringBuilder `/ `StringBuffer`核心差别是可变性，线程安全，性能场景

  - 可变性：
    - `String`不可变，
    - `StringBuilder `和`StringBuffer`可变
  - 线程安全：
    - `String`线程安全，
    - `StirngBuilder`线程不安全，
    - `StringBuffer`线程安全，因为它方法通过`synchronized`实现同步
  - 性能：
    - `String`性能最低，频繁修改字符串时会生成大量临时对象，增加内存开销和垃圾回收压力。
    - `StringBuilder` 性能最高，因为它没有线程安全的开销，适合单线程下的字符串操作。
    - `StringBuilder` 性能最高，因为它没有线程安全的开销，适合单线程下的字符串操作。
  - 使用场景：
    - 如果字符串内容固定或不常变化，优先使用 `String`
    - 如果需要频繁修改字符串且在单线程环境下，使用 `StringBuilder`。
    - 如果需要频繁修改字符串且在多线程环境下，使用 `StringBuffer`

- 常用方法

  - `length`
  - `isEmpty`
  - `charAt`
  - `substring`
  - `indexOf` / `contains`
  - `startsWith` / `endsWith`
  - `replace` / `replaceAll`
  - `split` 
  - `trim` / `strip`
  - `toLowerCase` / `toUpperCase`
  - `valueOf`
  - `format`
  - `getBytes`
  - `equals` / `equalsIgnoreCase`
  - `compareTo`

- 