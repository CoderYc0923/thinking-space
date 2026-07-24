# 16. Java8 新特性（前端极易理解，对标 JS）

## 16.1 Lambda 表达式

函数式接口（仅一个抽象方法）简化匿名内部类，对标 JS 箭头函数

```
// JS
()=>console.log(1)
// Java
() -> System.out.println(1);
```

## 16.2 方法引用 `::`

简化 Lambda：

- `对象::方法`：用已存在实例调用方法

  - ```java
    String str = "abc";
    Supplier<Integer> len = str::length;
    // 等价 () -> str.length()
    ```

- `类::静态方法`：调用静态工具方法

  - ```java
    Function<String, Integer> func = Integer::parseInt;
    // 等价 s -> Integer.parseInt(s)
    ```

- `类::实例方法`：流中元素作为调用者（最常用，如 Entry::getKey、String::trim）

  - ```java
    // 完整lambda
    (Map.Entry<String,Integer> entry) -> entry.getKey();
    // 方法引用简写
    Map.Entry::getKey;
    
    list.stream().map(String::toUpperCase);
    // 等价 s -> s.toUpperCase()
    ```

- `类::new`：创建对象构造器引用

  - ```java
    Supplier<List<String>> sup = ArrayList::new;
    // 等价 () -> new ArrayList<>()
    ```



## 16.3 Stream API

集合流式操作，对标 JS 数组高阶函数 filter/map/reduce

中间操作（延迟执行）：filter、map、sorted、limit

终端操作（触发执行）：collect、count、forEach

