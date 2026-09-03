count性能从好到差：

- count(*) = count(1) > count(主键) >count(普通字段)



- InnoDB的count是用来扫索引，对非NULL计数。

- count(*)等价于 count(0)、 count(1)。
- count(*) 、count(1) 、 count(主键)都会优先扫更小的二级索引，无二级索引时 count(主键)还会多一步取字段判NULL，所以稍微慢一点。
- count(普通字段)最差，常常全表扫。



- InnoDB因为MVCC不能像MyISAM那样存rows_count，读表行数O（1），大表精确技术要靠单独计数表或近似值（用EXPLAIN或者SHOW TABLE STATUS进行估算），别高频用count(*)

