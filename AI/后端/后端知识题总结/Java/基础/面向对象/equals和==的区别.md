- ==，基本数据类型比值，引用类型 **比地址**
- `equals` 是Object类定义的一个方法，默认**比地址**。但`Java`中很多常用的类都重写了来比**对象中时实际存储的内容是否相等**了。
  - **重写`equals`必须重写`hashCode`**，因为`Java`约定`equals`为true的`hashCode`必须相等，`hashCode`不相等的`equals`必须为false。不然的话，会发生hash冲突，使用集合的时候的一些去重、存储、查找都会出问题。

