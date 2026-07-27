整体层级关系：Java NIO（原生API，复杂难用，bug多） -> Netty（NIO封装高性能网络框架） -> Dubbo（基于Netty实现的RPC微服务框架）

## 一、Netty

1. 定位：

   - 基于JDK NIO封装的高性能、高可靠、异步事件驱动的网络通信框架
   - 解决原生NIO痛点：空轮询Bug、复杂API、缓冲区内存泄漏、粘包拆包、多线程并发处理
   - 主流用途：RPC底层通信（Dubbo、SpringCloud Alibaba）、IM聊天、网关、游戏服务器

2. 核心底层框架（基于NIO多路复用）

   - 核心线程模型：Reactor反应器模式
     - 单Reactor单线程（demo，不生产）
       - 1个线程同时负责：端口监听、连接处理、读写数据
       - 缺陷：长耗时业务阻塞整个线程，并发差
     - 单Reactor多线程（中小型服务）
       - 1个主线程负责监听连接；连接建立后交给线程池处理读写业务
       - 缺点：海量连接时，单主线程Accept存在瓶颈
     - 主从Reactor多线程（Netty默认，生产标准）
       - Main Reactor（Boss Group 老板线程组）
         - 仅负责监听端口，接收TCP连接；连接建立成功后，将SocketChannel注册给从Reactor，Boss不处理数据读写
         - 默认线程数：1（多端口监听可自动扩容）
       - Sub Reactor（Worker Group工作线程组）
         - N个线程（默认CPU核心数 * 2），每个线程绑定1个Selector
         - 负责已建立连接的IO读写事件；读写完成后交给业务线程池执行耗时逻辑

3. 核心组件

   - Channel
     - 封装TCP连接，对应NIO的SocketChannel
     - 提供网络读写、关闭、绑定地址等操作做
     - 每个客户端连接对应独立Channel
   - channelHandler & ChannelPipeline（业务处理器链）
     - ChannelPipeline
       - 每个Channel自带一条处理器双向链表；所有读写事件都会按顺序经过Pipeline内所有Handler
     - ChannelHandler：处理器，处理入站/出站数据，分两类：
       - ChannelInboundHandler：入站处理器
         - 读数据、连接建立、断开等从外部进入服务的事件（最常用：ChannelRead）
       - ChannelOutboundHndler：出站处理器
         - 写数据、连接关闭，服务向客户端发送数据
     - ChannelHandlerContext：Handler上下文，持有Channel、Pipeline，用于触发读写、刷新缓冲区
   - 编解码器Codec（解决TCP粘包拆包核心）
     - TCP时流式协议，无消息边界，多条消息会粘在一起 / 消息拆分，必须编解码器分割消息
     - 常用内置解码器
       - LineBasedFrameDecoder：按换行符\n分割消息
       - FixedLengthFrameDecoder: 固定长度消息
       - DelimiterBasedFrameDecoder：自定义分隔符
       - ProtobufVarint32FrameDecoder：Protobuf序列化专用
       - LengthFieldBasedFrameDecoder（生产最常用）：长度域解码器；消息结构【消息长度】【消息体】，自动根据长度读取完整消息，Dubbo、RPC通用
     - 编码器ProtobufEncoder、StringEncoder，出站时将对象/字符串转为字节流
   - ByteBuf（Netty自研缓冲区，替代NIO ByteBuffer）
     - 原生ByteBuffer痛点：读写切换必须flip()、无法动态扩容、索引操作繁琐
     - ByteBuf优势：
       - 双指针：readerIndex 读指针、writerIndex写指针，读写分离，无需flip
       - 自动扩容，支持堆缓冲区 / 直接缓冲区
       - 支持零拷贝、复合缓冲区CompositeByteBuf
       - 内置内存泄漏检测工具
   - ChannelFuture & Promise （异步回调）
     - Netty所有IO操作全部异步，chanel.write()、connect()不会阻塞
     - ChannelFuture：异步操作结果载体，支持addListenner()添加回调函数，操作完成自动执行
     - Promise是Future的可写版本，手动设置成功 / 失败结果

