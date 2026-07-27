# 20. IO 流

## 含义

1. I = Input输入（读数据，外部 -> 程序内部）
2. O = Output输出（写数据，程序内部 -> 外部）
3. 外部资源：文件、网络Socket、内存数组、管道、控制台。

## 分类

1. 字节流 InputStream/OutputStream：

   - 操作最小单位：1字节byte（8bit）
   - 处理二进制文件：图片、视频、音频、exe、压缩包
   - 所有文件底层都是字节，字节流万能，任何文件都能读写

2. 字符流 Reader/Writer：

   - 操作最小单位：1字符char（16bit）
   - 专门处理文本文件：txt,java,md,html
   - 内置编码解码，自动处理中文乱码，不能处理图片等二进制

3. 四大抽象顶层父类

   1. | 类型   | 输入（读）  | 输出（写）   |
      | ------ | ----------- | ------------ |
      | 字节流 | InputStream | OutputStream |
      | 字符流 | Reader      | Writer       |

      抽象类，不能被new，只能用它的实现类




## 字节流

1. 文件字节流（基础节点流，直接操作文件）

   - FileInputStream文件读、FileOutputStream文件写

     - ```java
       // 写入文件
       try (FileOutStream fos = new FileOutStream("test.txt")) {
           String str = "测试内容";
           fos.write(str.getBytes()); //字符串转字节数组写入
       } catch (IOException e) {
           e.printStackTrace();
       }
       
       // 读取文件
       try (FileInputStream fis = new FileInputStream("test.txt")) {
           byte[] buf = new byte[1024]; // 缓冲区数组
           int len;
           // read() 返回读取到的字节数，读到文件末尾返回 -1
           while ((len = fis.read(buf))  != -1) {
               System.out.println(new String(buf,0,len));
           }
       } catch (IOException e) {
           e.printStackTrace();
       }
       ```

     - 考点：文件追加写入

       - new FileOutputStream("test.txt", true)
       - 第二个参数true: 追加，false/不传：覆盖原文件

2. 缓冲字节流（包装流，增加缓冲区，减少 IO 磁盘交互，大幅提升读写性能）

   - BufferedInputStream缓冲读、BufferedOutputStream 缓冲写

   - 底层自带默认8KB字节缓冲区，减少磁盘IO次数，大幅提升速度

   - 节点流是原料，缓冲流是包装器，必须套在节点流外面

   - ```java
     // 缓冲写入
     try (BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream("a.txt"))) {
         bos.write("缓冲流".getBytes());
         bos.flush(); //强制刷新缓冲区，数据写入磁盘
     }
     ```

   - 高频坑点：flush()
     - 缓冲区满了才会自动写入磁盘；如果数据量很小，缓冲区没满，程序直接关闭则会丢失数据
     - flush()：手动刷新缓存区，把缓存数据写入文件
     - close()：关闭流前会自动执行一次flush()

3. 对象字节流（序列化/反序列化，高频面试）

   - ObjectInputStream 反序列化（读对象）
   - ObjectOutputStream 序列化（写对象）
   - 作用：把Java对象写入文件/网络传输，再读取还原对象
   - 强制要求（必考）
     - 实体类必须实现标记接口Serializable（无任何方法，仅标记可序列化）
     - 序列化版本号 private static final long serialVersionUID = 1L;
       - 不手动定义：编译器自动生成，修改实体类字段后版本号变化，反序列化直接报错
       - 手动固定值：新增/删除字段，旧序列化我呢见依然能正常读取，兼容历史数据
   - 关键字transient（考点）
     - 被transient修饰的成员变量不会参与序列化，反序列化后该字段为默认值（数字0，对象null）
     - 适用场景：临时缓存，敏感密码，不需要持久化

4. 内存字节流（ByteArray）

   - ByteArrayInputStream / ByteArrayOutputStream
   - 数组读写在内存数组中，不操作磁盘，无需关闭流（close无实际作用）



## 字符流

