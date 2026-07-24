# 1. 前置认知：Java 与 JS 核心差异（前端快速理解）

表格

|    维度    |                             Java                             |                   JavaScript                   |
| :--------: | :----------------------------------------------------------: | :--------------------------------------------: |
|  语言类型  |       **强静态类型**，声明必须指定类型，编译期校验类型       |     弱动态类型，变量无固定类型，运行时报错     |
|  运行环境  |   JVM 虚拟机，先编译.class 再运行；跨平台一次编译到处运行    |     浏览器 V8/Node.js，解释执行，无需编译      |
|  线程模型  |                多线程并发，手动处理线程安全锁                |      单线程事件循环，异步靠回调 / Promise      |
|  面向对象  | 纯面向对象，一切皆对象（除 8 大基本类型），类、继承、接口规范 | 原型式面向对象，无原生接口，ES6 class 是语法糖 |
| 变量作用域 |          类成员变量、局部变量、静态变量，作用域严格          |     var/let/const，存在变量提升、全局污染      |
|    容器    |             List/Set/Map 严格区分，泛型约束类型              |       Array、Object，任意类型混存无约束        |
|    函数    |     不能独立存在，必须依附类 / 接口（Java8 Lambda 除外）     |       一等公民，可单独定义、作为参数传递       |

关键记忆：JS 是脚本弱类型，Java 是编译强类型；JS 靠原型，Java 靠类继承 + 接口。

------

# 2. 基础语法

## 2.1 变量与常量

### 变量

- Java 变量必须**先声明类型再赋值**，不能像 JS `let a = 1` 省略类型

```
int age = 18; // 正确
age = 20;     // 可二次修改
```

### 常量 final

```
final` 修饰变量，只能赋值一次，不可修改，类比 JS `const
```

```
final double PI = 3.1415;
PI = 3; // 编译报错，常量不能修改
```

### 变量分类

1. **成员变量**：定义在类中，方法外；有默认初始值（int=0，String=null）
2. **局部变量**：定义在方法 / 代码块内；**无默认值，使用前必须手动赋值**（JS 无此限制）
3. **静态变量 static**：属于类，全局唯一，所有对象共享

## 2.2 运算符（补充原文缺失）

1. 算术：

   ```
   + - * / % ++ --
   ```

   - 注意：`int 5 / 2 = 2` 整数相除舍去小数；JS `5/2=2.5`

2. 赋值：`= += -= *= /=`

3. 比较：

   ```
   > < >= <= == !=
   ```

   - `==` 基本类型比值，引用类型比地址；JS `==` 会隐式类型转换

4. 逻辑：`&& || !`（短路特性同 JS）

5. 三元运算符：`条件 ? 成立值 : 失败值` 用法和 JS 完全一致

6. 位运算符：`& | ^ ~ << >> >>>`（JS 很少用到，后端高频）

## 2.3 8 大基本数据类型（强类型核心）

口诀：四整两浮一字符一布尔

|  类型   | 字节 |               取值要点               |          JS 对应           |
| :-----: | :--: | :----------------------------------: | :------------------------: |
|  byte   |  1   |               -128~127               | 无对应，JS 数字统一 Number |
|  short  |  2   |             -32768~32767             |             -              |
|   int   |  4   |           常用整数默认类型           |           Number           |
|  long   |  8   |     数值末尾加 L `long l = 100L`     |             -              |
|  float  |  4   |     小数末尾加 f `float f=3.14f`     |             -              |
| double  |  8   |             小数默认类型             |           Number           |
|  char   |  2   | 存储单个字符，支持中文 `char c='中'` |       String 单字符        |
| boolean | 1 位 |   只有 true/false，不能用 0/1 代替   |          Boolean           |

> JS 坑对比：JS 数字不分长短整型，全部浮点数；Java 严格区分，超出范围会溢出。

## 2.3.9 BigDecimal

- 为什么需要BigDecimal?

  - 浮点数精度丢失问题（计算机底层二进制存储小鼠，float/double都会出现精度丢失）

    - ```java
      // 0.1 + 0.2 问题
      System.out.println(0.1 + 0.2); // 输出：0.30000000000000004
      ```

    - 所以金融、金额、计费场景却对不能用double/float，必须使用BigDecimal精确运算

  - BigDecimal定位

    - java.math.BigDecimal：不可变高精度十进制运算类，专门处理金额、小数精确计算

  - ```java
    // 字符串构造（无精度丢失）
    BigDecimal num1 = new BigDecimal("0.1");
    BigDecimal num2 = new BigDecimal("0.2");
    System.out.println(num1.add(num2)); // 0.3
    
    // 禁止double直接构造（原生精度丢失会被带入）
    
    // 静态常量（0，1，10，复用对象）
    BigDecimal zero = BigDecimal.ZERO;
    BigDecimal one = BigDecimal.ONE;
    BigDecimal ten = BigDecimal.TEN;
    
    // valueOf静态方法（底层转字符串，安全）
    BigDecimal num = BigDecimal.valueOf(0.1);
    ```

  - 核心运算方法（所有方法返回新对象，自身不可变）

    - BigDecimal不可变，加减乘除不会修改原对象，必须接收返回值

    - ```java
      BigDecimal a  = new BigDecimal("0.1");
      BigDecimal b = new BigDecimal("0.2");
      // 加
      BigDecimal sum = a.add(b);
      // 减
      BigDecimal sub = b.subtract(a);
      // 乘
      BigDecimal mul = a.multiply(b);
      // 除（BigDecimal,保留位数，舍入模式）
      // 必须执行保留位数 + 舍入模式，不然遇到无限循环小数，直接抛出ArithmeticException算术异常
      // 舍入模式：ROUND_HALF_UP（四舍五入，业务金额最常用）；ROUND_DOWN（直接截断，舍弃后面小数）；ROUND_UP（无论后面多少直接进 1）；ROUND_HALF_EVEN（银行家舍入，5 前偶数舍弃、奇数进 1）
      BigDecimal div = a.divide(b, 3, BigDecimal.ROUND_HALF_UP)
      // 取绝对值 .abs()
      // 取相反数 .negate()
      // 取余 .remainder()
      ```

    - 大小比较用compareTo，不用 == 或 equals

      - compareTo () 推荐（忽略小数末尾多余 0）
      - equals () 会对比小数位数，极易踩坑
      - == 比较对象地址，完全不适用

    - 小数点、缩放操作

      - `setScale(位数, 舍入模式)`：设置保留小数
      - `movePointLeft(n)`：小数点左移 n 位（除以 10^n）
      - `movePointRight(n)`：小数点右移 n 位（乘以 10^n）

    - 类型转换

      - doubleValue()
      - intValue()
      - toString() 
      - 转数字推荐：String 无精度丢失

    - 工具封装类

      - ```java
        import java.math.BigDecimal;
        import java.math.RoundingMode;
        
        public class BigDecimalUtil {
            // 默认保留2位小数，四舍五入
            private static final int SCALE = 2;
        
            // 加
            public static BigDecimal add(BigDecimal a, BigDecimal b) {
                return a.add(b).setScale(SCALE, RoundingMode.HALF_UP);
            }
            // 减
            public static BigDecimal sub(BigDecimal a, BigDecimal b) {
                return a.subtract(b).setScale(SCALE, RoundingMode.HALF_UP);
            }
            // 乘
            public static BigDecimal mul(BigDecimal a, BigDecimal b) {
                return a.multiply(b).setScale(SCALE, RoundingMode.HALF_UP);
            }
            // 除
            public static BigDecimal div(BigDecimal a, BigDecimal b) {
                return a.divide(b, SCALE, RoundingMode.HALF_UP);
            }
        }
        ```

