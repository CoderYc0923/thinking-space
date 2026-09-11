- `notify`：随机唤醒一个等待线程，`HotSpot`里常见实现更接近排队（先等待的先被考虑唤醒）
- `notifyAll`：唤醒全部等待线程
- 规范写法通常用`while`判断条件+`notifyAll`