1. 文件字符流（FilRaeader / FileWriter）

   - 底层封装字节流 + 默认平台编码（Windows GBK, Linux/Mac UTF-8）

   - 致命坑（高频错题）

     - 直接使用FileReader读写带中文的跨平台文件，编码不匹配产生中文乱码，生产禁止直接使用FileReader/FileWriter，改用InputStreamReader / OutputStreamWriter制定编码

     - 原因：FileReader和FileWriter底层自动获取操作系统默认字符集，Windows默认GBK、服务器默认UTF-8，跨环境运行会产生中文乱码，编写不受代码控制，线上极易引发故障。而InputStreamReader / OutputStreamWriter作为字节流转字符流的转换桥梁，支持手动指定固定编码（统一utf-8），不受操作系统影响，彻底解决跨环境乱码问题，因此生产环境必须使用转换流，禁止直接使用FileReader / FileWriter 

       - Java11提供简易文件工具Files.readString，同样可以直接指定编码，代替底层转换流（底层依然封装了 `InputStreamReader`，核心思想不变：**显式指定编码**）

       - ```java
         // 直接指定UTF-8，简洁安全
         String content = Files.readString(Paths.get("config.txt"), StandardCharsets.UTF_8);
         ```

2. 转换流（字节 -> 字符桥梁，解决乱码核心）

   - InputStreamReader 字节输入 -> 字符输入

   - OutputStreamWriter 字符输出 -> 字节输出

   - 唯一可以手动指定编码集（UTF-8/GBK）的基础字符流，解决乱码标准答案

   - ```java
     // 读取utf-8编码文本文件
     try (FileInputStream fis = new FileInputStream("utf.txt");
          InputStreamReader isr = new InputStreamReader(fis, StandardCharsets.UTF_8);
          BufferedReader br = new BufferedReader(isr)) {
         String line;
         // readLine() 读取一整行字符串，返回null代表文件末尾
         while ((line = br.readLine()) != null) {
             System.out.println(line);
         }
     }
     ```

3. 缓冲字符流（BufferReader / BufferWriter）

   - 字符缓冲流独有便捷方法
     - BufferReader.readLine() 按行读取文本，无换行符
     - BufferWriter.newLine() 跨平台换行符（替代\n,兼容Windows \r\n）

4. 打印流 PrintWriter

   - 便捷输出工具，自带自动刷新，print/println支持所有基础类型、对象打印



## 流的分类标准

1. 按流向：输入流、输出流
2. 按处理单位：字节流、字符流
3. 按功能分层
   - 节点流（原始流）：直接对接目标资源（FileInputStream、ByteArrayInputStream）
   - 包装流/处理流：套在其他流外层，增强功能（缓冲流、转换流、对象流）



## 资源关闭规范 try-with-resources（核心考点）

自动关闭流，避免忘记 close 导致资源泄漏

1. 历史旧写法（缺陷多）

   ```java
   FileInputStream fis = null;
   try {
       fis = new FileInputStream("1.txt");
   } catch (IOException e) {
       e.printStackTrace();
   } finally {
       // 必须手动判断非空再关闭，代码冗余
       if (fis != null ){
           try {
               fis.close();
           } catch (IOException e) {}
       }
   }
   ```

   

2. Java7 + 标准写法try-with-resources（推荐）

   ```java
   // 实现 AutoCloseable 接口的资源（所有 IO 流、连接），放入 try () 括号内，代码块执行完毕自动关闭资源，无需手动 close，finally 都可以省略。
   
   try(BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream("test.txt"), StandardCharsets.UTF_8))) {
       String line = br.readLine();
   } catch (IOException e) {
       e.printStackTrace();
   }
   ```



## 高频核心考点汇总（面试 / 笔试必背）

1. 字节流和字符流区别（简答必考）
   - 处理单位：字节流 byte (8 位)，字符流 char (16 位)
   - 适用文件：字节流处理所有文件（二进制、文本）；字符流仅处理文本文件
   - 编码：字节流不涉及编码；字符流底层依赖编码，容易乱码
   - 顶层父类：InputStream/OutputStream、Reader/Writer
   - 缓冲区：字节流缓冲 8KB byte 数组；字符流缓冲 char 数组
