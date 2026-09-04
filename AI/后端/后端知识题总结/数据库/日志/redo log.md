redo log 重做日志，是物理日志

作用：记录修改后的数据状态，并持久化到磁盘，当事务崩溃时能够恢复数据，保证事务的D持久性

实现：

- 产生的redo log先写入redo log buffer（默认16MB，可通过`innodb_log_Buffer_size`动态调整大小，调大可以让MySQL处理大事务时不必写入磁盘，提升IO性能） ，然后在合适的时机刷盘
  - 具体刷盘时机：
    - MySQL正常关闭时
    - 当redo log buffer中的记录写入量大于redo log buffer内存空间一半时
    - InnoDB的后台线程每隔一秒刷盘
    - 每次事务提交时将缓存在redo log buffer里的redo log刷盘，这个策略可以通过`innodb_flush_log_at_trx_commit`控制：
      - 0：每次事务提交时，还是将redo log留在redo log buffer中
      - 1（默认值）：每次事务提交时，将redo log直接刷盘
      - 2：每次事务提交时，将redo log buffer中的redo log写入redo log文件，也就是进入了操作系统文件系统中的page cache文件缓存，并不是写入磁盘
- redo log文件满了怎么办？
  - 存储上redo log是定长环形空间（老版本用多个`ib_logfile`，8.0.30+常用`innodb_redo_log_capacity`），靠checkpoint检查之前对应的脏页是否已进数据文件，进了那段redo才能覆盖。
  - 所谓满了就是写指针快追上checkpoint，可覆盖的空间不够，InnoDB会强制刷新脏页推进checkpoint，严重时会阻塞写入

解决的问题：

- InnoDB改数据先改Buffer pool里的页（内存），脏页稍后才刷到.ibd。如果中间宕机，数据会丢失。
- 采用WAL，让MySQL的写操作从磁盘的随机写变成了顺序写。

redo log和undo log的区别：

- redo log记录此次事务修改后的数据状态，记录的是更新后的值，用于崩溃恢复，保证事物的持久性
- undo log记录此次事务修改前的数据状态，记录的是更新前的值，主要用于事务回滚和MVCC版本链，保证事务的原子性

总结：redo log 是InnoDB的重做日志，采用WAL：先写日志，再异步刷盘。作用是保证事务持久性，并让提交不必同步把所有数据页落盘。宕机后用redo把已经提交的改动重放到数据文件。