1. 分为中间操作和终端操作

   ```java
   import java.util.*;
   import java.util.stream.Collectors;
   
   List<Integer> nums = Arrays.asList(1,2,3,4,5,6,6,7,8,9,10);
   List<String> names = Arrays.asList("张三","李四","王五","张六","赵七");
   ```

   

   - 中间操作

     - 延迟执行，返回新Stream,可链式调用

     - filter 过滤

       ```java
       List<Integer> evens = nums.stream().filter(n -> n % 2 == 0).collect(Collectors.toList());
       ```

     - map 转换映射

       ```java
       // 数字转字符串
       List<String> numStr = nums.stream()
               .map(String::valueOf)
               .collect(Collectors.toList());
       
       // 获取姓名长度
       List<Integer> nameLen = names.stream()
               .map(String::length)
               .collect(Collectors.toList());
       ```

     - flatMap 扁平化

       ```java
       List<List<Integer>> data = Arrays.asList(
               Arrays.asList(1,2),
               Arrays.asList(3,4)
       );
       List<Integer> flat = data.stream()
               .flatMap(List::stream)
               .collect(Collectors.toList());
       // [1,2,3,4]
       ```

     - distinct 去重

       ```java
       List<Integer> distinctNums = nums.stream()
               .distinct()
               .collect(Collectors.toList());
       // [1,2,3,4,5,6,7,8,9,10]
       ```

     - sorted 排序

       ```java
       // 升序
       nums.stream().sorted().collect(Collectors.toList());
       // 降序
       nums.stream().sorted((a,b)->b-a).collect(Collectors.toList());
       
       // 按字符串长度排序
       names.stream()
               .sorted(Comparator.comparing(String::length))
               .collect(Collectors.toList());
       ```

     - limit (n) 截取前 n 个元素

       ```java
       // 取前3个
       List<Integer> top3 = nums.stream()
               .limit(3)
               .collect(Collectors.toList()); // [1,2,3]
       ```

     - skip (n) 跳过前 n 个元素

       ```java
       // 跳过前2个，取后面所有
       List<Integer> skip2 = nums.stream()
               .skip(2)
               .collect(Collectors.toList());
       ```

     - peek 调试打印（不改变流，仅执行逻辑）

       ```java
       nums.stream()
               .filter(n -> n > 5)
               .peek(n -> System.out.println("过滤后："+n))
               .collect(Collectors.toList());
       ```

       

   - 终端操作

     - 触发计算，关闭流，只能最后调用一次

     - collect () 收集（最常用）

       ```java
       // 1.1 转 List / Set
       // List
       List<Integer> list = nums.stream().filter(n->n>5).collect(Collectors.toList());
       // Set（自动去重）
       Set<Integer> set = nums.stream().collect(Collectors.toSet());
       
       // 1.2 转 Map（重点）
       // key:姓名 value:姓名长度
       Map<String, Integer> nameMap = names.stream()
               .collect(Collectors.toMap(
                       name -> name,
                       String::length
               ));
       // 重复key场景：第三个参数处理冲突
       Map<String, Integer> mapWithDup = nums.stream()
               .collect(Collectors.toMap(
                       String::valueOf,
                       n->n,
                       (oldVal, newVal) -> oldVal // 重复key保留旧值
               ));
       
       // 1.3 分组 groupingBy
       // 按奇偶分组 key:true/false
       Map<Boolean, List<Integer>> groupByOdd = nums.stream()
               .collect(Collectors.groupingBy(n -> n % 2 == 0));
       
       
       // 1.4 分区 partitioningBy（特殊分组，仅 true/false）
       Map<Boolean, List<Integer>> part = nums.stream()
               .collect(Collectors.partitioningBy(n -> n > 5));
       
       
       // 1.5 拼接字符串 joining
       String join = names.stream().collect(Collectors.joining("、"));
       // 张三、李四、王五、张六、赵七
       
       ```

     - forEach 遍历（无返回值）

       ```java
       nums.stream().forEach(System.out::println);
       ```

     - count () 统计元素数量，返回 long

       ```java
       long evenCount = nums.stream().filter(n->n%2==0).count();
       ```

     - max /min 取最大最小，返回 Optional

       ```java
       Optional<Integer> max = nums.stream().max(Integer::compareTo);
       Optional<Integer> min = nums.stream().min(Integer::compareTo);
       max.ifPresent(System.out::println);
       ```

     - anyMatch /allMatch/noneMatch 返回布尔

       ```java
       // anyMatch：任意一个满足
       boolean hasBig = nums.stream().anyMatch(n -> n > 8); // true
       // allMatch：全部满足
       boolean allPositive = nums.stream().allMatch(n -> n > 0); // true
       // noneMatch：全部不满足
       boolean noNeg = nums.stream().noneMatch(n -> n < 0); // true
       ```

     - findFirst /findAny 获取元素，返回 Optional

       ```java
       // 获取第一个偶数
       Optional<Integer> firstEven = nums.stream().filter(n->n%2==0).findFirst();
       firstEven.ifPresent(v-> System.out.println(v));
       
       // 并行流随机取 findAny
       Optional<Integer> any = nums.parallelStream().findAny();
       ```

     - reduce 归约聚合（求和、乘积、拼接）

       ```java
       // 求和
       Integer sum = nums.stream().reduce(0, Integer::sum);
       // 乘积
       Integer mul = nums.stream().reduce(1, (a,b)->a*b);
       // 字符串拼接
       String nameStr = names.stream().reduce("", (s1,s2)->s1+s2);
       ```

   - 数值流专用（IntStream/LongStream/DoubleStream）

     ```java
     // 求和
     int sum = nums.stream().mapToInt(Integer::intValue).sum();
     // 平均值
     double avg = nums.stream().mapToInt(Integer::intValue).average().getAsDouble();
     // 最大、最小
     int max = nums.stream().mapToInt(Integer::intValue).max().getAsInt();
     ```

   - 并行流 parallelStream ()

     ```java
     //大数据量提升遍历效率，多线程执行；不适合有线程安全操作
     nums.parallelStream().filter(n->n>5).collect(Collectors.toList());
     ```

   - 高频开发场景完整示例

     ```java
     // 场景 1：过滤、转换、去重、排序、收集
     List<String> res = nums.stream()
             .filter(n -> n > 3)
             .distinct()
             .sorted((a,b)->b-a)
             .map(n->"数字："+n)
             .collect(Collectors.toList());
     
     // 场景 2：分组统计
     // 按姓名首字分组
     Map<Character, List<String>> group = names.stream()
             .collect(Collectors.groupingBy(name -> name.charAt(0)));
     ```

   - Stream 注意事项

     - 流只能使用一次，终端操作后流关闭，重复调用抛异常
     - 中间操作延迟执行，只有调用终端操作才会真正计算
     - parallelStream 并行流存在线程安全问题，不要操作外部共享变量
     - 操作自定义对象去重、分组依赖 `equals+hashCode`
     - 尽量用 Collectors 收集，少用循环手动组装集合