2. 什么时候用字节流，什么时候用字符流？
   - 字节流：图片、视频、音频、压缩包、exe、网络二进制传输；
   - 字符流：纯文本文件（txt、html、java、json），需要读取文本行、处理中文
3. 转换流作用？为什么 FileReader 容易乱码？
   - 转换流是字节流与字符流中间桥梁，可以手动指定读写文件编码（UTF-8/GBK）
   - FileReader 底层使用操作系统默认编码，Windows 是 GBK，Linux 是 UTF-8，跨平台读写文本就会出现中文乱码；生产环境统一使用 InputStreamReader 指定 UTF-8
4. flush () 和 close () 区别
   - flush ()：强制把缓冲区缓存数据写入磁盘，流不会关闭，后续可继续读写
   - close ()：先自动执行一次 flush ()，然后关闭 IO 流，释放操作系统文件句柄；流关闭后无法继续读写，会抛出 IO 异常
5. 序列化相关考点
   - 序列化接口 Serializable 是标记接口，无抽象方法
   - serialVersionUID 作用：兼容实体类字段变更，防止反序列化失败
   - transient 关键字修饰的字段不参与序列化，反序列化取默认值
   - 静态 static 变量不属于对象，序列化不会保存静态变量值
6. 包装流与节点流区别
   - 节点流：直接绑定文件 / 数组等资源，是最底层的流
   - 处理流（包装流）：构造方法传入其他流对象，不直接操作资源，用于增强功能（缓冲、编码转换、序列化）
   - 关闭规则：只需要关闭最外层包装流，内层节点流会自动关闭



## 易错查漏补缺（90% 人踩过的坑）

1. 使用 FileWriter 写中文乱码
   - 解决方案：放弃 FileWriter，使用 `new OutputStreamWriter(new FileOutputStream("xxx.txt"), StandardCharsets.UTF_8)` 强制指定 UTF-8 编码。
2. 缓冲流写入少量数据，文件空白丢失数据
   - 原因：数据不足缓冲区容量，未自动刷盘，程序直接结束；
   - 解决：写完调用`bos.flush()`，或使用 try-with-resources 自动 close 刷盘。
3. 序列化实体类没加 serialVersionUID，修改字段后反序列化报错
   - 解决：手动固定版本号 `static final long serialVersionUID = 1L;`
4. 读取文件循环判断条件写错，死循环或读不全
   - 错误写法：`while(fis.read(buf) != -1)` 但打印时直接 new String (buf)，读取最后一段数据不足数组长度，会拼接上一次残留字节；
   - 正确写法：`new String(buf, 0, len)` 只截取本次读取到的有效字节
5. 字符流读取二进制文件（图片）导致文件损坏
   - 字符流会按照编码规则解析字节，无法识别二进制字节，解析过程会破坏原始数据；图片、压缩包必须使用字节流
6. 流关闭遗漏，造成文件句柄泄漏
   - 大量 IO 操作不关闭流，操作系统文件句柄耗尽，程序抛出无法打开文件异常
   - 解决方案：统一使用 try-with-resources 自动关闭所有流
7. transient 修饰静态变量无意义
   - 静态变量本身属于类，不属于实例对象，序列化本来就不会存储静态变量，加 transient 不会有任何变化



## BIO/NIO/AIO

1. 基础区分

   - BIO
     - 同步：读写操作主线程等待完成，不能干别的
     - 阻塞：无数据时，线程卡死等待，不能释放
     - 模型：一线程已连接，上万连接会创建上万线程，内存耗尽、CPU上下文切换爆炸
     - 适用：连接数少、短连接（普通本地文件读写）
   - NIO（NEW IO / Non-Blocking IO, 同步非阻塞）
     - JDK1.4引入，核心用于网络高并发（Netty底层基于NIO）
     - 同步：读写操作主线程等待完成，不能干别的
     - 非阻塞：没有数据时线程不阻塞，立刻返回，可以去处理其他连接
     - 核心模型：单线程 / 少量线程处理大量连接，通过Selector多路复用实现
     - 适用：高并网络服务（网关、IM、RPC框架）
   - AIO（异步非阻塞NIO2,JDK7+）
     - 异步：内核数据准备完成后ii主动回调通知程序，线程全程无需轮询
     - Windows支持差，Linux下依赖epoll，实际项目很少使用，主流还是NIO+Netty