4. Netty标准服务端完整模板

   ```java
   public class NettyServer {
       public static void main(String[] args) throws InterruptedException {
           // 创建Boss\Worker线程组
           NioEventLoopGroup bossGroup = new NioEventLoopGroup(1);
           NioEventLoopGroup workerGroup = new NioEventLoopGroup();
           
           try {
               // 服务端启动引导器
               ServerBootstrap bootstrap = new ServerBootstrap();
               bootstrap.group(bossGroup,workerGroup)
                   .channel(NioServerSocketChannel.class) //指定NIO服务通道
                   .option(ChannelOption.SO_BACKLOG, 1024) //半连接队列
                   .childOption(ChannelOption.SO_KEEPALIVE,true) //长连接保活
                   // 装配处理器链
                   .childHandler(new ChannelInitializer<NioSocketChannel>() {
                       @Override
                       protected void initChannel(NioSocketChannel ch) {
                           ChannelPipeline pipeline = ch.pipeline();
                           // 长度域解码器，解决粘包拆包
                           pipeline.addLast(new LengthFieldBasedFrameDecoder(1024,0,4,0,4));
                           pipeline.addLast(new ProtobufDecoder(MessageProto.Message.getDefaultInstance()));
                           pipeline.addLast(new ProtobufEncoder());
                           //自定义业务处理器
                           pipeline.addLast(new BusinessServerHandler());
                       }
                   });
               // 绑定端口，同步等待启动完成
               ChannelFuture future = bootstrap.bind(8080).sync();
               System.out.println("Netty服务启动，端口8080");
               // 等待服务端口关闭
               future.channel().closeFuture().sync();
           } finally {
               // 优雅关闭线程池
               bossGroup.shutdownGracefully();
               workerGroup.shutdownGracefully();
           }
       }
   }
   ```

5. Netty 高频核心考点

   - Reactor 三种线程模型区别，Netty 使用哪一种？
     - 主从 Reactor 多线程模型；Boss 单线程处理连接，Worker 多线程处理 IO 读写。
   - ChannelPipeline 执行顺序
     - 入站 Handler 从头向后执行；出站 Handler 从后向前执行
   - TCP 粘包拆包产生原因及解决方案
     - TCP 无消息边界，缓冲区满自动合并；Netty 使用 LengthFieldBasedFrameDecoder 长度域解码器
   - ByteBuf 对比 NIO ByteBuffer 优势
     - 双指针无需 flip、自动扩容、内存泄漏检测、零拷贝支持
   - Netty 异步非阻塞怎么实现？
     - 基于 NIO Selector 多路复用，所有 IO 操作返回 ChannelFuture，通过监听器回调处理结果，不阻塞线程
   - SO_KEEPALIVE 心跳机制作用
     - 检测无效死连接，长时间无数据交互自动断开失效 TCP 连接，释放资源
   - Netty 内存泄漏如何排查？
     - 开启 `-Dio.netty.leakDetection.level=PARANOID` 内存泄漏检测，定位未释放的 ByteBuf
   - 优雅关闭 shutdownGracefully () 作用
     - 停止接收新连接，等待现有连接任务处理完成后再销毁线程，避免消息丢失。

## 二、Dubbo

1. 定位

   - Apache Dubbo 是一款**高性能、轻量级 Java RPC 远程调用框架**
   - 底层网络通信默认使用 Netty（NIO），实现跨进程、跨服务器方法远程调用，像调用本地方法一样调用远程服务
   - 核心功能：远程通信、服务注册发现、负载均衡、容错降级、限流、服务治理