​	

## 2.4 引用数据类型

类、接口、数组、String、包装类、集合等；变量存储**对象内存地址**，而非真实值。

## 2.5 类型转换

### 自动转换（隐式，小范围→大范围，安全）

```
byte→short→int→long→float→double
```

```
int a = 10;
double b = a; // 自动转，无精度丢失
```

### 强制转换（显式，大范围→小范围，丢失精度风险）

```
double d = 3.99;
int num = (int)d; // num=3，小数直接截断
```

### 字符串拼接特殊转换

任意类型和`String`用`+`拼接，自动转为字符串，和 JS 一致

```
int x = 10;
String s = x + "java"; // "10java"
```

## 2.6 值传递（面试必考点，对比 JS）

Java**只有值传递**，不存在引用传递：

1. 基本类型：传递变量副本，方法内修改不影响外部
2. 引用类型：传递**地址副本**，修改对象内部属性会影响外部；但重新赋值对象不影响外部

```
// 示例
public void change(int num, User u) {
    num = 100; // 基本类型副本，外部不变
    u.name = "李四"; // 修改地址指向的对象，外部同步变
    u = new User(); // 仅修改副本地址，外部对象不变
}
```

JS 对比：JS 函数传参规则和 Java 完全一致，同样是值传递。

------

# 3. 流程控制

## 3.1 分支语句

### if-else 用法和 JS 完全一致

### switch 分支

支持：byte/short/int/char、String、Enum；**不支持 long、浮点**（JS switch 任意类型）

必须加`break`，否则穿透；`default`兜底

```
String week = "周一";
switch(week) {
    case "周一":
        System.out.println("上班");
        break;
    default:
        System.out.println("休息");
}
```

## 3.2 循环

1. `for`：已知循环次数，语法和 JS 几乎一样
2. `while`：先判断再执行
3. `do-while`：先执行一次，再判断（JS 无原生 do while 极少用）
4. 增强 for 循环 `for(元素类型 变量 : 数组/集合)` 简化遍历，类比 JS `for...of`

## 3.3 关键字

- `break`：终止当前循环 /switch
- `continue`：跳过本次循环，进入下一轮
- `return`：结束当前方法，返回值

------

# 4. 数组与可变参数

## 4.1 数组特性

1. 长度**固定不可变**，创建时确定大小；JS 数组长度动态可变
2. 只能存放**同一种类型**数据；JS 数组可混合数字、字符串、对象
3. 下标从 0 开始，越界抛出 `ArrayIndexOutOfBoundsException`（JS 越界返回 undefined）

```
// 静态初始化
int[] arr = {1,2,3};
// 动态初始化
int[] arr2 = new int[5]; // 默认填充0
// 两种遍历
for(int i=0;i<arr.length;i++){}
for(int num : arr){} // 增强for
```

## 4.2 可变参数（补充原文缺失）

1. 方法参数 `类型...参数名`，本质是自动将传入的参数封装成对应类型的数组
2. 必须放在参数列表最后
3. 一个方法只能有一个可变参数
4. 不可传null，会报空指针异常
5. 重载时优先匹配精确传参类型再匹配可变参数
6. 泛型可变参数会产生unchecked警告

```
public static int sum(int... nums){
    int total = 0;
    for(int n : nums) total +=n;
    return total;
}

public static void main(String[] args) {
	sum(); // 不传任何参数（合法，底层是空数组）
	sum(10); // 传1个参数
	sum(10,20,30); // 传多个零散参数（任意个数，同类型即可）
	sum(new int[]{10,20,30,40}); // 直接传对应类型的数组（底层本身就是数组，直接复用）
}
```

------

# 5. 访问修饰符 + static /final/this /super

## 5.1 四大访问修饰符（面试高频）