2. 三大核心组件（Channel通道，Buffer缓冲区，Selector选择器）

   - Channel通道

     - 特点：

       - 双向读写（BIO流单向，输入流是能读，输出流只能写）
       - 读写必须配合Buffer，不能直接读写
       - 支持非阻塞模式（核心区别BIO）

     - 常用Channel实现类

       - FileChannel：文件通道，仅支持阻塞，不支持Selector多路复用
       - SocketChannel：TCP客户端网络通道，非阻塞，Selector管理
       - ServerSocketChannel：TCP服务端监听通道，非阻塞
       - DatagramChannel：UDP通道

     - FileChannel文件赋值示例（NIO文件操作）

       - ```java
         try(FileChannel in = FileChannel.open(Paths.get("a.txt"), StandardOpenOption.READ);FileChannel out = FileChannel.open(Paths.get("b.txt"),StandardOpenOptions.CREATE,StandardOpenOptions.WRITE)) {
             ByteBuffer buf = ByteBuffer.allocate(1024);
             while(in.read(buf) != -1) {
                 buf.flip();
                 out.write(buf);
                 buf.clear();
             }
         }
         ```

       - 

   - Buffer缓冲区（数据容器）

     - 概念

       - 所有NIO读写不能直接操作Channel，必须经过Buffer
       - 本质是一块内存数组，用来存放读写数据
       - 常用实现类
         - ByteBuffer（唯一用于网络/文件）
         - CharBuffer\IntBuffer\LongBuffer等基础类型缓冲区

     - Buffer四大核心标记

       - capacity：容量，缓冲区最大存储长度，创建后永远不可修改
       - limit：界限，读写上限
         - 写模式：limit = capacity
         - 读模式：limit = 写入数据的末尾位置
       - position：当前指针位置，下一个读写的下标
       - mark：标记，临时记录posiiton，reset()可以回到mark位置

     - 关键切换方法（必考）

       - flip() 写模式 -> 读模式
         - limit = position
         - posiiton = 0
         - 作用：写完数据后，切换准备读取缓冲区内容
       - clear() 读模式 -> 清空重置，回到写模式
         - position = 0,limit = capacity,mark = -1
         - 注意：不会清空底层数组数据，只是重置标记
       - rewind() 重读，position置0，limit不变
       - mark() 标记当前position；reset()回到mark位置

     - BypeBuffer两种模式示例

       - ```java
         // 分配堆缓冲区（JVM堆内存，频繁IO效率低）
         ByteBuffer buffer = ByteBuffer.allocate(1024);
         //写数据
         buffer.put("hello".getBytes());
         //切换读模式
         buffer.flip();
         //循环读取
         while(buffer.hasRemaining()) {
             byte b = buffer.get();
             System.out.print((char)b);
         }
         // 重置，准备下一次写入
         buffer.clear();
         ```

     - 堆缓冲区 vs 直接缓冲区

       - allocate() 堆缓冲区：JVM堆，GC回收，数据需要拷贝到内核缓冲区
       - allocateDirect() 直接缓冲区：操作系统内核内存，减少一次数据拷贝，高性能网络场景使用；创建销毁开销大，GC回收慢

   - Selector选择器（多路复用器）（NIO灵魂，网络高并发内核）

     - 作用：单个线程管理多个Channel，轮询查询哪些Channel已经就绪（可读，可写，有连接），避免BIO一线程一连接的资源浪费。

     - 三大角色关系：多个Channel ->注册到同一个Selector -> 单个线程循环遍历Selector获取就绪通道

     - 4种注册就绪时间（枚举SelectionKey，必考）

       - Channel注册到Selector时，需要声明监听的事件：
         - SelectionKey.OP_ACCEPT：服务端通道收到新客户端连接（仅 ServerSocketChannel）
         - SelectionKey.OP_CONNECT：客户端通道与服务端连接完成
         - SelectionKey.OP_READ：通道有数据可读
         - SelectionKey.OP_WRITE：通道缓冲区可写入数据

     - Selector 核心方法

       - Selector.open() 创建多路复用器
       - channel.register(selector, 事件) 通道注册到选择器，监听指定事件，返回 SelectionKey（通道与事件绑定的载体）
       - selector.select() 阻塞等待，直到至少一个通道就绪
       - selector.select(1000) 限时阻塞，超时返回
       - selector.selectorNow() 非阻塞，立刻返回就绪通道数量
       - selector.selectedKeys() 获取所有就绪通道对应的 SelectionKey 集合

     - NIO服务端最简完整代码（标准多路复用模型）

       - ```java
         public class NioServer {
             public static void main(String[] args) throws IOException {
                 // 1.创建Selector
                 Selector selector = Selector.open();
                 // 2.创建服务端通道，绑定端口
                 ServerSocketChannel serverChannel = ServerSocketChannel.open();
                 serverChannel.bind(new InetSocketAddress(8888));
                 // 3.设置非阻塞（必须，否则Selector失效）
                 serverChannel.configureBlocking(false);
                 // 4.注册到Selector，监听ACCEPT连接事件
                 serverChannel.register(selector, SelectionKey.OP_ACCEPT);
                 
                 // 循环轮询就绪事件
                 while(true) {
                     selector.select();
                     Set<SelectionKey> keySet = selector.selectedKeys();
                     Iterator<SelectionKey> iter = keySet.iterator();
                     while(iter.hasNext()) {
                         SelectorKey key = iter.next();
                         iter.remove(); //必须手动删除，否则重复处理
                         if (key.isAcceptable()) {
                             //新连接事件
                             ServerSocketChannel server = (ServerSocketChannel) key.channel();
                             SocketChannel client = server.accept();
                             client.configureBlocking(false);
                             //客户端通道注册事件
                             client.register(selector, SelectionKey.OP_READ);
                             System.out.println("客户端连接成功");
                         } else if (key.isReadable()){
                             // 客户端有数据可读
                             SocketChannel client = (SocketChannel) key.channel();
                             ByteBuffer buf = ByteBuffer.allocate(1024);
                             int len = client.read(buf);
                             if (len <= 0) {
                                 // 客户端断开连接，关闭通道
                                 client.close();
                                 continue;
                             }
                             buf.flip();
                             String msg = new String(buf.array(),0,buf.remaining());
                             System.out.println("收到客户端消息：" + msg);
                             // 回写数据
                             buf.clear();
                             buf.put("收到".getBytes());
                             buf.flip();
                             client.write(buf);
                         }
                     }
                 }
             }
         }
         ```

