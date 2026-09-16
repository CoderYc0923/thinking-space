锁可以从多个维度划分，不是互斥分类

- 从**并发冲突预判策略**分，可分为**悲观锁**和**排他锁**
  - `悲观锁`
    - `synchronized`、`ReentrantLock（默认悲观）`、`ReentrantReadWriteLock`
    - 原理：默认**一定会发生线程竞争冲突**，**访问共享资源前先上锁**，别的线程无法访问改共享资源
  - `乐观锁`
    - `CAS（Compose and Swap比较并交换）`、`Atomic原子类`、`数据库版本号机制`
    - 原理：默认**很少发生线程竞争冲突**，**访问共享资源前不上锁**，**等线程操作完成时校验**资源有没有被别的线程修改，**校验失败则重试**。**无阻塞**。
  
- 从**能不能多人同时占用资源**分，可分为**排他锁**和**共享锁**
  - `排他锁（写锁）`
    - `synchronized`、`ReentrantReadWriteLock.WriteLock`
    - 原理：同一时刻**只能一个线程持有锁**，其他线程全部阻塞
  - `共享锁（读锁）`
    - `ReentrantReadWriteLock.ReadLock`
    - 原理：同一时刻**可有多个线程持有锁**，**读锁之间不互斥**，**读和写 / 写和写锁之间互斥**
  
- 从**持有者能不能再获得同一把锁**分，可分为**可重入锁**和**非可重入锁**
  - `可重入锁（递归锁）`
    - `synchronized（隐式可重入）`、`ReentrantLock（显示可重入）`
    - 原理：**同一个线程已经持有锁，能够再次获取同一把锁**，**不会死锁**；通过**内部记录持有次数**，**释放锁时需要释放对应次数**
  - `不可重入锁`
    - `java`没有内置实现，需要自己手动写
    - 原理：**持有锁时，再次申请同一把锁，直接阻塞 / 死锁，必须先释放原有锁，然后再申请同一把锁**
  
- 从**排队是否严格按照先来后到**分，可分为**公平锁**和**非公平锁**
  - `公平锁`
    - `new ReentrantLock(true)`
    - 原理：线程按请求锁的**先后顺序排队，先到先得，严格`FIFO`。**
    - 缺点：**频繁切换线程**，性能较低
  - `非公平锁（默认）`
    - `synchronized`、`new ReentrantLock() 无参构造`
    - 原理：**线程抢锁不遵守排队顺序，允许插队**
    - 优点：同一线程可能可以插队，**减少线程切换，吞吐量更高**
    - 缺点：可能出现线程长时间抢不到锁。
  
- 从**拿不到锁是循环尝试还是休眠等待**分，可分为**自旋锁**和**阻塞锁**
  - `自旋锁`
    - `JUC底层CAS`、`synchronized 轻量级锁`、`LockSupport 可自定义`
    - 原理：**拿不到锁不进入阻塞休眠，而是循环不断尝试获取锁**
    - 缺点：长时间自旋消耗`CPU`
  - `阻塞锁`
    - `synchronized 重量级锁`、`ReentrantLock 阻塞逻辑`
    - 原理：**拿不到锁就进入阻塞休眠，放弃`CPU`,锁释放后由操作系统唤醒抢锁。**
  
- `synchronized`的三种状态：**偏向锁**，**轻量级锁**，**重量级锁**
  - `synchronized`根据竞争程度在对象头`Mark Word`里做锁升级，路径是`偏向锁`，`轻量级锁`，`重量级锁`，**只升不降**。**无线程竞争的时候**，用`偏向锁`，第一个线程进来，用`CAS` 把**线程ID写进对象头`Mark Word`**，该线程再次进入的时候，**只需比对一下对象头中是不是自己**，几乎零开销。一旦**出现第二个线程**，就撤销`偏向锁`，升级成`轻量级锁`，**`JVM`在线程栈里建一条锁记录**（`Lock Record`），把原来的`Mark word`拷贝进去，再**`CAS`把对象头改成指向这条锁记录**。`CAS`成功就拿到`轻量级锁`，**失败**说明有人正在抢，**就先`自旋`尝试抢锁**，`JDK1.6`以后是**自适应自旋**（该线程**上次自旋成功就多自旋几次**，一直**不成功就少自旋几次甚至不自旋**）。当**自旋**到**阈值**还抢不到锁或者**持锁期间有多个线程在抢（竞争激烈）的时候**，升级成`重量级锁`，对象头指向`ObjectMonitor`（`entryList`/ `waitList`），抢不到的线程阻塞进等待队列，释放的时候再唤醒等待线程。
  - **`JDK15`起，`偏向锁`默认关了，因为收益越来越小了**。现代应用单线程反复进同一把锁的情况减少，且撤销`偏向锁`的开销大，别的优化足够了，所以默认关了。
  