|   修饰符    | 同类 | 同包 | 子类 | 任意包所有类 |
| :---------: | :--: | :--: | :--: | :----------: |
|   private   |  ✅   |  ❌   |  ❌   |      ❌       |
| 缺省 (不写) |  ✅   |  ✅   |  ❌   |      ❌       |
|  protected  |  ✅   |  ✅   |  ✅   |      ❌       |
|   public    |  ✅   |  ✅   |  ✅   |      ✅       |

## 5.2 static 静态关键字

修饰：变量、方法、代码块、内部类

1. 静态成员**属于类**，全局唯一，所有对象共享
2. 调用方式：`类名.静态成员`，无需 new 对象
3. 静态方法**不能直接使用 this、super、非静态变量 / 方法**（静态加载早于对象）
4. 静态代码块：类加载时执行，仅运行一次，用于初始化静态资源

## 5.3 final 关键字

1. final 变量：常量，仅赋值一次
2. final 方法：子类**不能重写**
3. final 类：**不能被继承**（String 是 final 类）

## 5.4 this & super（原文缺失重点）

### this

1. 代表当前对象
2. `this.属性`：区分成员变量和局部变量重名
3. `this(参数)`：调用本类其他构造方法，必须放在构造方法第一行

### super

1. 代表父类对象
2. `super.属性/方法`：访问父类被重写的成员
3. `super(参数)`：调用父类构造方法，默认隐含，必须首行

------

# 6. 面向对象基础：类、对象、构造、重载、重写

## 6.1 类与对象

类：模板（类比 JS 构造函数 /class）；对象：类的实例（new 出来）

Java 创建对象必须`new`，JS 可字面量`{}`快速创建对象。

## 6.2 构造方法（原文重点缺失）

1. 方法名和类名完全一致，**无返回值**
2. 创建对象时自动调用，用于初始化成员变量
3. 一个类默认有**无参构造**；自定义有参构造后，默认无参构造消失
4. `this()` / `super()` 只能写在构造第一行

```
public class User {
    // 无参构造
    public User(){}
    // 有参构造
    public User(String name){
        this.name = name;
    }
}
```

## 6.3 方法重载 Overload（同一个类内）

条件：**方法名相同，参数列表不同**（个数 / 类型 / 顺序）；和返回值、修饰符无关

类比 JS：JS 无重载，只能手动判断参数区分逻辑

## 6.4 方法重写 Override（父子类之间）

1. 子类重写父类非 private 方法
2. 方法名、参数、返回值完全一致
3. 子类访问权限不能低于父类（父 protected，子类不能 private）
4. 使用`@Override`注解校验，防止写错

重载 vs 重写区分（面试简答题）：

- 重载：同类，同名不同参，编译期绑定
- 重写：父子类，完全相同签名，运行期多态绑定

------

# 7. OOP 三大核心特性：封装、继承、多态（面试必考）

## 7.1 封装

核心：私有化成员变量`private`，对外提供 get/set 方法；

好处：控制数据合法性、隐藏内部实现、代码解耦。

```
private int age;
public void setAge(int age){
    if(age>0 && age<150) this.age=age;
}
```

## 7.2 继承 extends

1. Java**单继承**：一个类只能直接继承一个父类；JS 可通过原型链多层继承
2. 子类拥有父类非私有属性、方法
3. 构造方法不继承，子类默认调用父类无参构造`super()`
4. 避免代码复用，拓展功能

## 7.3 多态

核心定义：**父类引用指向子类对象**，调用重写方法时执行子类逻辑

```
Animal a = new Dog(); // 父引用，子对象
a.eat(); // 执行Dog重写后的eat()
```

使用`instanceof`判断实际对象类型，强制向下转型调用子类独有方法。

三大特性记忆：封装藏数据，继承复代码，多态扩功能。

------

# 8. 抽象类 Abstract vs 接口 Interface（高频对比面试）

## 8.1 抽象类 abstract class

1. 不能 new 实例；包含抽象方法（无方法体）+ 普通成员 / 方法
2. 子类必须实现全部抽象方法，否则子类也声明 abstract
3. 使用`extends`，只能单继承
4. 有构造方法、成员变量、静态变量

## 8.2 接口 interface（Java8+）

1. Java8 前：仅抽象常量、抽象方法；Java8 新增 default 默认方法、static 静态方法；Java9 私有方法
2. 使用`implements`，一个类可实现多个接口，解决单继承局限
3. 无构造方法；变量默认`public static final`常量；方法默认`public abstract`
4. 设计思想：抽象类 is-a（是什么），接口 can-do（能做什么）

## 核心对比表

|  对比项  |       抽象类       |             接口              |
| :------: | :----------------: | :---------------------------: |
|  关键字  |      extends       |          implements           |
| 继承数量 |    只能一个父类    |           多个接口            |
| 构造方法 |         有         |              无               |
| 成员变量 |     任意修饰符     | 只能 public static final 常量 |
|   方法   | 普通 / 静态 / 抽象 |  抽象、default、static、私有  |
| 设计定位 |    事物共性模板    |         行为能力规范          |

------

# 9. 内部类 & 枚举 Enum

## 9.1 四类内部类

1. 成员内部类：类中定义，可直接访问外部所有成员（含 private）
2. 静态内部类 static：只能访问外部静态成员，开发最常用（Builder 模式）
3. 局部内部类：方法内定义，极少使用
4. 匿名内部类：无类名，快速实现接口 / 抽象类，Lambda 替代方案

## 9.2 枚举 enum

1. 本质继承`Enum`的特殊类，固定有限常量场景（状态、季节、订单类型）
2. 天然线程安全，可实现单例模式（面试最优单例）
3. 自带`values()`遍历、`ordinal()`序号、`valueOf()`转换

```
enum Season { SPRING, SUMMER, AUTUMN, WINTER }
```

------

# 10. 包装类、自动装箱拆箱、Integer 缓存坑

## 10.1 基本类型 ↔ 包装类

byte-Byte /short-Short/int-Integer /long-Long/float-Float /double-Double/char-Character /boolean-Boolean