3. 零拷贝（NIO高性能核心考点）

   - 传统BIO文件传输四次拷贝

     - 磁盘文件 到 内核缓冲区（DMA拷贝，无CPU参与）
     - 内核缓冲区 到 JVM堆缓冲区 （CPU拷贝）
     - JVM堆缓冲区 到 Socket内核缓冲区 （CPU拷贝）
     - Socket内核缓冲区 到 网卡（CPU拷贝）

   - NIO零拷贝transferTo() / transferFrom()

     - 文件通道直接在内核缓冲区传输，消除两次CPU拷贝，仅两次DMA拷贝，无需JVM堆内存中转，大文件传输性能提升数倍

     - ```java
       // 零拷贝复制文件
       try(FileChannel read = FileChannel.open(Paths.get("1.mp4"), StandardOpenOptions.READ);FileChannel write = FileChannel.open(Paths.get("2.mp4"), StandardOpenOptions.CREATE, StandardOpenOptions.WRITE)) {
           read.transferTo(0, read.size(), write);
       }
       ```

     - 面试简答：零拷贝不是完全无拷贝，而是无CPU参与的用户态内核态之间拷贝，减少上下文切换与内存复制开销

4. NIO高频核心考点

   - BIO、NIO、AIO 三者区别
     - BIO：同步，阻塞，1连接1线程，适用于少量连接、本地文件
     - NIO：同步，非阻塞，多路复用，少量线程处理大量连接，适用于高并发网络、Netty
     - AIO：异步，非阻塞，内核回调，适用于文件异步读写，极少用于网络
   - NIO 三大组件作用
     - channel：通道，配合buffer双向读写，分文件、TCP、UDP通道
     - buffer：缓冲区，所有数据读写载体，底层数组，四大标记控制读写切换（capacity,limit,position,mark）
     - selector：多路复用器，单线程管理大量非阻塞channel，轮询就绪事件，解决BIO线程爆炸问题
   - Buffer flip ()、clear ()、rewind () 区别
     - flip()： 写转读，标记limit=position,position=0；读取数据必备，底层数组数据不清空
     - clear()：重置所有标记，读转写，不会清空底层数组数据
     - rewind()：position置为0.limit不变，用于重复读取缓冲区
   - SelectionKey 四种事件分别适用什么通道
     - ON_ACCEPT：仅ServerSocketChannel，监听新TCP客户端连接
     - ON_CONNECT：SocketChannel客户端，与服务端TCP连接建立完成
     - ON_READ：SocketChannel/FileChannel，通道有数据可读取
     - ON_WRITE：SocketChannel，内核发送缓冲区空闲，可以写入数据
   - 什么是多路复用？为什么 NIO 可以支持高并发？
     - 多路复用：一个Seloctor线程同时监控成千上万非阻塞channel，轮询只处理已经就绪的通道，空闲连接不占用线程资源。
     - BIO每个连接独占线程，上万连接创建上万线程，内存、CPU切换开销巨大；NIO少量线程管理海量连接，是RPC、网关、Netty底层核心
   - 什么是零拷贝？transferTo 优势
     - 传统IO需要内核缓冲区与JVM堆之间两次CPU拷贝；NIO FileChannel.transferTo直接在内核缓冲区完成数据传输，消除CPU拷贝，减少用户态内核态上下文切换，大文件/网络传输性能大幅提升
   - FileChannel 能否注册到 Selector？
     - 不同，FileChannel仅支持阻塞模式，不支持非阻塞，无法和Selector多路复用配合，Selecotr只适用于网络Socket通道
   - 堆缓冲区 allocate () 和直接缓冲区 allocateDirect () 区别
     - allocate ：内存位于JVM堆，GC自动回收；读写数据需要内核<->堆内存拷贝，网络IO性能差
     - allocateDirect ：操作系统内核物理内存，不占用堆空间；读写直接操作内核，省去一次拷贝，高性能网络场景使用；创建销毁开销更大，GC回收慢，长期不使用容易内存泄漏
   - NIO 同步非阻塞如何理解？
     - 同步：数据读取动作仍然由应用线程主动发起，线程需要主动轮询Selector查看通道是否就绪，内核不会主动通知程序
     - 非阻塞：通道无就绪数据时，read/accept操作不会阻塞线程，立即返回，线程可以处理其他通道任务
   - NIO 存在什么经典问题（epoll 空轮询，Netty 解决方案）
     - Linux 下 Selector 会出现空轮询 bug：通道无就绪事件，但 selector.select () 持续返回 0，线程无限空循环，CPU100%
     - Netty 解决方案：定时重建新 Selector，替换产生空轮询的旧选择器

5. 易错查漏补缺

   - 误区：NIO 就是非阻塞 IO
     - 纠正：NIO 包含阻塞 FileChannel 和非阻塞 SocketChannel；只有网络通道支持非阻塞 + Selector 多路复用
   - 误区：flip () 会清空缓冲区数据
     - 纠正：flip () 仅修改 position 和 limit 标记，底层字节数组数据完全保留
   - 误区：Selector 多线程操作安全
     - 纠正：Selector、SelectionKey 非线程安全，多线程并发注册、删除通道会出现并发异常，标准实现单线程处理 Selector 轮询
   - 误区：零拷贝完全没有数据复制
     - 纠正：零拷贝仅消除 CPU 拷贝，DMA 硬件拷贝依然存在，只是不需要 CPU 参与内存复制
   - 误区：AIO 性能一定优于 NIO
     - 纠正：Linux 下 AIO 对网络支持很差，主流中间件（Netty、Dubbo）全部基于 NIO 实现，AIO 仅用于本地文件异步读写

   

