- Integer内部有静态缓存，默认-128~127

- Integer.valueOf（自动装箱也走它）：落在范围内就复用缓存对象；超出范围新建对象

- 所以：

  - ```java
    Integer a = 100,b = 100; //true 同一缓存对象
    Integer c = 200, d = 200; //fasle 两个新对象，==比较引用，值比较用equals
    ```

  - 