作用：集合、泛型只能存引用类型，必须用包装类。

出现原因：基本类型不是对象，而Java集合、泛型等特性只能操作对象，包装类让基本类型也能以对象形式使用。

## 10.2 装箱 / 拆箱

- 装箱：基本类型 → 包装类 `Integer i = 10;`
- 拆箱：包装类 → 基本类型 `int num = i;`

## 10.3 Integer 缓存（面试大坑）

Integer 缓存范围：`-128 ~ 127`，范围内`==`为 true；超出范围创建新对象，`==`返回 false，统一用`equals()`比较值。

```
Integer a = 127; Integer b = 127; System.out.println(a==b); // true
Integer c = 128; Integer d = 128; System.out.println(c==d); // false
```

------

# 11. String、StringBuilder、StringBuffer & 常量池

## 11.1 String 不可变

底层 char 数组`final`修饰，字符串一旦创建无法修改；拼接会生成新字符串，大量拼接性能差。

JS 字符串同样不可变，逻辑一致。

## 11.2 三者区分

1. String：不可变，少量拼接使用
2. StringBuilder：可变字符数组，**线程不安全**，单线程推荐（性能最高）
3. StringBuffer：可变，方法加`synchronized`锁，**线程安全**，多线程使用

## 11.3 字符串常量池（面试高频）

1. 双引号字面量创建，优先存入常量池复用；`new String()`强制在堆创建新对象

```
String s1 = "abc"; // 常量池
String s2 = new String("abc"); // 堆新对象
System.out.println(s1 == s2); // false
```

## 11.4 常用方法

- 比较
  - equals() 判断内容是否相同，区分大小写，推荐用“常量.equals(变量)”写法，避免空指针
  - equalsIgnoreCase() 不区分大小写比较
  - compareTo() 比较字符串大小关系，返回负整数、零、正整数
- 查
  - length() 返回字符串长度
  - charAt(int index) 获取制定位置的字符，索引从0开始
  - inidexOf(String str) 查找子字符串第一次出现的位置，没找到返回-1
  - contains() 判断是否包含指定内容
- 处理（截取、转换、替换等）
  - substring(int start, int end) 截取子字符串，左闭右开区间
  - trim() 去掉字符串两端空格
  - split(String regex) 按分隔符拆分字符串返回数组
  - replace()/replaceAll() 替换字符或字符串
  - toLowerCase()/toUpperCase() 大小写转换

------

# 12. ==、equals、hashCode 面试必背

1. ```
   ==
   ```

   - 基本类型：比较数值
   - 引用类型：比较内存地址

2. ```
   equals()
   ```

   - Object 原生 equals 等价于`==`；String/Integer 等重写后比较内容
   - 自定义类必须手动重写 equals 实现内容对比

3. ```
   hashCode()
   ```

   - 返回对象哈希整数，用于 HashSet/HashMap 快速判断
   - **黄金规则**：重写 equals 必须重写 hashCode；相等对象 hashCode 必须相同；hash 相同对象不一定相等（哈希碰撞）

   哈希碰撞：

   - 含义：两个或多个不同的输入数据在经过哈希函数处理后产生了相同的输出值

   - 产生原因：

     - **有限的输出范围**‌：哈希函数的输出范围（即哈希表的大小）是有限的，而输入空间通常是无限的或非常大
     - **生日攻击（Birthday Attack）**：对于某些类型的哈希函数，特别是那些输出空间相对较小的，理论上存在概率使得两个输入产生相同的输出。

   - 影响：

     - **性能下降**‌：在哈希表中，如果发生碰撞，通常需要通过链表或开放寻址法等方法解决，这会增加查找、插入和删除操作的复杂度。
     - **安全风险**‌：在某些应用场景中，如密码存储或数字签名，哈希碰撞可能导致安全漏洞，例如通过找到两个不同的密码产生相同的哈希值，从而破解密码。

   - 解决策略：

     - ‌**链地址法（Chaining）**：在哈希表的每个槽位中存储一个链表，所有哈希到该槽位的元素都链接在这个链表上。
     - **开放寻址法（Open Addressing）**：当发生碰撞时，算法会寻找表中的另一个空槽位来存储这个元素。
     - **使用更强的哈希函数**：例如SHA-256等，它们提供更大的输出空间，减少碰撞的可能性。
     - **增加哈希表的大小**：通过增加哈希表的大小，可以减少碰撞的概率。
     - **双哈希法**‌：结合两个哈希函数来减少碰撞。如果第一个哈希函数发生碰撞，可以使用第二个哈希函数来确定下一个位置。

   - 例子

     ```java
     import java.util.HashMap;
     import java.util.Map;
     
     public class HashCollisionExample {
         public static void main (String[] args) {
             Map<String, String> hashMap = new HashMap<>();
             hashMap.put("key1","value1");
             hashMap.put("key2","value2"); //正常情况下不会有碰撞
             hashMap.put("anotherKey1","value1"); //这里可能会有碰撞，取决于HashMap的实现和负载因子
             
             System.out.println(hashMap.get("key1")); // 输出 value1
             System.out.println(hashMap.get("key2")); // 输出 value2
             System.out.println(hashMap.get("anotherKey1")); // 如果发生碰撞，可能输出 value1 或其他值，取决于HashMap的实现细节
         }
     }
     ```

     在这个例子中，虽然我们手动添加了两个不同的键（"key1" 和 "anotherKey1"），它们的值（"value1"）相同，理论上在标准的`HashMap`实现中可能会发生碰撞（取决于具体的实现和当前负载因子），但在大多数情况下，`HashMap`会很好地处理这种情况，通过链地址法来存储具有相同哈希值的键值对。如果你需要避免这种情况或者需要更强的碰撞抵抗能力，可以考虑使用`LinkedHashMap`或自定义更复杂的冲突解决方法。对于安全性要求高的应用，应使用如SHA-256等更安全的哈希算法。

   

