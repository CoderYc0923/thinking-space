- Stream是对数据源（集合/数组等）的一次流水线处理：先进行一串**中间操作**（懒执行），最后用**终端操作**触发计算并得到计算结果，不改原集合

- ```java
  list.stream()
      .filter(x -> x > 0) // 中间，惰性计算
      .map(x -> x + 2) //中间，惰性计算
      .collect(Collectors.toList()); // 终端，这里才触发计算
  ```

- **创建Stream的方式**

  - 集合：`list.stream() / list.parallelStream()`
  - 数组：`Arrays.stream(arr)`
  - 可变参数：`Stream.of(1,2,3)`
  - 构造器：`Stream.builder().add(1).add(2).build()`
  - 无限流（要`limit`）：`Stream.iterate(0, n -> n + 1) / Stream.generate(Math::random)`
  - 基本类型特化：`IntStream.range(1, 10) \ LongStream \ DoubleStream`
  - 文件行（需要手动关闭）：`Files.lines(path)`

- **中间操作（惰性操作，链式）**

  - 筛选/去重/截断

    - `filter`：条件过滤
    - `distinct`：去重（靠`equals`和`hashCode`）
    - `limit(n)`：取前n个
    - `skip(n)`：跳过前n个
    - `takeWith / dropWhile（Java9+）`遇到不满足就停止/丢弃前缀

  - 映射

    - `map`：转换函数，一对一转换

    - `flatMap`：扁平化

      - ```java
        List<List<String>> lists = List.of(
        	List.of("a", "b"),
            List.of("c", "d")
        );
        
        List<String> flat = lists.stream()
            	.flatMap(list -> list.stream())
            	.collect(Collectors.toList());
        
        // [a,b,c,d]
        ```

      - 

    - `mapToInt / mapToLong / mapToDouble`：转成基本类型流，方便`sum() / average()`

      - ```java
        List<Integer> nums = List.of(1,2,3,4);
        
        int sum = nums.stream()
            	.mapToInt(Integer::intVale)
            	.sum(); // 10
        
        // 对象上取int字段也一样
        int total = orders.stream()
            	.mapToInt(Order::getAmount)
            	.sum();
        ```

      - 

    - `boxed`：基本类型流 再装箱成对象流，方便`collect`

      - ```java
        List<Integer> list = IntStream.rangeClosed(1,5)
            .boxed()
            .collect(Collectors.toList());
        
        // [1,2,3,4,5,]
        ```

  - 排序/查看

    - `sorted`：自然序
    - `sorted(Comparator)`：自定义排序
    - `peek(Consumer)`：中间“偷看”（调试用）

- **终端操作（触发计算，之后流结束）**

  - 收集/遍历
    - `collect(Collectors)`：最常用，收集成`List/Set/Map`等
      - 转集合
        - `Collectors.toList() / toSet() / toMap(User::getId, User::getName, (a,b) -> a)`： `toMap`key冲突要写合并函数
      - 拼接
        - `Collectors.joining(",")`
      - 分组 / 分区
        - `Collectors.groupingBy(User::getDept)`：按某个字段分成多组
        - `Collectors.partitioningBy(u -> u.getAge() >= 18)`：按条件`true/fasle`分成两组
      - 统计
        - `Collectors.counting`：个数
        - `Collectors.summingInt(Order::getAmount)`：和
        - `Collectors.averagingDouble(Order::getAmount)`：平均值
        - `Collectors.summarizingInt(Order::getAmount)`：几个指标都要（个数，和，平均值）
      - 下游收集器（比如分组后再处理）
        - `Collectors.groupingBy(User::getDept, Collectors.counting())`
    - `toList() (Java16+)`：快捷收集`List`
    - `forEach(Consumer)`：遍历（并行时不保证顺序）
    - `forEachOrdered`：遍历（并行时保证顺序）
  - 匹配/查找
    - `anyMatch / allMatch / noneMatch`：是否存在/全是/全不是
    - `findFirst`：第一个（有序流稳定）
    - `findAny`：任意一个（并行时更合适）
  - 聚合
    - `count`：个数
    - `reduce`：归约成一个值（求和，拼串等）
    - `min / max`：最小/最大（常配`Comparator`）
    - `sum / average 等`：多在`IntStream`等上

- **并行流 ParallelStream**

  - `list.parallelStream / list.stream().parallel()`
  - 本质是把数据拆成多段**子流**，多线程并行处理，再把结果合并
  - 底层是`ForkJoin`：大任务拆小任务并行算，再汇总
  - 默认用`JVM`的`ForkJoinPool.commonPool()`公共池
  - 执行顺序可能会乱，要顺序的话用`forEachOrdered / findFirst`
  - **适合**：CPU密集、数据量大、元素彼此独立、无共享状态的场景
  - **不适合**：I/O密集（查库/HTTP/读文件会占着公共池干等）、数据量小、有共享状态、强依赖顺序
  - **注意**：
    - 线程安全性
    - 公共池**可能被其他并行任务共用**
    - `forEach`无序
    - 别在里面改同一集合

