Java Object类是所有类的超类，默认提供**11**个核心方法，核心用于对象比较、哈希、字符串表示、线程同步等

- **`equals`**

  - 默认实现是比较两个对象的内存地址，和`==`效果一样。

  - **重写`equals`必须重写`hashCode`**，因为`Java`约定**若两个对象`equals`返回true，他们的`hashCode`必须相等**；若**`hashCode`不相等，equals一定返回false**。不然会导致对象在`HashMap/HashSet`等**集合中无法正确存储**

  - `JDK`部分类（`String`,`Integer`,`List\Set\Map`）已经重写比内容。

  - 自定义类没重写还是比地址

  - 重写主要是为了比如：

    - 放进集合能正确去重 / 查找
      - `HashSet`,`HashMap`的key靠`equals`+`hashCode`。两个User都是id=1,若没重写，会被当成两个不同对象
    - 字符串、数字等「值语义」
      - `String`、`Integer` 等：你关心的是字面/数值相不相等，不是是不是同一个实例。
      - `"abc" == "abc"` 有时是 true（常量池），不可靠；该用 `equals`。
    - 业务对象判等
      - 订单号相同算同一单、手机号相同算同一用户等——和是不是 `new` 了两次无关。
    - 测试、比较、去重逻辑
      - `assertEquals`、列表里 `contains` 等，通常也走 `equals`。

  - ```java
    // 重写equals必须同时重写HashCode
    class User {
        private int id;
        private String name;
        
        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (obj == null || getClass() !== obj.getClass()) return false;
            
            User user = (User) obj;
            return id == user.id;
        }
        
        @Override
        public int hashCode() {
            return Integer.hashCode(id);
        }
    }
    ```

  - 

  - 

- **`toString`**

  - 默认返回**”类名+@+对象的哈希码十六进制**“，如：`User@1b6d3586`

  - 实际开发中可重写自定义，如

  - ```java
    @Override
    public String toString() {
        return "User{id=}" + id + ",name="+name+"}";
    }
    ```

  - 

- **`getClass`**

  - 返回对象**运行时的实际类对象**，和**编译时类型可能不同**

  - 这个方法**不能重写**

  - 常用于**反射场景**，如通过`getClass`获取类的属性和方法。

  - ```java
    Animal animal = new Dog();
    Class<?> clazz = animal.getClass();
    System.out.println(clazz.getName()); //输出Dog
    ```

  - 

- **`clone`**

  - 默认用于创建对象的**浅拷贝**

  - 使用`clone`需要让类实现`Cloneable`接口，否则抛出`ClassNotSupportedException`

  - ```java
    class Product implements Cloneable {
        private String name;
        private Decimal price;
        
        @Override
        protected Object clone() throws CloneNotSupportedException {
            return super.clone();
        }
    }
    ```

  - 

- **`notify`和`notifyAll`**

  - 用于**多线程同步**，和`synchronized`配合使用，用来**唤醒等待当前对象锁**的线程
  - `notify`是**随机唤醒一个等待线程**
  - `notfyAll`是**唤醒全部等待线程**
  - 比如生产者消费者模式下，生产者生产完数据后调用`notifyAll`，唤醒等待的消费者线程

- **`wait`**

  - 作用是让当前持有对象锁的线程释放锁并进入等待状态，直到被`notify`或`notifyAll`唤醒或者等待时间到期

  - 需要在**`synchronized`同步块或者方法中**使用，否则会抛`IllegalArgumentException`

  - ```java
    synchronized (lockObj) {
        while (条件不满足) {
            lockObj.wait(1000); // 等待1秒，超时唤醒
        }
        // 执行业务逻辑
    }
    ```

  - 

- **`finalize`**

  - **对象被垃圾回收器回收前**会调用的方法，**默认是空实现**
  - 但现在不推荐使用了，因为**它执行的时机不确定**，`Java9`被标记过时
  - 替代方案是`try-with-resources`或`PhantomReference`来处理资源释放

  