------

# 13. 日期时间 API

## 旧 API（Date/Calendar）缺陷

1. 可变对象，线程不安全
2. API 混乱，月份从 0 开始，计算繁琐

## Java8 新时间包 java.time（推荐）

1. LocalDate：纯日期
2. LocalTime：纯时间
3. LocalDateTime：日期 + 时间
4. DateTimeFormatter：线程安全格式化（替代 SimpleDateFormat）
5. Period/Duration：计算年月日、时分秒间隔

优势：不可变对象，线程安全，语法清晰，规避旧 API 坑。

------

# 14. 集合体系（对比 JS 数组 / 对象）

整体结构：Collection 单列集合 + Map 双列键值对

## 14.1 Collection

### List 有序、可重复

1. ArrayList：底层数组，查询快、尾部增删快，中间插入删除慢（JS 数组逻辑类似）, 随机get慢，线程不完全

2. LinkedList：双向链表，头尾增删极快，查询慢

3. Vector：数组，全部方法加锁，线程安全，性能差，淘汰

4. 常用方法：

   - 增

     - add(E e) 末尾添加单个元素
     - add(int index, E e) 指定下标插入
     - addAll(Collection<?extends E> c) 批量追加集合
     - addAll(int index, Collection<?extends E> c) 指定下标批量插入集合

   - 删

     - remove(int index) 按下标删除，返回被删除元素
     - remove(Object o) 删除第一个匹配元素，返回true/false
       - 坑：存数字时 `list.remove(1)` 会优先匹配下标，不是删除数字 1；要用 `list.remove(Integer.valueOf(1))`
     - removeAll(Collection<?> c) 删除交集元素
     - retainAll(Collection<?> c)  保留交集，删除其他
     - clear() 清空

   - 改

     - set(int index, E e) 替换指定下标元素，返回旧值

   - 查

     - get(int index) 根据下标取值
     - size() 获取集合长度
     - indexOf(Object o) 正向查找元素下标，不存在返回-1
     - lastIndexOf(Object o) 反向查找元素下标，不存在返回-1
     - contains(Object o) 是否包含元素，返回boolean
     - isEmpty() 判断是否为空

   - 转

     - subList(int formIndex, int toIndex) 截取子合集（左闭右开）
       - 坑：子列表是原集合视图，修改 sub 会同步影响原 list；原 list 结构性修改（add/remove）后 sub 会报错。
     - toArray() 转Object数组
     - toArray(T[] a) 转指定类型数组

   - 遍历

     - 普通 for

     - 增强 for

     - 迭代器 Iterator（遍历中安全删除元素）

       - ```java
         Iterator<String> it = list.iterator();
         while(it.hasNext()){
             String s = it.next();
             if ("B".equals(s)) it.remove();
         }
         ```

     - Stream (Java8) (类似箭头函数)

       - ```java
         //（对标JS forEach）
         list.forEach(item -> System.out.println(item));
         
         // Java8 Stream 拓展高频操作（实际开发最常用）
         List<Integer> nums = Array.asList(1,2,3,4,5);
         
         //过滤
         List<Integer> gt2 = nums.stream().filter(x -> x > 2).collect(Collectors.toList());
         
         //转换
         List<String> strList = nums.srteam().map(String::valueOf).collect(Collectors.toLsit());
         
         //去重
         List<Integer> distinct = nums.stream().distinct().collect(Collectors.toList());
         
         //排序
         List<Integer> sorted = nums.stream().sorted().collect(Collectors.toList());
         
         //求和、计数
         lang count = nums.stream().count();
         int sum = nums.stream().mapToInt(Integer::intValue).sum();
         ```

   - 排序

     - Collections.sort(List)自然排序（元素实现Comparable）
     - sort(comparator)自定义比较器（java8推荐）

   - 常用工具方法Collections

     - ```java
       // 反转集合
       Collections.reverse(list);
       // 随即打乱
       Collections.shuffle(list);
       // 获取最大值、最小值
       String max = Collections.max(list);
       String min = Collections.min(list);
       // 不可变集合（禁止增删改）
       List<String> unMod = Collections.unmodifiableList(list);
       ```

   - 坑点

     - remove(数字)优先匹配下标，删除数字包装类要传 `Integer.valueOf()`
     - `subList` 是视图，不是新集合，原 list 增删后子列表抛异常
     - `Arrays.asList()` 返回固定长度集合，不能 add/clear，会抛 UnsupportedOperationException
     - 遍历时用 list.remove () 会并发修改异常，删除必须用 Iterator.remove ()
     - ArrayList 查询快、中间插入删除慢；LinkedList 头尾增删快、随机 get 慢

### Set 无序、不可重复（依赖 equals+hashCode 去重）

1. HashSet：底层哈希表，无序，查询增删速度快;去重依靠 `hashCode + equals`

2. LinkedHashSet：哈希表 + 双向链表，**保留插入顺序**;性能略低于 HashSet，需要有序去重场景使用

3. TreeSet：红黑树，元素自动升序；元素必须实现 `Comparable` 或创建时传入 `Comparator`;支持区间截取、首尾获取等排序相关 API

