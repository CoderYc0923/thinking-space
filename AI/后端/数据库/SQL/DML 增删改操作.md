## 前置准备

```sql
-- 创建学生表 student
CREATE TABLE student (
	id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学生主键id'，
    name VARCHAR(20) NOT NULL COMMENT '学生姓名',
    age INT COMMENT '年龄',
    gender VARCHAR(2) COMMENT '性别：男/女',
    class_id INT COMMENT '班级编号',
    score DECIMAL(5,1) COMMENT '考试总分',
    create_time DATETIME DEFAULT NOW() COMMENT '创建时间'
);

-- 插入测试数据
INSERT INTO student(name, age, gender,class_id,score)
VALUES
('张三',18,'男',1,92.5),
('李四',17,'男',1,86.0),
('小美',18,'女',1,96.0),
('王小花',17,'女',2,78.5),
('赵强',19,'男',2,59.0),
('刘雪',18,'女',2,88.0),
('周小天',17,'男',3,45.0),
('吴雨',18,'女',3,91.0),
('郑浩',19,'男',3,76.0),
('孙倩',17,'女',3,66.0),
('马明',18,'男',1,null); -- 分数为空
```

```sql
-- 成绩表：每个学生多门科目成绩
CREATE TABLE score (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    student_id INT COMMENT '学生id，关联student表',
    subject VARCHAR(20) COMMENT '科目：语文/数学/英语',
    score DECIMAL(5,1) COMMENT '单科分数'
);

-- 插入测试数据
INSERT INTO score(student_id,subject,score)
VALUES
(1,'语文',90), (1,'数学',95), (1,'英语',92.5),
(2,'语文',88), (2,'数学',82), (2,'英语',86),
(3,'语文',97), (3,'数学',94), (3,'英语',96),
(4,'语文',75), (4,'数学',80), (4,'英语',78.5),
(5,'语文',60), (5,'数学',55), (5,'英语',59),
(6,'语文',85), (6,'数学',92), (6,'英语',88),
(7,'语文',40), (7,'数学',48), (7,'英语',45),
(8,'语文',93), (8,'数学',89), (8,'英语',91),
(9,'语文',72), (9,'数学',78), (9,'英语',76),
(10,'语文',65), (10,'数学',68), (10,'英语',66),
(11,'语文',null), (11,'数学',50), (11,'英语',null);
```

```sql
-- 班级表
CREATE TABLE class (
    class_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '班级编号',
    class_name VARCHAR(20) NOT NULL COMMENT '班级名称',
    teacher VARCHAR(10) COMMENT '班主任'
);

INSERT INTO class(class_name,teacher)
VALUES
('高一1班','王老师'),
('高一2班','李老师'),
('高一3班','张老师');
```



## 说明

1. DML 全称 Data Manipulation Language 数据操作语言
2. 包含三大核心指令：`INSERT` 新增、`UPDATE` 修改、`DELETE` 删除
3. 重中之重安全规范：生产环境**禁止不带 WHERE 条件**执行 UPDATE/DELETE，会清空整张表



## 一、INSERT 插入数据（新增）

1. INSERT 基础语法

   - 语法 1：给全部字段插入数据（必须按建表字段顺序传值）

     - ```sql
       INSERT INTO 表名 VALUES (值1,值2...);
       
       -- 向班级表新增一条班级数据
       INSERT INTO class VALUES (4,'高一4班','陈老师');
       ```

     - 

   - 语法 2：指定字段插入（推荐，工作标准写法）只给需要的字段传值，未填写字段会自动使用默认值、NULL、自增

     - ```sql
       INSERT INTO 表名(字段1,字段2) VALUES (值1,值2);
       
       -- 新增学生，只填写姓名、年龄、班级，其余字段留空
       INSERT INTO student(name, age, class_id) VALUES ('林峰',18,4);
       ```

2. 批量插入多条数据（高效写法）

   - 一次性插入多行，减少数据库 IO，导入数据必备

   - ```SQL
     INSERT INTO student(name,age,gender,class_id,score)
     VALUES
     ('小宇',17,'男',4,82),
     ('欣怡',18,'女',4,90),
     ('浩然',19,'男',4,75);
     ```