- `ReentrantLock`的原理

  - 底层实现依赖于`AQS（AbstractQueuedSynchronizer）`这个抽象类。

  - `ReentrantLock`在`AQS`的基础上通过内部类`Sync`来实现具体的锁操作。

    - **可中断性**：**等待线程可被中断而提前结束等待**

      - `ReentrantLock`实现了可中断性，这意味着线程在等待锁的过程中，可以被其他线程中断而提前结束等待。
      - 底层通过`LockSupport.park()`和`LockSupport.unpark()`相关

    - **设置超时时间：超时放弃获取锁**

      - `ReentrantLock`支持在尝试获取锁时设置超时时间，超过超时时间后，放弃锁的获取。
      - 通过内部的`tryAcquireNanos`方法来实现

    - **公平锁和非公平锁：等待线程的排队顺序，是否可插队**

      - 直接创建`ReentrantLock`对象时，默认情况下时**非公平锁**
      - 创建`ReentrantLock`时传入`true`，为**公平锁**

    - **多个条件变量**：**让线程更灵活的等待和唤醒**

      - `ReentrantLock`**支持多个条件变量**，每个条件变量可以与一个`ReentrantLock`关联。使得线程更灵活地进行等待和唤醒，而不仅仅是基于**对象监视器**的`wait()`和`notify()`

      - 多个条件变量的实现依赖于`Condition`接口

        - ```java
          ReentrantLock lock = new ReentrantLock();
          Condition condition = lock.newCondition();
          
          // 使用下面方法进行等待和唤醒
          condition.await();
          condition.signal();
          ```

    - 可重入性：

      - `ReentrantLock`支持可重入性，**一个线程可以多次获得同一把锁，而不造成死锁**。
      - 通过**`AQS`的`state`状态变量来记录可重入次数**实现。当一个线程多次获取锁时，`state`递增，释放锁时递减，只有当`state`减为0时，其他线程才有机会获取锁。

      


**synchronized vs ReentrantLock**？

- 两者都是可重入互斥锁，都能保证原子性、可见性。差别在于应用场景。
- `synchronized`适用简单同步用，基于`JVM Monitor`对象监视器
- `ReentrantLock`适合公平、可中断、超时尝试、多条件队列，基于`AQS`



**示例**

- `synchronized`：简单互斥用、临界区短

  - ```java
    // 锁方法，锁的是this
    public synchronized void increment() { count++; }
    
    // 锁代码块，锁的是指定对象，粒度更细
    private Object lock = new Object();
    synchronized (lock) { count++; }
    ```

- `ReentrantLock`：需要公平锁、可中断/超时拿锁、多条件变量、`tryLock`尝试抢锁的情况

  - ```java
    // 显式lock/unlock，支持尝试锁、可中断、超时；必须finally释放
    Lock lock = new ReentrantLock();
    lock.lock();
    try {
        count++;
    } finally {
        lock.unlock();
    }
    ```

- `ReentrantReadWriteLock`：读多写少用

  - ```java
    // 适合读多写少，多读并行，写独占
    ReadWriteLock rw = new ReentrantReadWriteLock();
    Lock r = rw.readLock(), w = rw.writeLock();
    
    // 读
    r.lock();
    try { return data; } finally { r.unlock(); }
    
    // 写
    w.lock();
    try { data = newData; } finally { w.unlock(); }
    ```

  - 