4. 常用方法：

   - 增

     - boolean  add(E e)  添加单个元素，重复元素添加失败返回 `false`，成功返回 `true`
     - boolean addAll(Collection<? extends E> c) 批量添加集合所有元素，自动去重

   - 删

     - boolean remove(Object o) 删除匹配元素，成功返回 true
     - boolean removeAll(Collection<?> c) 删除和传入集合的交集元素
     - boolean retainAll(Collection<?> c) 保留交集，删除其他元素
     - void clear() 清空

   - 查

     - int size() 获取元素个数
     - boolean isEmpty() 判断是否为空集合
     - boolean contains(Object o) 是否包含指定元素
     - boolean containsAll(Collection<?> c) 是否包含传入集合全部元素

   - 集合转换

     - Object[] toArray() 转为 Object 数组
     - <T> T[] toArray(T[] a) 转为指定类型数组

   - 遍历

     - 增强 for

     - 迭代器 Iterator

     - Stream

       - ```java
         // Stream 常用操作（开发高频）
         Set<Integer> numSet = new HashSet<>(Arrays.asList(1,2,3,4,5));
         
         // 过滤
         Set<Integer> filterSet = numSet.stream().filter(n -> n > 2).collect(Collectors.toSet());
         
         // 转list
         List<Integer> list = numSet.stream().collect(Collectors.toList());
         
         // 去重（Set天然去重，List转Set可快速去重）
         List<Integer> source = Arrays.asList(1,1,2,2,3);
         Set<Integer> distinctSet = new HashSet<>(source);
         
         // 统计、求和
         long count = numSet.stream().count();
         int sum = numSet.stream().mapToInt(Integer::intValue).sum();
         
         ```

   - TreeSet独有方法（有序排序集合）

     - TreeSet 实现SortedSet，提供首尾、截取区间API

       - ```java
         TreeSet<Integer> tree = new TreeSet<>(Arrays.asList(10,20,30,40));
         tree.first();    // 获取最小元素 10
         tree.last();     // 获取最大元素 40
         tree.lower(30);  // 小于30的最大元素 20
         tree.higher(30); // 大于30的最小元素 40
         tree.floor(25);  // 小于等于25最大元素 20
         tree.ceiling(25);// 大于等于25最小元素 30
         tree.subSet(10,30); // [10,30) 截取区间
         ```

   - 坑点：

     - Set**没有索引**，不能通过下标获取、插入、删除
     - 自定义对象存入 Set，必须重写 `equals()` 和 `hashCode()`，否则无法去重
     - `TreeSet` 存储自定义对象不重写比较器会直接抛类型转换异常
     - `Arrays.asList()` 转 List 后再 new HashSet 可快速给 List 去重
     - 遍历过程中使用 `set.remove()` 会触发并发修改异常，删除只能用迭代器 `it.remove()`

## 14.2 Map 键值对，key 唯一

1. HashMap：哈希表，无序，开发最常用

2. LinkedHashMap：插入有序

3. TreeMap：key 自动升序排序

4. Hashtable：线程安全，性能差，淘汰

