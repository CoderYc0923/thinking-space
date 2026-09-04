MVCC ：通过版本链来控制并发事务访问同一个记录的行为（多版本并发控制）

原理：通过事务的Read View中的字段和行记录中的两个隐藏字段（trx_id和roll_pointer）做对比，来控制并发事务访问你同一个记录时的行为。



三大组件：

- undo log：数据修改前的旧版本数据存放处
- Read View：判断数据版本对当前事务是否可见
- roll_pointer：每条记录指向旧版本的链表指针



具体：

- Read View有四个重要字段：
  - m_ids：当前数据库活跃事务（启动了但未提交）的事务ID列表
  - min_trx_id：创建Read View时，当前数据库中活跃事务中事务ID最小的事务，m_ids的最小值
  - max_trx_id：创建Read View时，下一个将要分配给新事务的事务ID值
  - creator_trx_id：创建该Read View的事务的事务ID
- 行记录中的两个隐藏字段
  - trx_id：当一个事务对某条聚簇索引记录进行改动时，就会把该事务的事务ID记录在这
  - roll_pointer：每次对某条聚簇索引记录进行改动时，都会把旧版本记录写进undo log中，然后这里放指向旧版本记录的指针



如何运行：

- 当一个事务去访问记录的时候：
  - 自己更新的数据总是可见，因为trx_id == creator_trx_id
  - 若记录的trx_id小于Read View中的min_trx_id，代表这个版本的记录由创建Read View之前就提交的事务产生，所以当前事务可见
  - 若记录的trx_id大于Read View中的max_trx_id，代表这个版本的记录由创建Read View之后才启动的事务产生，所以当前事务不可见，不可见就会沿着undo log链找旧版本数据（快照）
  - 若记录的trx_id在Read View中的min_trx_id和max_trx_id之间，代表该事务的ID在Read View 创建之前就已经分配出去了，需要再判断记录的trx_id是否在 `m_ids` 列表中:
    - 如果 trx_id **在** `m_ids` 列表中，代表生成改版本记录的事务在创建 Read View 时仍然活跃（未提交），所以当前事务不可见就会沿着undo log链找旧版本数据（快照）
    - 如果 trx_id **不在** `m_ids` 列表中，代表生成改版本记录的事务在创建 Read View 时已经提交，所以当前事务可见