## 16.4 Optional

解决空指针 NPE，替代多层`if(obj!=null)`，JS 无原生 Optional

1. java.util.Optional<T>

   - 是**容器对象**，内部只能存两种状态：
     - 包裹一个非空 `T` 对象
     - 空（不存任何值，替代 `null`）
   - 核心目的：**优雅规避空指针异常 NullPointerException**，代替一堆 `if(obj != null)` 判断

2. 创建 Optional 的 3 种方式

   ```java
   // 1. 包装确定不为空的值，传null直接抛空指针
   Optional<String> op1 = Optional.of("Java");
   // 2. 包装可能为null的值（最常用），null会生成空Optional
   Optional<String> op2 = Optional.ofNullable(null);
   // 3. 直接创建空Optional
   Optional<String> empty = Optional.empty();
   ```

   、

3. 常用核心方法（分大类）

   - 判断是否有值

     - `isPresent()`：返回 boolean，有值 true，空 false
     - `isEmpty()`（Java11+）：和 isPresent 相反，空返回 true

   - 有值就执行逻辑（推荐，替代 if 判断）

     - `ifPresent(Consumer)`：有值才执行，无值啥也不做

   - 获取值（避坑：get () 不推荐单独用）

     - `get()`：有值返回，**空直接抛 NoSuchElementException**

   - 无值时给默认值（高频业务使用）

     - `orElse(T defaultValue)`：无论有没有值，**默认对象都会创建**

       ```java
       String res = Optional.ofNUllable(null).orElse("默认名称");
       ```

       

     - `orElseGet(Supplier)`：只有为空时才执行生成默认值，性能更好

       ```java
       String res = Optional.ofNullable(null).orElseGet(() -> "默认名称");
       ```

       

     - `orElseThrow()`：空则抛出异常，有值直接返回

       ```java
       String name = Optional.ofNullable(null).orElseThrow(() -> new RuntimeException("用户不存在"));
       ```

       

   - 映射转换 map /flatMap（配合 Stream 思想）

     - map：一层转换，返回 Optional <转换后类型>

       ```java
       // 获取用户城市，为空返回默认
       class User{ String city; public String getCity(){return city;} }
       Optional<User> userOpt = Optional.ofNullable(new User());
       // 提取city
       Optional<String> cityOpt = userOpt.map(User::getCity);
       String city = cityOpt.orElse("未知城市");
       ```

     - flatMap：转换后本身返回 Optional，避免嵌套 Optional<Optional<T>>

       ```java
       // 假设getAddress返回Optional<Address>
       Optional<String> city = userOpt.flatMap(User::getAddress)
               .map(Address::getCity);
       ```

       

   - 过滤 filter（满足条件保留，否则变成空 Optional）

     ```java
     Optional<String> opt = Optional.of("张三");
     opt.filter(name -> name.length() > 2).ifPresent(System.out::println);
     ```

4. 完整链式实战（多层对象，无 if 判空）

   ```java
   // 需求：获取用户所在城市，为空输出"未知"
   String city = Optional.ofNullable(getUser())
           .map(User::getAddress)
           .map(Address::getCity)
           .orElse("未知");
   ```

5. 开发使用规范 & 坑点

   - **不要滥用 get ()**：必须搭配 `isPresent()` 再调用，否则极易抛异常；优先用 orElse /orElseGet
   - 方法返回值推荐用 Optional：比如查询单个对象 `Optional<User> findById(Long id)`，明确告知调用方可能为空
   - 不要把 Optional 作为类成员变量（不适合序列化，占用额外内存）
   - 不要作为方法入参，入参直接传原对象即可
   - Optional 是不可变容器，内部值一旦包裹无法修改

6. 高频面试题

   - Optional.of 和 Optional.ofNullable 区别？
     - `of()` 传入 null 直接抛空指针；`ofNullable()` 允许 null，生成空 Optional。
   - orElse 和 orElseGet 的区别？
     - orElse 不管是否为空，都会创建默认对象；orElseGet 只有为空才执行生成，开销更小。
   - map 和 flatMap 区别？
     - map 转换函数返回普通类型；flatMap 转换函数返回 Optional，防止嵌套 Optional。
   - Optional 能不能解决所有空指针？
     - 只能处理引用类型判空；基础类型、数组下标越界、集合 get 越界无法处理。

