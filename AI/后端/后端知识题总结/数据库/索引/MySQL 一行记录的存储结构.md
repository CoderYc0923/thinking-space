**MySQL中支持多种存储引擎，不同存储引擎保存得的文件不同**

**InnoDB**

- **MySQL数据库的文件存放目录**

  - 每创建一个database，都会在/var/lib/mysql目录中创建一个以database为名的目录。然后保存的表结构和表数据都会存放在这个目录里。

  - ![](https://cdn.xiaolincoding.com/gh/xiaolincoder/mysql/row_format/database.png)

  - 一个database目录下存放三个文件

    - ```bash
      [root@xxx ~]#ls /var/lib/mysql/my_test
      db.opt
      t_order.frm
      t.order.ibd
      ```

    - db.opt

      - 用来存储当前数据库的默认字符集和字符校验规则

    - t_order.frm

      - 存放一张表的**表结构**（元数据信息，表结构定义等）

    - t_order.ibd

      - 存放一张表的**表数据**
      - 表数据可以存在共享表空间文件（文件名：ibdata1）里，也可以存放在独占表空间文件（文件名：表名.ibd）。
        - 这个行为是通过innodb_file_pre_table控制的。若设置为1，则存放在独占表空间
          - MySQL5.6.6开始，这个字段的默认值就是1了。所以这个版本之后，表数据就默认存放在一个单独的.ibd文件中。

    - 一个表空间文件（.ibd文件）的结构

      - ![](https://cdn.xiaolincoding.com/gh/xiaolincoder/mysql/row_format/%E8%A1%A8%E7%A9%BA%E9%97%B4%E7%BB%93%E6%9E%84.drawio.png)
      - 表空间由段（segment）、区（extent）、页（page）、行（row）组成
        - 行（row）
          - 表中的记录都是按行进行存放的。
          - 每行记录根据不同的行格式，有不同的存储结构
        - 页（page）
          - 页中存放行数据
          - InnoDB的数据是通过**页**为单位来读写的，默认每一页大小16KB，也就是最多能保证16KB的连续存储空间。
          - 页的类型有很多，常见的有**数据页、undo日志页、溢出页**等。
          - [数据表中的行记录是用数据页来管理的](./InnoDB的B+树.md)
        - 区（extent）
          - B+树的每一层是通过双向链表连接起来的。
          - 如果以页为单位分配存储空间，那么链表中相邻的两个页之间的物理位置可能并不是连续的。这样的话，磁盘查询的时候就会有大量的随机IO，随机IO是很慢的。
          - 所以为了解决这个问题，当表中数据量大的时候，为某个索引分配空间的时候就不再按照页为单位分配了，而是按照区为单位。
            - 每个区的大小是1MB，对于16KB的页来说，连续64个页会被划分为一个区，这样就让链表中相邻的页物理位置也相邻，这样就可以使用顺序IO了
        - 段（segment）
          - 表空间由各个段组成，段由多个区组成。
            - 段分为：数据段、索引段、回滚段
              - 索引段：存放B+树的非叶子节点的区的集合
              - 数据段：存放B+树叶子节点的区的结合
              - 回滚段：存放回滚数据区的集合

- **InnoDB的行格式有哪些**

  - 行格式就是存储一条记录的存储格式

  - InnoDB提供4种行格式，分别是Redundant、Compact、Dynamic、Compressed

    - Redundant ：MySQL5.0版本之前用的行格式，现在基本没人用了
    - Compact ：一种紧凑的行格式，设计的初衷就i是为了让一个数据页可以存放更多的行记录，从MySQL5.1之后，行格式默认设置成Compact
    - Dynamic和Compressed：都是紧凑的行格式，都是基于Compact进行了改进。从MySQL5.7之后，默认使用Dynamic

  - Compact行格式

    - ![](https://cdn.xiaolincoding.com/gh/xiaolincoder/mysql/row_format/COMPACT.drawio.png)

    - 例：一张表，字符集是ascii（每个字符占1字节），行格式是Compact

      - ```sql
        CREATE TABLE 't_user' (
        	id int(11) NOT NULL,
            name VARCHAR(20) DEFAULT NULL,
            phone VARCHAR(20) DEFAULT NULL,
        ) ENGINE = InnoDB DEFAULT CHARACTER SET = ascii ROW_FORMAT = COMPACT;
        ```

      - ![](https://cdn.xiaolincoding.com/gh/xiaolincoder/mysql/row_format/t_test.png)

        

    - 一条记录分为"**记录的额外信息**"和“**记录的真实数据**”两部分

    - 记录的额外信息：

      - **变长字段长度列表（变长字段允许存储的最大字节小于等于255字节，就用1字节表示；大于255字节，就用2字节表示）**

        - 变长字段（varchar、TEXT、BLOB 等）实际长度不固定，要把占用大小记下来，读的时候才知道读多长
        - **变长字段长度列表**只出现在数据表中**有变长字段**的时候
        - 变长字段的真实数据占用字节数会**逆序**存放在变长字段长度列表中
          - 为什么逆序？
            - 因为“记录头部信息”中指向下一个记录的指针，指向的是下一条记录的“记录头部信息”和“真实数据”之间的位置，逆序的话，就让**真实数据和数据对应的字段长度信息**可以在**一个CPU Cache Line 中**，这样可以**提高CPU Cache的命中率**
            - **NULL值列表同理逆序**。
        - 例：
          - 第一条记录：name字段1字节，十六进制0x01，phone字段3字节0x03
          - ![](https://cdn.xiaolincoding.com/gh/xiaolincoder/mysql/row_format/%E5%8F%98%E9%95%BF%E5%AD%97%E6%AE%B5%E9%95%BF%E5%BA%A6%E5%88%97%E8%A1%A81.png)

      - NULL值列表（**至少1字节**）

        - 存放表中NULL值的列，若存在允许NULL值的列，则每个列对应**一个二进制位（bit）**，**逆序**

          - 二进制位的值为**1代表该列的值为NULL**；反之则不会NULL
          - 二进制值列表必须用**整数个字节的位**表示（1字节8位），所以**NULL值列表至少1字节空间**
            - 若使用的二进制位个数不足整数个字节，就高位补0
            - 若超过，则整数个加（比如一张表9个NULL）那就是创建2字节空间的NULL值列表，以此类推

        - 只出现在**表中允许NULL值**的时候

        - 例：

          - 第二条记录
          - ![](https://cdn.xiaolincoding.com/gh/xiaolincoder/mysql/row_format/null%E5%80%BC%E5%88%97%E8%A1%A83.png)

          

      - 记录头部信息（**5字节**）

        - 记录头部信息中包含很多内容，列举比较重要的
        - delete_mask：标识这条数据是否被删除，（执行delete删除记录时，并不会马上真正删除记录，只是先将这条记录的delete_mask标记为1）
        - next_record：下一条记录的位置（页内单向链表）
        - record_type：当前记录的类型
          - 0：普通记录
          - 1：B+ 树非叶子节点记录（目录项）
          - 2：最小记录
          - 3：最大记录
    
    - 记录的真实数据：
    
      - ![](https://cdn.xiaolincoding.com/gh/xiaolincoder/mysql/row_format/%E8%AE%B0%E5%BD%95%E7%9A%84%E7%9C%9F%E5%AE%9E%E6%95%B0%E6%8D%AE.png)
      - **row_id（6字节）**
        - 建表时指定了主键或唯一约束列 → 没有 `row_id`
        - 都没指定 → InnoDB 自动加隐藏 `row_id`
      - **trx_id（6字节）**
        - 事务ID，表示这条数据是由哪个事务生成的。
      - **roll_pointer（7字节）**
        - 指向上一个版本（和 undo / MVCC 相关）
      - 各列真实数据（按列定义依次存放；NULL 列跳过）
  
  
  
  ​	
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  