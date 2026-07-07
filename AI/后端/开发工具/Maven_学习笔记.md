# Maven 学习笔记

> 一份面向 AI 全栈开发者的 Maven 知识体系梳理，涵盖核心概念、生命周期、依赖管理、项目结构、仓库机制、常用命令及与 Node.js 的对照。

---

## 目录

1. [什么是 Maven](#1-什么是-maven)
2. [Maven vs Gradle](#2-maven-vs-gradle)
3. [核心概念](#3-核心概念)
4. [构建生命周期](#4-构建生命周期)
5. [项目结构与约定优于配置](#5-项目结构与约定优于配置)
6. [仓库体系](#6-仓库体系)
7. [插件机制](#7-插件机制)
8. [常用命令汇总](#8-常用命令汇总)
9. [与 Node.js (npm) 对照表](#9-与-nodejs-npm-对照表)

---

## 1. 什么是 Maven

Maven 是 Apache 旗下的开源项目，是 Java 生态中最主流的**项目构建和依赖管理工具**。

### 一句话理解

**Maven 之于 Java ≈ npm 之于 Node.js** —— 帮你管理依赖包（jar），并自动化项目的编译、测试、打包、部署全过程。

### 它解决什么问题？

| 问题 | Maven 的解决方案 |
|------|------------------|
| jar 包手动下载、版本冲突 | 统一依赖管理，自动解析传递依赖 |
| 项目结构不统一，换项目就要重新熟悉 | "约定优于配置"，强制标准目录结构 |
| 编译、测试、打包步骤繁琐 | 标准化构建生命周期，一条命令搞定 |
| 多模块项目管理复杂 | 父子 POM 继承，模块聚合 |

---

## 2. Maven vs Gradle

| 维度 | Maven | Gradle |
|------|-------|--------|
| 配置文件 | `pom.xml` (XML) | `build.gradle` (Groovy/Kotlin DSL) |
| 构建速度 | 一般（无增量编译） | 快（增量编译 + 构建缓存） |
| 灵活性 | 低，遵循固定生命周期 | 高，脚本化定制 |
| 学习曲线 | 平缓 | 较陡 |
| 生态成熟度 | 极成熟，插件丰富 | 成熟，Android 官方 |
| 适用场景 | 传统企业项目、Spring Boot | Android 开发、大型微服务 |

> 对于学习和中小型项目，**Maven 是更稳妥的选择**，大部分 Spring Boot 官方文档和教程默认使用 Maven。

---

## 3. 核心概念

### 3.1 POM (Project Object Model)

`pom.xml` 是 Maven 项目的核心配置文件，类似 Node.js 的 `package.json`。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    
    <modelVersion>4.0.0</modelVersion>

    <!-- GAV 坐标：唯一标识一个项目 -->
    <groupId>com.example</groupId>       <!-- 组织/公司域名倒写 -->
    <artifactId>my-app</artifactId>       <!-- 项目名 -->
    <version>1.0.0</version>              <!-- 版本号 -->
    <packaging>jar</packaging>            <!-- 打包方式：jar / war / pom -->

    <!-- 依赖列表 -->
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>3.2.0</version>
        </dependency>
    </dependencies>
</project>
```

### 3.2 GAV 坐标

每个依赖/项目由三个要素唯一确定：

| 元素 | 含义 | 类比 npm |
|------|------|----------|
| **GroupId** | 组织/公司标识 | `@scope/package-name` 中的 scope |
| **ArtifactId** | 项目/模块名 | package name |
| **Version** | 版本号 | version 字段 |

### 3.3 依赖管理

#### 依赖声明

```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
    <scope>runtime</scope>  <!-- 作用域 -->
</dependency>
```

#### 依赖作用域 (scope)

| Scope | 说明 | 示例 |
|-------|------|------|
| `compile` (默认) | 编译、运行、测试都可用 | Spring Boot Starter |
| `provided` | 编译和测试可用，运行时由容器提供 | Servlet API |
| `runtime` | 运行时和测试可用，编译不需要 | JDBC 驱动 |
| `test` | 仅测试可用 | JUnit |

#### 传递依赖

Maven 自动解析依赖的依赖（传递依赖），遵循以下规则：

- **最短路径优先**：A→B→C(1.0) 和 A→C(2.0)，选 C(2.0)
- **先声明优先**：路径长度相同时，选 `pom.xml` 中先声明的

#### 排除传递依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```

#### 统一版本管理

```xml
<properties>
    <java.version>17</java.version>
    <spring-boot.version>3.2.0</spring-boot.version>
</properties>
```

---

## 4. 构建生命周期

Maven 有三大生命周期，最核心的是 **Default 生命周期**。

### 4.1 三大生命周期

| 生命周期 | 作用 |
|----------|------|
| **clean** | 清理项目（删除 target 目录） |
| **default** | 构建项目（编译→测试→打包→部署） |
| **site** | 生成项目站点文档 |

### 4.2 Default 生命周期核心阶段

```
validate  →  验证项目结构
compile   →  编译源码 (.java → .class)
test      →  运行单元测试
package   →  打包 (jar / war)
verify    →  集成测试验证
install   →  安装到本地仓库 (~/.m2/repository)
deploy    →  部署到远程仓库
```

**阶段有顺序依赖** —— 执行 `mvn install` 会自动先执行 compile、test、package 等前置阶段。

### 4.3 常用构建命令

```bash
# 清理 + 编译
mvn clean compile

# 清理 + 打包（跳过测试）
mvn clean package -DskipTests

# 清理 + 安装到本地仓库
mvn clean install

# 只跑测试
mvn test

# 部署到远程仓库
mvn clean deploy
```

### 4.4 Spring Boot 项目打包

```bash
mvn clean package -DskipTests
# 输出：target/my-app-1.0.0.jar（可执行 jar）

# 运行
java -jar target/my-app-1.0.0.jar
```

关键插件：
```xml
<build>
    <plugins>
        <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
        </plugin>
    </plugins>
</build>
```

---

## 5. 项目结构与约定优于配置

### 5.1 标准目录结构

```
my-app/
├── pom.xml                          ← 核心配置
├── src/
│   ├── main/
│   │   ├── java/                    ← Java 源码
│   │   │   └── com/example/
│   │   │       ├── controller/      ← 控制器
│   │   │       ├── service/         ← 业务逻辑
│   │   │       ├── repository/      ← 数据访问 (DAO)
│   │   │       ├── model/           ← 实体类
│   │   │       └── Application.java ← 启动类
│   │   └── resources/
│   │       ├── application.yml      ← 配置文件
│   │       ├── static/              ← 静态资源
│   │       └── templates/           ← 模板文件
│   └── test/
│       └── java/                    ← 测试代码
└── target/                          ← 构建产物（自动生成，勿提交 Git）
```

### 5.2 Git 忽略清单 (.gitignore)

```gitignore
# Maven
target/
*.jar
*.war

# IDE
.idea/
*.iml
.vscode/

# OS
.DS_Store
Thumbs.db
```

---

## 6. 仓库体系

### 6.1 仓库类型

```
中央仓库 (Maven Central)
    ↓ 默认查找
远程仓库 (私服 Nexus/Artifactory)
    ↓ 找不到则下载到
本地仓库 (~/.m2/repository)
```

### 6.2 查找顺序

1. **本地仓库** → 有则直接用
2. **远程仓库**（私服）→ 有则下载到本地
3. **中央仓库**（Maven Central）→ 下载到本地

### 6.3 配置镜像（加速下载）

`~/.m2/settings.xml`：

```xml
<settings>
    <mirrors>
        <mirror>
            <id>aliyun</id>
            <name>阿里云 Maven 镜像</name>
            <url>https://maven.aliyun.com/repository/public</url>
            <mirrorOf>central</mirrorOf>
        </mirror>
    </mirrors>
</settings>
```

---

## 7. 插件机制

Maven 本身只是一个框架，具体工作由**插件**完成。

### 7.1 常用插件

| 插件 | 作用 |
|------|------|
| `maven-compiler-plugin` | 编译 Java 源码 |
| `maven-surefire-plugin` | 运行单元测试 |
| `maven-jar-plugin` | 打包普通 jar |
| `spring-boot-maven-plugin` | 打包可执行 Spring Boot jar |
| `maven-resources-plugin` | 处理资源文件 |

### 7.2 插件配置示例

```xml
<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.11.0</version>
            <configuration>
                <source>17</source>   <!-- Java 版本 -->
                <target>17</target>
            </configuration>
        </plugin>
    </plugins>
</build>
```

---

## 8. 常用命令汇总

```bash
# 项目创建
mvn archetype:generate -DgroupId=com.example -DartifactId=my-app

# 编译
mvn compile

# 运行测试
mvn test

# 运行单个测试类
mvn test -Dtest=UserServiceTest

# 打包
mvn package

# 打包跳过测试
mvn package -DskipTests

# 安装到本地仓库
mvn install

# 清理
mvn clean

# 强制更新快照依赖
mvn clean install -U

# 查看依赖树
mvn dependency:tree

# 分析依赖冲突
mvn dependency:analyze

# 运行 Spring Boot 项目（开发模式）
mvn spring-boot:run

# 多模块构建（-pl 指定模块，-am 同时构建依赖模块）
mvn clean install -pl module-a -am
```

---

## 9. 与 Node.js (npm) 对照表

| 概念 | Maven (Java) | npm (Node.js) |
|------|-------------|---------------|
| 配置文件 | `pom.xml` | `package.json` |
| 依赖仓库 | `~/.m2/repository/` | `node_modules/` |
| 仓库同步文件 | - | `package-lock.json` |
| 安装依赖 | `mvn install` | `npm install` |
| 添加依赖 | 手动编辑 `pom.xml` | `npm install <pkg>` |
| 编译 | `mvn compile` | `tsc` (TypeScript) |
| 测试 | `mvn test` | `npm test` |
| 打包 | `mvn package` | `npm run build` |
| 运行 | `java -jar xxx.jar` | `node dist/index.js` |
| 中央仓库 | Maven Central | npm registry |
| 多模块/工作区 | 父子 POM / modules | npm workspaces |
| 版本锁定 | `<properties>` + parent POM | `package-lock.json` |

> 💡 **记忆技巧**：`mvn clean install` ≈ `rm -rf node_modules && npm install && npm run build`，把清理、装依赖、构建三步合一。

---

## 附录：结合 Docker 的典型工作流

结合你已掌握的 Docker 工作流，Spring Boot + Maven 的典型流程：

```dockerfile
# 阶段一：Maven 构建
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline   # 预下载依赖（层缓存）
COPY src ./src
RUN mvn clean package -DskipTests

# 阶段二：运行
FROM eclipse-temurin:17-jre-alpine
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

```yaml
# docker-compose.yml 中使用
services:
  backend-java:
    build: ./backend-java
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
    depends_on:
      - mysql
```

---

> 📅 生成日期：2026-07-07
> 🏷️ 标签：Maven, Java, 构建工具, 依赖管理, Spring Boot
