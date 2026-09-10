```java
public class singleTon {
    // volatile 关键字修饰变量，防止指令重排序
    private static volatile SingleTon instance = null;
    private SingleTon() {}
    
    public static SingleTon getInstance() {
        if (instance == null) {
            // 同步代码块
            // 只有在第一次获取对象的时候会执行
            synchronized(SingleTon.class) {
                if (instance == null) {
                    instance = new SingleTon();
                }
            }
        }
        
        return instance;
    }
}
```

- 实现单例一般需要用到`volatile`和`synchronized`
  - `volatile`保证可见性和禁止指令重排序，所以保证其他线程可访问到一个初始化完成的对象
  - `synchronized`保证创建单例时不会并发new多次