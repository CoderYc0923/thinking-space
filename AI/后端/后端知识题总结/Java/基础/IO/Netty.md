- **总结**：Netty是**基于NIO多路复用的网络框架**，用事件驱动写TCP/HTTP等服务，用**Reactor把就绪事件分发给Handler**。服务端一般**Boss接连接**、**Worker做读写**，**连接挂在Pipeline上编解码和业务**。比手写NIO更稳定、更好扩展，适合高并发长连接和自定义协议。

  

- **原理：**

  - 通过**NIO多路复用实现非阻塞IO**
  - **Reactor模式**（**事件分发**）：**事件就绪分发给对应Handler**
    - **Reactor≈同步非阻塞**
    - **Proactor≈异步回调**
  - 读到数据后进**Pipeline（责任链式）**：**解码** → **业务** → **编码** → 写**出**



- **组件**：
  - `Bootstrp / ServerBootstrap`：**启动器，配线程、端口、Handler**
  - `EventLoopGroup`：**线程池**；里面**每个EventLoop绑定一个线程+一个Selector**
  - `Channel`：**一条连接的抽象（可读写）**
  - `ChannelPipline`：这条连接上的**处理器链**
  - `ChannelHandler`：**链上的节点（出入站逻辑）**
  - `ByteBuf`：比`ByteBuffer`更好用的**字节容器**



- **线程模型（面试高频）**
  - 常见的**主从Reactor**
    - `BossGroup`：一个或少量`EventLoop`
      - 只负责`accept`新连接
    - `WorkerGroup`：多个`EventLoop`
      - 每个连接绑定到其中一个`EventLoop`
      - 负责该连接的读、写、编解码、业务（若业务重可再丢到业务线程池）
    - **要点**：
      - 一个`Channel`终身跟一个`EventLoop`，**避免同连接并发乱序**
      - 业务别在`EventLoop`里干重活/阻塞IO，**否则拖垮整条线程上的所有连接**



- **使用场景**：
  - **RPC、网关、长连接推送、游戏服、IM**
  - **中间件或自研协议**



- **粘包/半包**
  - **TCP是字节流**，要用`LengthField`，`Delimiter`，`HttpCodec`等**解码器切出完整消息**
  - **零拷贝等优化**，`CompositeByteBuf`、文件传输`DefaultFileRegion`等

