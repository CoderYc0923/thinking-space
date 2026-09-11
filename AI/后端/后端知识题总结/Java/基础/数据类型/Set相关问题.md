- **Set集合特点**
  - **无重复**



- **如何实现key无重复？**
  - `HashSet/ LinkedHashSet`，底层是**哈希表**，插入元素时，**先`hashCode`定位桶，再通过`equals`判断是否存在相同元素，相同则不插入**
  - `TreeSet`，底层是**红黑树**，插入时通过**`Comparable.compareTo()`自然排序或自定义`Comparator.compare()`的返回值判断是否为0来判断重复**



- **有序的Set是什么？记录插入顺序的集合是什么？**
  - 有序的Set
    - `TreeSet`，基于`Comparable.comparaTo`自然排序或者自定义排序`Comparator.compare`的返回值是否为0来判断重复
    - `LinkedHashSet`，基于哈希表+双向链表实现，**链表记录元素的插入顺序**，**遍历时按插入顺序输出**，属于**“保留插入顺序”**
  - 记录插入顺序的集合是`LinkedHashSet`，既保证元素唯一，又按照插入顺序遍历。

