# 20. IO 流

## 分类

1. 字节流 InputStream/OutputStream：处理图片、视频、所有文件
2. 字符流 Reader/Writer：仅处理文本文件，自动处理编码

## 缓冲流

Buffered 系列，增加缓冲区，减少 IO 磁盘交互，大幅提升读写性能

## try-with-resources

自动关闭流，避免忘记 close 导致资源泄漏

## NIO 简述

非阻塞 IO，同步通道，高并发网络编程使用，区别传统阻塞 IO。