5. 常用方法：

   - 增 / 改

     - V put(K key, V value) 存入键值对
       - key 不存在：新增，返回 `null`
       - key 已存在：覆盖旧 value，返回**被覆盖的旧值**
     - void putAll(Map<? extends K, ? extends V> m) 批量复制另一个 Map 所有键值，重复 key 覆盖
     - V putIfAbsent(K key, V value) key 不存在才存入，存在则不修改，返回原有值；常用于**不存在再新增**

   - 查

     - V get(Object key) 根据 key 获取 value；key 不存在返回 `null`
     - V getOrDefault(Object key, V defaultValue) key 存在返回对应 value，不存在返回指定默认值（替代 `if null`）
     - boolean containsKey(Object key) 判断是否存在指定 key
     - boolean containsValue(Object value)  判断是否存在指定 value（效率低，会遍历全部元素）
     - int size() 获取键值对数量
     - boolean isEmpty() 判断集合是否为空

   - 删

     - V remove(Object key) 根据 key 删除，返回被删除的 value；不存在返回 null
     - boolean remove((Object key, Object value) **key 和 value 同时匹配才删除**，匹配成功返回 true，否则 false
     - void clear() 清空所有键值对

   - 获取视图（遍历必备三大方法）

     - Set<K> keySet() 获取所有 key 组成 Set

       - ```java
         Set<String> keys = map.keySet();
         // 遍历key
         for(String key : keys){
             System.out.println(key + "=" + map.get(key));
         }
         ```

     - Collection<V> values() 获取所有 value 组成集合（可重复）

       - ```java
         Collection<Integer> vals = map.values();
         for(Integer v : vals){
             System.out.println(v);
         }
         ```

     - Set<Map.Entry<K,V>> entrySet() 获取键值对实体（最高效遍历）

       - ```java
         for(Map.Entry<String, Integer> entry : map.entrySet()){
             String k = entry.getKey();
             Integer v = entry.getValue();
             System.out.println(k + ":" + v);
         }
         ```

     - Java8 新增常用方法（开发高频）

       - forEach(BiConsumer) 一键遍历

         - ```java
           map.forEach((k,v) -> System.out,println(k + "" + v));
           ```

       - computeIfAbsent(K key, Function) key 不存在，执行函数生成 value 存入并返回；存在直接返;适合：key 不存在才创建对象 / 集合回原有 value

         - ```java
           Map<String, List<Integer>> data = new HashMap();
           //不存在则新建ArrayList
           data.computeIfAbsent("soreList", k -> new ArrayList<>()).add(99);
           ```

       - computeIfPresent(K key, BiFunction) key 存在才执行函数，更新 value；不存在不操作

         - ```java
           map.computeIfPresent("Java", (k,v) -> v + 5);
           ```

       - compute(K key, BiFunction) 不管 key 是否存在，都执行函数替换 value

         - ```java
           map.compute("Java", (k,v) -> v == null ? 0 : v + 10);
           ```

       - merge(K key, V value, BiFunction) 合并 value：key 不存在则存入 value；存在则执行函数合并新旧值

         - ```java
           map.merge("Java", 10, Integer::sum);
           ```

   - Stream 处理Map

     - ```java
       Map<String, Integer> map = new HashMap<>();
       map.put("A", 10);
       map.put("B", 20);
       map.put("C", 30);
       
       // 过滤key，转为新Map
       Map<String, Integer> filterMap = map.entrySet().stream().filter(e -> e.getValue() > 10).collect(Collectors.toMap(Map.Enrty::getKey, Map.Entry::getValue));
       // 只提取value集合
       List<Integer> valList = map.values().stream().collect(Collectors.toList());
       // 按value排序（LinkedHashMap有序输出）
       Map<String, Integer> sortedMap = map.entrySet().stream().sorted(Map.Entry.comparingByVlaue()).collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue, (oldV, newV) -> oldV, LinkedHashMap::new));
       ```

   - TreeMap 独有方法（有序 Map）

     - ```java
       TreeMap<String, Integer> treeMap = new TreeMap<>();
       
       treeMap.firstKey(); //最小key
       treeMap.lastKey(); //最大key
       treeMap.lowerKey("C"); //小于C的最大key
       treeMap.higherKey("C"); //大于C的最小key
       treeMap.subMap("A", "D"); // [A,D) 区间截取
       ```

   - Map遍历四种方式对比

     - keySet() + get()：性能差，多次查询，数据量大不推荐
     - values()：只需要 value 时使用；
     - entrySet()：最优，一次获取 key+value，日常首选；
     - forEach Lambda：简洁，适合简单打印、逻辑处理。

   - 坑点：

     - Map 的 key 唯一，重复 put 会覆盖旧值

     - 自定义对象作为 key，必须重写 `equals()` + `hashCode()`，否则 HashMap 无法去重

       - ```java
         // HashMap去重原理：先算hashCode定位到“哪个桶”，再用equals对比内容
         // 不重写的默认行为：Object类原生的hashCode()根据对象内存地址算的，equals等价于==比内存地址。
         // 所以会出现两个内容完全一样的new对象，地址不同，hashCode就不同，HashMap就会认为是两个不同的key，去重失败。
         ```

       - 反面例子：不重写

         ```java
         import java.util.HashMap;
         import java.util.Map;
         
         //自定义对象，补充些equals和hashCode
         class Student {
             String name;
             int age;
             
             public Student(String name, int age) {
                 this.name = name;
                 this.age = age;
             }
         }
         
         public class Test {
             public static void main(String[] args) {
                 Map<Student, Integer> map = new HashMap<>();
                 
                 Student s1 = new Student("张三", 19);
                 Student s2 = new Student("张三", 19);
                 
                 map.put(s1, 100);
                 map.put(s2, 99);
                 
                 System.out.println(map.size()); // 输出：2  ← 去重失败了！两个张三都存进去了
                 
                 Student s3 = new Student("张三", 19);
                 System.out.println(map.get(s3)); // 输出：null  ← 内容相同但查不到，因为地址不一样
             }
         }
         ```

       - 正面例子：重写了

         ```java
         import java.util.HashMap;
         import java.util.Map;
         import java.util.Objects;
         
         //自定义对象，补充些equals和hashCode
         class Student {
             String name;
             int age;
             
             public Student(String name, int age) {
                 this.name = name;
                 this.age = age;
             }
             
             @Override
             public boolean equals(Object o) {
                 if (this == o) return true;
                 if (o == null || getClass() != 0.getClass()) return false;
                 Student student = (Student) 0;
                 return age == student.age && Objects.equals(name, student.name);
             }
             
             @Override
             public int hashCode() {
                 return Objects.hash(name, age);
             }
         }
         
         public class Test {
             public static void main(String[] args) {
                 Map<Student, Integer> map = new HashMap<>();
                 
                 Student s1 = new Student("张三", 19);
                 Student s2 = new Student("张三", 19);
                 
                 map.put(s1, 100);
                 map.put(s2, 99);
                 
                 System.out.println(map.size()); // 输出：1 
                 
                 Student s3 = new Student("张三", 19);
                 System.out.println(map.get(s3)); // 输出：99
             }
         }
         ```

       - 黄金规则

         - 两个对象 equals 相等，hashCode 必须相等
         - **两个对象 hashCode 相等，equals 不一定相等**（哈希碰撞，正常现象）
         - 重写 equals 就必须重写 hashCode，反之亦然

     - TreeMap 的 key 必须实现 `Comparable`，或构造传入比较器，否则抛异常

       - ```java
         //TreeMap 底层是红黑树（自动排序的二叉树），它存元素时必须知道 "谁大谁小" 才能放到正确的位置。
         //你不给它比较规则，它不知道怎么排序，直接抛异常。
         ```

       - 反面例子

         ```java
         import java.util.TreeMap;
         
         class Student {
             String name;
             int age;
             
             public Student(String name, int age) {
                 this.name = name;
                 this.age = age;
             }
         }
         
         puiblic class Test {
             public static void main(String[] args) {
                 TreeMap<Student, Integer> treeMap = new TreeMap<>();
                 treeMap.put(new Student("张三", 99), 100); // 直接抛异常：ClassCastException: Student cannot be cast to Comparable
             }
         }
         ```

       - 正面例子

         ```java
         import java.util.TreeMap;
         import java.util.Comparator;
         
         // 方案一：让类实现Comparable接口
         calss Student implements Comparable<Student> {
             String name;
             int age;
             
             public Student(String name, int age) {
                 this.name = name;
                 this.age = age;
             }
             
             //重写比较方法：返回负数=小，0=相等，正数=大
             @Override
             public int compareTo(Student o) {
                 // 按年龄升序排序
                 return this,age - o.age
             }
             
             @Override
             public String toString() {
                 reutrn name + "(" + age + ")"
             }
         }
         
         public class Test {
             public static void main(String[] args) {
                 TreeMap<Student, Integer> treeMap = new TreeMap<>();
                 
                 treeMap.put(new Student("李四", 20), 90);
                 treeMap.put(new Student("张三", 18), 100);
                 treeMap.put(new Student("王五", 22), 80);
                 
                 treeMap.forEach((k,v) -> System.out.println(k + " + " + v));
                 // 输出自动按年龄升序：
                 // 张三(18) = 100
                 // 李四(20) = 90
                 // 王五(22) = 80
             }
         }
         
         
         
         //=================================================================================
         
         // 方案二：构造 TreeMap 时传入 Comparator 比较器（外部指定规则，更灵活）
         class Student {
             String name;
             int age;
             public Student(String name, int age) {
                 this.name = name;
                 this.age = age;
             }
             
             @Override
             public String toString() {
                 return name + "(" + age + ")";
             }
         }
         
         public class Test {
             public static void main(String[] args) {
                 // 构造时传入比较器：按年龄降序
                 TreeMap<Student, Integer> treeMap = new TreeMap<>(
                 	Comparator.comparingInt(s -> -s.age) //加负号就是降序
                 );
                 
                 treeMap.put(new Student("李四", 20), 90);
                 treeMap.put(new Student("张三", 18), 100);
                 treeMap.put(new Student("王五", 22), 80);
         
                 treeMap.forEach((k, v) -> System.out.println(k + " = " + v));
                 // 输出按年龄降序：
                 // 王五(22) = 80
                 // 李四(20) = 90
                 // 张三(18) = 100
             }
         }
         
         ```

         

     - `get(key)` 可能返回 null，取值优先用 `getOrDefault` 避免空指

     - 遍历 `entrySet` 时调用 `map.put/remove` 会触发并发修改异常；如需删除用迭代器

     - `HashMap` 线程不安全，多线程并发操作会数据错乱，可用ConcurrentHashMap

### 14.3 List / Set / Map核心区别速记

| 集合 | 存储结构 | 是否可重复           | 是否有索引 | 核心特点                        |
| ---- | -------- | -------------------- | ---------- | ------------------------------- |
| List | 单列对象 | 允许重复             | 有下标     | 有序，支持按索引增删查          |
| Set  | 单列对象 | 不允许               | 无下标     | 自动去重，依赖hashCode + equals |
| Map  | 键值对   | key唯一，value可重复 | 无下标     | 双列存储，通过key查询value      |

JS 对比：JS Array≈List，Object/Map≈Java HashMap，但无类型约束、无去重机制。

- BiFunction

  - java.util.function.BiFunction<T,U,R> （T\U两个入参类型，R返回值类型）

    - 属于Java8函数式接口，作用：接收两个入参，返回一个结果
    - 和Function的区别：Function单入参
    - 函数式接口只有一个抽象方法
      - R apply(T t, U u);

  - 示例

    - ```java
      import java.util.function.BiFunction;
      
      public class Test {
          public static void main(String args) {
              BiFunction<Integer, Integer, Integer> add = (a ,b) -> a + b;
              Integer res = add.apply(10, 20); // 输出 30
          }
      }
      ```

  - Map中高频使用场景

    - ```java
      Map<String, Integer> map = new HashMap<>();
      map.push("Cyrus", 100);
      
      // computeIfPresent(K key, BiFuncion) 
      map.computeIfPresent("Cyrus", (k, oldV) -> oldV + 10);
      
      // compute (K key, BiFunction) 
      map.compute("shanshan", (k, oldV) -> oldV == null ? 0 : oldV + 5);
      
      // merge (K key, V value, BiFunction)
      map.merge("Cyrus", 200, (oldV, newV) -> oldV + newV);
      
      ```

- BiConsumer<T,U> 双参数，**无返回值**（Map.forEach 用的就是它）

- BiPredicate<T,U> 双参数，返回 `boolean` 做判断

- Function<T,R>  单参数有返回

- Consumer<T> 单参数无返回

------

# 15. 泛型 Generics

## 15.1 作用

编译期类型校验，消除类型转换异常，类型更安全；自动强转，代码更简洁；同一个泛型类可以用不同类型的参数实例化，一套代码能复用。

## 15.2 类型擦除（面试核心）

泛型仅存在编译阶段，运行时全部擦除为 Object，无泛型类型信息。

泛型类型必须是引用类型不能是基本类型，也不能用new T() 创建对象。

| 泛型字母 | 全称         | 用途场景                  |
| -------- | ------------ | ------------------------- |
| T        | Type         | 单个任意类型（最通用）    |
| E        | Element      | 集合元素：List<E>、Set<E> |
| K        | Key          | Map的键Key                |
| V        | Value        | Map的值Value              |
| N        | Number       | 数字类型(Number 子类)     |
| S/U/V    | Second/Third | 多个泛型参数时依次使用    |
| R        | Return       | 返回值类型（函数式接口）  |

```java
// 1. T：普通单个类型: 通用类、工具类，单个未知类型
public class Box<T> {
    private T data;
}

// 2. E：集合元素 Element: List、Set、Collection 标准写法
List<E>;
Set<E>;
public static <E> void print(E[] arr) {}

// 3. K + V：Map 键值对 Key / Value
MaP<k,v>;
public class MyMap<K,V>{};


// 4. S、U、V：多个泛型参数 两个、三个泛型依次用 S U V
// 两个参数
public class Pair<S, U> {};
// 三个参数
public class Triple<S, U, V> {};

// 5. R：返回值 Return 函数式接口专用（Function、BiFunction）
// T入参，R返回值
public interface Function<T,R> {
    R apply(T t);
}
// BiFunction<T,U,R> 两个入参，R返回


// 6. N：数字 Number 只用于数字相关工具类
public class NumUtil<N extends Number>{}

```



## 15.3 通配符

1. `List<?>`：任意类型，仅可读，不能 add（null 除外）
2. `? extends T` 上界：T 及子类，只读
3. `? super T` 下界：T 及父类，可写入

## 泛型类 / 泛型方法

```
// 泛型类
class Box<T>{}
// 泛型方法
public <E> void print(E e){}
```

------