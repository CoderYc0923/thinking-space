# 后端开发环境安装教程：Python + venv + pip & JDK + Maven

> **生成日期：2026-07-15**
> **适用系统：Windows / Linux（含宝塔面板）**

---

## 一、版本选择建议

### Python 推荐：Python 3.12.x

| 版本 | 状态 | 建议 |
|------|------|------|
| 3.13 | 较新，部分 AI/数据科学库兼容性滞后 | 尝鲜可用，生产暂缓 |
| **3.12** | 主力稳定版，生态完美支持 | ✅ **首选** |
| 3.11 | 仍广泛使用，但已不是最新 LTS 思路的焦点 | 可接受 |
| 3.10 | 即将进入安全维护末期 | 新项目不推荐 |

**结论：选 Python 3.12，兼容性与性能的最佳平衡点。**

### JDK 推荐：JDK 21（LTS）

| 版本 | LTS | 支持截止 | 建议 |
|------|-----|----------|------|
| **JDK 21** | ✅ | 2031年 | ✅ **首选**，虚拟线程等重磅特性 |
| JDK 17 | ✅ | 2029年 | 保守环境可用 |
| JDK 25 | ❌ 非 LTS | 6个月后停止 | 不要用于学习/生产 |

**结论：选 JDK 21，当前最新 LTS 版本，Spring Boot 3.x 官方推荐。**

### Maven 推荐：Maven 3.9.x

用最新稳定版即可，3.9.x 系列对 JDK 21 支持完善。

---

## 二、Python + venv + pip 安装教程

### 2.1 Windows 安装

#### 步骤 1：下载安装 Python

1. 打开 https://www.python.org/downloads/
2. 点击黄色的 **"Download Python 3.12.x"** 按钮
3. 运行下载的安装程序
4. ⚠️ **务必勾选底部的 "Add Python to PATH"**
5. 点击 "Install Now"

#### 步骤 2：验证安装

打开 PowerShell 或 CMD：

```powershell
python --version
# 应输出: Python 3.12.x

pip --version
# 应输出: pip 24.x (python 3.12)
```

#### 步骤 3：创建 venv 虚拟环境

每个项目都应该有自己的虚拟环境，避免依赖冲突：

```powershell
# 进入你的项目目录
cd D:\projects\my-backend

# 创建虚拟环境（名称习惯叫 venv 或 .venv）
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 此时命令行前面会出现 (venv) 标识
```

#### 步骤 4：在 venv 中使用 pip

```powershell
# 确保虚拟环境已激活（前面有 (venv) 标识）
(venv) pip install flask          # 安装包示例
(venv) pip list                   # 查看已安装的包
(venv) pip freeze > requirements.txt  # 导出依赖清单

# 退出虚拟环境
(venv) deactivate
```

### 2.2 Linux（宝塔面板环境）安装

```bash
# 1. 检查当前 Python 版本
python3 --version

# 2. 如果版本低于 3.12，安装 Python 3.12
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# CentOS/RHEL（宝塔面板常见）
sudo yum install python3.12

# 3. 确保 pip 已安装
python3.12 -m ensurepip --upgrade

# 4. 创建并激活虚拟环境
cd /www/wwwroot/my-backend
python3.12 -m venv venv
source venv/bin/activate

# 5. 后续使用同上
(venv) pip install flask
(venv) deactivate
```

### 2.3 pip 换国内镜像源（强烈推荐）

国内网络环境下，换源能显著提速：

```bash
# 临时使用（单次生效）
pip install flask -i https://pypi.tuna.tsinghua.edu.cn/simple

# 永久配置（推荐）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

常用国内镜像：

| 镜像源 | 地址 |
|--------|------|
| 清华 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple/` |

---

## 三、JDK + Maven 安装教程

### 3.1 Windows 安装 JDK 21

#### 步骤 1：下载 JDK 21

1. 打开 https://adoptium.net/download/ （推荐 Eclipse Adoptium 发行版，开源无限制）
2. 选择 **JDK 21 (LTS)**，操作系统选 Windows，下载 `.msi` 安装包

> 备选：Oracle JDK 从 JDK 17 起免费用于生产，也可从 oracle.com 下载。

#### 步骤 2：安装

1. 运行 `.msi` 安装程序，一路 Next
2. 安装程序会自动配置 `JAVA_HOME` 环境变量和 PATH

#### 步骤 3：验证安装

