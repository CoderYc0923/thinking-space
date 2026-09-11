- 数组和集合的区别，用过哪些？
  - **数组**是**固定长度**的数据结构，一旦创建长度就无法改变，而**集合**是**动态长度**的数据结构，可以根据取药动态增加或减少元素。
- 说说Java中的集合和Map？
  - **List**
    - **有序**、**可重复**、**可按下标访问**
    - 
    - **`ArrayList`**
      - **底层使用数组实现**，当集合扩容时，会创建更大的数组，并把原数组复制到新数组
      - **随机访问快，尾部增删快，中间增删要搬移**
      - **线程不安全**
        - 因为为了性能故意**不做同步**，**共享可变状态**（数组 + `size` + 扩容）在多线程下既**不原子、也不可见性一致**，所以线程不安全
        - **如何变线程安全**：**`Colloctors.synchronizedList(new ArrayList<>()) 粗粒度同步`，`CopyOnWriteArrayList（读多写少）`**，或**外层自己加锁**
      - **扩容约1.5倍**（因为1.5可以充分**利用位移操作**，**减少浮点数**或者**运算时间和运算次数**），扩容有**数组复制**，
      - 场景：**查询多，尾部追加**
    - **`LinkedList`**
      - **双向链表**，也可以当双端队列
      - **任意位置插入不一定比`ArrayList`快**，因为要**先O(n)找到节点**，且**缓存不友好**，多数场景`ArrayLsit`更快
      - 场景：**头尾频繁插入删除**
    - `CopyOnWriteArrayList`
      - **线程安全**：使用**`volatile`关键字**修饰数组，**保证可见性**。**写操作**时加了**`ReentrantLock`保证线程安全**
      - 场景：**读多写少**
    - `Vector`
      - 类似`ArrayList`，方法带`synchronized`
      - 锁整表，性能差
      - 场景：几乎不推荐
    - `Stack`
      - 继承`Vector`的栈
      - 更推荐`Deque`，如`ArrayDeque`
  - **Set**
    - **不可重复**，**通常无序**
    - `HashSet`
      - 底层是**`HashMap`**
      - **无序，线程不安全，依赖`equals`和`hashCode`**
      - 场景：**去重，判断是否存在**
    - `LinkedHashSet`
      - **`HashSet` + 链表记插入顺序**
      - **无序，线程不安全，依赖`equals`和`hashCode`**
      - 场景：要**去重且保证插入顺序**
    - `TreeSet`
      - 底层是**`TreeMap`，红黑树**，**插入时自动排序**
      - **元素需要实现`Comparable`或传`Comparator`；线程不安全**
      - 场景：要**排序的去重集合**
    - `CopyOnWriteArratSet`
      - **基于`CopyOnWriteArrayList`**
      - **写操作拷贝整个数组**
      - 场景：适合**读多写少的并发`Set`**
  - **Queue**
  - **Map**
    - **键唯一，值可重复**
    - `HashMap`
      - **数组 + 链表/红黑树**，`JDK8`链表长度大于等于8且容量大于等于64才会树化。容量宜2^n
      - **允许一个null key**
      - 线程不安全。
      - 场景：**通用KV，查询为主**
    - `LinkedHashMap`
      - `HashMap` + **双向链表**
      - 场景：**要插入顺序/访问顺序（可做简单LRU）**
    - `TreeMap`
      - **红黑树，按key排序**
      - **key需要可比，线程不安全**
      - 场景：要**有序Map**、**范围查询**
    - `HashTable`
      - **方法级`synchronized`**
      - **锁整表；不允许null**；不推荐，**要用`ConcurrentHashMap`**
    - `ConcurrentHashMap`
      - **`JDK7`分段锁；`JDK8`CAS + 桶头`synchronized`**
      - **不允许null，并发下`size`等是弱一致观感**
      - 场景：**并发Map首选，线程安全**

**场景选择口诀：**

- `ArrayList`：**列表、下标访问、一般增删**
- `ArrayDeque（常优于LinkedList）`：**只要头尾队列操作**
- `HashSet`：**要去重**
- `LinkedHashSet`：**要去重且排序**
- `TreeSet / TreeMap`：**要排序集合/有序Map**
- `HashMap`：**普通`KV`**
- `LinkedHashMap`：**要有序的Map/简单`LRU`**
- `ConcurrentHashMap`：**多线程Map**
- `CopyOnWriteArrayList/Set`：**读多写少**



**注意：**

- **线程安全集合不等于符合操作原子**
- **`equals`和`hashCode`一起重写**