3. 查询结果插入表（INSERT ... SELECT）

   - 把一张表的查询结果，直接插入另一张表，用于数据复制、数据备份

   - ```SQL
     -- 复制1班所有学生到临时备份表（先自行创建student_back表）
     INSERT INTO student_back(name,age,gender,class_id,score)
     SELECT name,age,gender,class_id,score FROM student
     WHERE class_id = 1;
     ```

4. INSERT 补充规则

   - 字符串、日期类型的值必须用单引号 `'内容'` 包裹
   - 数值类型直接写数字，不需要引号
   - 主键自增字段 AUTO_INCREMENT，插入时可以直接写 NULL 或省略
   - 字段允许为 NULL 时，不填写会自动填充 NULL；有 DEFAULT 默认值则填充默认值

## 二、UPDATE 修改

1. 基础语法

   - ```SQL
     UPDATE 表名
     SET 字段1=新值1, 字段2=新值2
     [WHERE 过滤条件];
     ```

2. 示例

   - 修改林峰的分数为 88

   - ```sql
     UPDATE student
     SET score = 88
     WHERE name = '林峰';
     
     ```

   - 修改小宇年龄 18，性别女，分数 86

   - ```sql
     UPDATE student SET age=18,gender='女',score=86 WHERE name='小宇';
     ```

   - 所有人分数 + 5 分

   - ```sql
     UPDATE student SET score = score + 5;
     ```

3. UPDATE 致命风险（必记）

   - **省略 WHERE 条件 = 修改整张表全部数据**，生产重大事故

   - ```sql
     -- 错误！无WHERE，所有学生score全部变成0，无法恢复
     UPDATE student SET score = 0;
     ```

   - 安全操作流程：**先 SELECT 验证条件，确认数据无误再执行 UPDATE**

   - ```sql
     -- 第一步：查询确认要修改的数据
     SELECT * FROM student WHERE name = '林峰';
     -- 第二步：再执行更新
     UPDATE student SET score=88 WHERE name='林峰';
     ```



## 三、DELETE 删除

1. 基础语法

   - ```sql
     DELETE FROM 表名
     [WHERE 过滤条件];
     ```

2. 示例

   - 删除姓名为浩然的学生

   - ```sql
     DELETE FROM student
     WHERE name = '浩然';
     ```

   - 删除 4 班分数低于 60 分的学生

   - ```sql
     DELETE FROM student
     WHERE class_id = 4 AND score <= 60; 
     ```

3. DELETE 致命风险

   - 省略 WHERE 条件会**删除整张表所有记录**
   - 安全规范：删除前同样先用 SELECT 校验筛选结果

## 四、DELETE 和 TRUNCATE 彻底清空表 核心区别

| 对比项   | DELETE                  | TRUNCATE TABLE               |
| -------- | ----------------------- | ---------------------------- |
| 操作本质 | DML 语句，逐行删除数据  | DDL 语句，直接摧毁重建数据表 |
| 事务支持 | 可以被事务回滚 ROLLBACK | 无法回滚，执行立刻生效       |
| 自增主键 | 自增值不会重置          | 自增 AUTO_INCREMENT 重置为 1 |
| 触发器   | 删除行会触发表触发器    | 不会触发触发器               |
| 性能     | 数据量大时速度慢        | 速度极快，不记录单行日志     |

TRUNCATE 语法

```sql
-- 清空student表所有数据，谨慎使用
TRUNCATE TABLE student;
```



## 总结

1. INSERT 三种用法：单行插入、指定字段插入、批量插入、查询结果插入
2. UPDATE 修改数据，**必须携带 WHERE 条件**，修改前先用 SELECT 验证
3. DELETE 删除指定行，无 WHERE 清空整张表；支持事务回滚
4. TRUNCATE 快速清空全表，DDL 语句，不可回滚，重置自增主键
5. 生产环境标准操作规范：先查、后改 / 删，杜绝无条件 UPDATE、DELETE