2. 五大核心架构角色

   - Provider 服务提供者
     - 部署服务接口实现类，启动后将自身服务地址注册到注册中心
   - Consumer 服务消费者
     - 引用远程服务接口，启动时从注册中心订阅需要的服务，缓存服务提供者地址列表
   - Registry 注册中心
     - 存储服务提供者地址元数据；提供服务注册、订阅通知能力
     - 主流实现：Nacos（推荐）、Zookeeper、Redis
   - Monitor 监控中心
     - 采集服务调用次数、耗时、异常率，可视化监控面板（Dubbo Admin）
   - Container 服务容器
     - 服务运行容器，Spring 容器最常用（SpringBoot 整合 Dubbo）

   完整调用流程

   - Provider 启动，将 `接口名+IP+端口` 注册到注册中心
   - Consumer 启动，向注册中心订阅目标服务
   - 注册中心推送所有 Provider 节点地址给 Consumer，本地缓存
   - Consumer 发起远程调用，本地通过负载均衡算法选择一个 Provider 节点
   - Consumer 通过 Netty 建立 TCP 长连接，发送 RPC 请求
   - Provider 接收请求，反射执行目标接口方法，结果通过 Netty 返回 Consumer
   - 注册中心感知 Provider 上下线，实时推送更新地址列表给 Consumer

3. Dubbo 核心核心配置与组件

   - 通信层：Netty 传输
     - Dubbo 默认传输协议 `dubbo` 协议，底层基于 Netty4 实现 TCP 长连接
     - 特点：二进制协议、序列化体积小、性能高，适合内网微服务调用
     - 其他协议：http、grpc、rmi（极少使用）
   - 序列化机制（高频考点）
     - RPC 调用需要将 Java 对象转为二进制网络传输，主流序列化方案：
       - **Hessian2（Dubbo 默认）**：跨语言、兼容性好，平衡性能与兼容性
       - Protobuf：序列化体积最小、速度最快，需提前编写 proto 文件
       - Java 原生序列化：性能差、体积大、存在安全漏洞，禁止使用
       - Fastjson2：JSON 序列化，可读性高，适合调试
   - 负载均衡策略（Consumer 调用时选择节点）
     - `random` 随机（默认）：加权随机，性能好，生产默认
     - `roundrobin` 轮询：按权重依次分发请求
     - `leastactive` 最少活跃调用：优先选择当前并发压力小的服务节点
     - `consistenthash` 一致性哈希：相同参数固定路由到同一节点，适合会话黏连场景
   - 集群容错策略（Provider 节点故障时处理方案）
     - 多个服务提供者集群部署，调用失败后的容错机制：
       - `failover` 失败自动切换（默认）：失败自动重试其他节点，适合读接口；**写接口禁用，会重复提交**
       - `failfast` 快速失败：只发起一次调用，失败直接抛出异常，适合新增 / 支付等幂等写操作
       - `failsafe` 失败安全：调用失败直接忽略，返回空，日志记录，适合日志、埋点无关紧要接口
       - `failback` 失败自动恢复：后台定时重试失败请求，适合异步消息通知
       - `forking` 并行调用多个节点，取第一个成功返回，实时高可用场景
   - 服务注册中心 Nacos / Zookeeper
     - Zookeeper：经典注册中心，临时节点实现服务上下线感知
     - Nacos：阿里开源，同时支持注册中心 + 配置中心，轻量易用，SpringCloud 生态互通，现在主流推荐

