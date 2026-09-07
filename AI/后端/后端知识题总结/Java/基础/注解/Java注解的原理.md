**总结：**

- 注解就是一种标签，用来提供信息。将注解贴到类/方法/字段上并写参数；编译后RUNTIME注解会留在类/方法/字段的.class的属性表中。运行时，反射把属性表中的注解信息读出来然后通过`AnnotationvoParser`解析进`memberValues`这个Map中，并生成一个动态代理对象；这样就可以为后续框架比如Spring、AOP提供信息去做注入、拦截、增强。



**流程总结：**[案例](./注解案例.md)

- 自定义一个注解（本质是继承了`Annotation`的接口）。
- 将注解绑定到某个类/方法/字段上，并填充注解的参数，比如（value="xxx"）
- 编译成`.class`文件时，若是`RUNTIME`策略。将注解信息写进对应类/方法/字段的`.class`文件的属性表。类加载后 JVM 可读
- 运行时，反射拿到属性表里注解原始数据，通过`AnnotationParser`解析成Map（注解属性），再生成注解的动态代理包装
- 调用`注解.value()`时，等于调用动态代理的`invoke`， `invoke`从handler中的Map取对应值
- 然后框架再消费这些元数据，比如Spring 根据读到的信息去做注入、AOP拦截、增强。







**注解本质：**

- `@interface`编译后是一个继承`Annotation`的特殊接口（**声明式接口**）

  - ```java
    public @interface MyAnnotatiion {
        String value();
    }
    ```

- 反射拿到的注解对象，是运行时生成的**动态代理**

- 调用`annotation.value()` -> 进代理 -> 调用`AnnotationInvocationHandler.invoke` -> 从`memberValues`这个Map取属性值（数据来自`.class`里解析出来的注解信息 / 常量池相关数据）



**注解类型：**`@Retention(RetentionPolicy.xxx)`

- `SOURCE`：只在源码，编译后没了
- `CLASS`（默认）在`.class`里，运行时不可见，反射拿不到
- `RUNTIME` 在`.class`里，运行时可见，反射可以解析



**注解存在哪：**

- 编译器把`RUNTIME`注解写进`.class`属性表，例如：
  - `RuntimeVisibleAnnotations`：存储运行时可见的注解信息
  - `RuntimeInvisibleAnnotations`：存储运行时不可见的注解信息
  - `RuntimeVisibleParameterAnnotations`/ `RuntimeInvisibleParameterAnnotations`：存储方法参数上的注解信息
- 可以用`javap -v`看到



**注解解析流程：**

- `.class`属性表存储注解原始信息
- 类加载时，JVM从常量池/属性表读取相关数据（底层有`native`读字节码）
- 调用`clazz.getAnnotation(...)`等反射API
- `AnnotationElement`体系（`Class` `Method` `Field`等）
- 延迟解析：`AnnotationParser.parseAnnotations(...)`把原始字节码解析成Map<注解类型，Annotation>
- 用动态代理包装成`Annotation`对象返回
- 调用注解方法时，`AnnotationInvocationHandler`从Map取值