打开新的 PowerShell 或 CMD：

```powershell
java --version
# 应输出: openjdk 21.0.x 2024-xx-xx LTS

javac --version
# 应输出: javac 21.0.x
```

如果提示找不到命令，手动配置环境变量：

1. 搜索"编辑系统环境变量"→"环境变量"
2. 新建**系统变量**：`JAVA_HOME` = `C:\Program Files\Eclipse Adoptium\jdk-21.0.x.xx-hotspot\`
3. 编辑 `Path`，新增一条：`%JAVA_HOME%\bin`
4. 重启终端验证

### 3.2 Linux 安装 JDK 21

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install openjdk-21-jdk

# CentOS/RHEL（宝塔面板常见）
sudo yum install java-21-openjdk-devel

# 验证
java --version
javac --version
```

### 3.3 Windows 安装 Maven

#### 步骤 1：下载

1. 打开 https://maven.apache.org/download.cgi
2. 下载 **Binary zip archive**（例如 `apache-maven-3.9.9-bin.zip`）

#### 步骤 2：安装

Maven 是免安装的，解压即用：

1. 解压到 `C:\tools\apache-maven-3.9.9`（路径随意，别带空格和中文）
2. 添加环境变量：
   - 新建 `MAVEN_HOME` = `C:\tools\apache-maven-3.9.9`
   - 编辑 `Path`，新增 `%MAVEN_HOME%\bin`
3. 重启终端

#### 步骤 3：验证

```powershell
mvn --version
# 应输出 Maven 版本和使用的 JDK 路径
```

### 3.4 Maven 换国内镜像源

编辑 `C:\tools\apache-maven-3.9.9\conf\settings.xml`（或 Linux 上的对应路径），在 `<mirrors>` 标签内添加：

```xml
<mirror>
    <id>aliyun</id>
    <mirrorOf>central</mirrorOf>
    <name>Aliyun Maven Mirror</name>
    <url>https://maven.aliyun.com/repository/public</url>
</mirror>
```

### 3.5 创建第一个 Maven 项目验证

```powershell
# 快速生成一个项目骨架
mvn archetype:generate ^
  -DgroupId=com.example ^
  -DartifactId=hello-world ^
  -DarchetypeArtifactId=maven-archetype-quickstart ^
  -DinteractiveMode=false

cd hello-world
mvn compile    # 编译
mvn package    # 打包
```

如果一切正常，`target/` 目录下会生成 `.class` 文件和 `.jar` 包。

> **Linux / macOS 注意**：换行符用 `\` 而非 `^`。

---

## 四、总结速查

| 工具 | 推荐版本 | 验证命令 | 下载地址 |
|------|----------|----------|----------|
| Python | **3.12.x** | `python --version` | https://www.python.org/downloads/ |
| pip | 随 Python 自带 | `pip --version` | — |
| venv | Python 内置模块 | `python -m venv venv` | — |
| JDK | **21 (LTS)** | `java --version` | https://adoptium.net/download/ |
| Maven | **3.9.x** | `mvn --version` | https://maven.apache.org/download.cgi |

### 国内镜像速查

| 工具 | 镜像地址 |
|------|----------|
| pip (清华) | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| pip (阿里云) | `https://mirrors.aliyun.com/pypi/simple/` |
| Maven (阿里云) | `https://maven.aliyun.com/repository/public` |

---

## 五、常见问题排查

### Python

| 问题 | 解决方案 |
|------|----------|
| `python` 命令找不到 | 安装时未勾选 "Add Python to PATH"，重新安装或手动添加 Path |
| `pip` 下载速度慢 | 配置国内镜像源（见 2.3 节） |
| venv 激活失败 (Windows) | PowerShell 执行策略问题，运行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

### JDK / Maven

| 问题 | 解决方案 |
|------|----------|
| `java` 命令找不到 | 检查 `JAVA_HOME` 和 `Path` 是否正确配置，重启终端 |
| `mvn` 命令找不到 | 检查 `MAVEN_HOME` 和 `Path` 配置 |
| Maven 下载依赖慢 | 配置阿里云镜像（见 3.4 节） |
| 多个 JDK 版本冲突 | 检查 `Path` 中哪个 JDK 排在前面，或使用 `JAVA_HOME` 明确指定 |

---

两个语言的环境都装好后，你的后端学习基础设施就齐了。如果在安装过程中遇到任何报错，可以直接把错误信息贴出来排查。