4. SpringBoot 整合 Dubbo 最简代码示例

   - 服务提供者（Provider）

     - pom依赖

     - ```xml
       <dependency>
           <groupId>org.apache.dubbo</groupId>
           <artifactId>dubbo-spring-boot-starter</artifactId>
           <version>2.7.15</version>
       </dependency>
       <dependency>
           <groupId>com.alibaba.nacos</groupId>
           <artifactId>nacos-client</artifactId>
       </dependency>
       ```

     - application.yml

     - ```yaml
       dubbo:
         application:
           name: dubbo-provider
         registry:
           address: nacos://127.0.0.1:8848
         protocol:
           name: dubbo
           port: 20880
       ```

     - 定义接口

     - ```java
       public interface UserService {
           String getUserInfo(Long userId);
       }
       ```

     - 接口实现（@DubboService 暴露服务）

     - ```java
       import org.apache.dubbo.config.annotation.DubboService;
       
       @DubboService
       public class UserServiceImpl implements UserService {
           @Override
           public String getUserInfo(Long userId) {
               return "用户ID：" + userId + "，Dubbo远程调用成功";
           }
       }
       ```

     - 启动类

     - ```java
       import org.apache.dubbo.config.spring.context.annotation.EnableDubbo;
       import org.springframework.boot.SpringApplication;
       import org.springframework.boot.autoconfigure.SpringBootApplication;
       
       @SpringBootApplication
       @EnableDubbo
       public class ProviderApplication {
           public static void main(String[] args) {
               SpringApplication.run(ProviderApplication.class);
           }
       }
       ```

   - 服务消费者（Consumer）

     - application.yml

     - ```yaml
       dubbo:
         application:
           name: dubbo-consumer
         registry:
           address: nacos://127.0.0.1:8848
       ```

     - 远程引用服务 @DubboReference

     - ```java
       import org.apache.dubbo.config.annotation.DubboReference;
       import org.springframework.web.bind.annotation.GetMapping;
       import org.springframework.web.bind.annotation.RestController;
       
       @RestController
       public class UserController {
           // 远程注入RPC服务
           @DubboReference
           private UserService userService;
       
           @GetMapping("/user")
           public String getUser() {
               // 像本地方法调用远程服务
               return userService.getUserInfo(10001L);
           }
       }
       ```

5. Dubbo 高频核心面试考点

   - Dubbo 架构五大角色及完整调用流程
     - Provider、Consumer、Registry、Monitor、Container；
     - 完整注册、订阅、远程调用、通知流程
   - Dubbo 默认通信框架、协议、序列化方案
     - 底层 Netty；dubbo 二进制 TCP 协议；默认 Hessian2 序列化
   - 五种集群容错策略区别，默认是哪一种？读写接口如何选择？
     - 默认 failover 失败重试；查询接口可用 failover；新增、支付写接口使用 failfast 快速失败，防止重复请求
   - 四种负载均衡策略适用场景
     - random 加权随机默认；leastactive 应对节点压力不均；consistenthash 会话黏连
   - 注册中心 Nacos 对比 Zookeeper 优势
     - Nacos 同时支持注册 + 配置中心，性能更高，AP 架构，可用性更强，适配云原生；Zookeeper 是 CP 架构，集群故障会影响服务注册
   - Dubbo 和 SpringCloud OpenFeign 核心区别
     - Dubbo：基于 Netty TCP 长连接，二进制序列化，性能高，专为内网微服务 RPC
     - OpenFeign：基于 HTTP 短连接，JSON 序列化，跨语言友好，适合对外 HTTP 接口
   - failover 重试会带来什么问题？如何解决？
     - 写操作会产生重复请求（重复下单、重复扣款）；解决方案：接口实现幂等（唯一业务号、数据库唯一索引），写接口切换为 failfast
   - Dubbo 超时配置如何生效，超时后会发生什么？
     - 通过 timeout 配置调用超时；超时触发集群容错策略，failover 自动重试其他节点
   - @DubboService 和 @DubboReference 作用
     - @DubboService：将当前实现类注册为 RPC 服务，上报注册中心
     - @DubboReference：动态生成远程服务代理，本地调用转发至远程 Netty 连接
   - Dubbo 服务雪崩如何治理？
     - 通过限流、降级、熔断、超时控制、集群容错、隔离线程池实现服务保护

6. Netty 与 Dubbo 关联总结

   - Dubbo 的 dubbo 协议底层通信完全依赖 Netty 框架
   - Netty 负责 TCP 长连接、异步 IO、粘包拆包处理、二进制传输
   - Dubbo 在 Netty 基础上封装了 RPC 能力：服务注册发现、负载均衡、容错、序列化、代理调用，让开发者无需关注底层网络，只需要编写业务接口