# Scoop 安装与 JDK 迁移教程（Windows）

> **适用机器**：已有 `D:\Java\jdks` 下的 Temurin 8 / 21，全局 `JAVA_HOME` 指向 8，Maven 在 `D:\Java\maven`  
> **目标**：用 Scoop 统一安装/切换 JDK，验通后删除旧目录  
> **重要**：Scoop **不能**把现有文件夹「登记」进去，迁移 = **用 Scoop 重装同发行版 → 改环境变量 → 确认无误再删旧 JDK**

---

## 〇、迁移前你现在的状态（对照用）

| 项 | 当前值 |
|----|--------|
| 系统 `JAVA_HOME`（Machine） | `D:\Java\jdks\jdk-8.0.504.1-hotspot` |
| PATH 里的 JDK | `...\jdk-8...\bin` 以及 `...\jdk-21...\bin` |
| Maven | `D:\Java\maven\apache-maven-3.9.16`（**保留，不用迁**） |
| Scoop | 尚未安装 |

旧目录（迁完、确认后再删）：

- `D:\Java\jdks\jdk-8.0.504.1-hotspot`
- `D:\Java\jdks\jdk-21.0.11_10`

---

## 一、装之前要知道的 3 件事

1. **装的是同一类 JDK**  
   Scoop 的 `temurin8-jdk` / `temurin21-jdk` 来自 Eclipse Temurin，和你现在用的是同一路线，只是安装位置变成 Scoop 目录。

2. **`scoop reset` 只管 PATH 里的 `java`，不管 `JAVA_HOME`**  
   Maven 主要看 `JAVA_HOME`。所以切换版本时要：**`scoop reset` + 改 `JAVA_HOME`**（后面有一键脚本）。

3. **建议把 Scoop 装到 D 盘**  
   你 Java 相关都在 `D:\Java`，下面按 `D:\Scoop` 来写，避免全堆到 C 盘用户目录。

---

## 二、安装 Scoop（装到 D:\Scoop）

### 2.1 打开 PowerShell（普通用户即可）

Win + X →「Windows PowerShell」或「终端」。

### 2.2 允许当前用户执行本地脚本

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

若提示确认，输入 `Y`。

### 2.3 指定 Scoop 根目录并安装

```powershell
$env:SCOOP = "D:\Scoop"
[Environment]::SetEnvironmentVariable("SCOOP", "D:\Scoop", "User")

# 官方安装脚本
irm get.scoop.sh | iex
```

装完后**新开一个** PowerShell，检查：

```powershell
scoop --version
echo $env:SCOOP
# 应类似：D:\Scoop
```

若提示找不到 `scoop`：关掉终端重开；或检查用户 PATH 是否包含 `D:\Scoop\shims`。

### 2.4（可选）换国内镜像加速

网络慢时再加，不慢可跳过：

```powershell
# 示例：使用镜像（地址可能变化，以你当时能用的为准）
scoop config SCOOP_REPO https://gitee.com/scoop-bucket/scoop
# 若镜像不可用，删掉配置即可：
# scoop config rm SCOOP_REPO
```

不熟悉镜像就先用官方源。

---

## 三、安装 Java 桶与各版本 JDK

### 3.1 添加 java bucket

```powershell
scoop bucket add java
```

### 3.2 查看可装版本（可选）

```powershell
scoop search temurin | Select-String "temurin(8|17|21)-jdk"
```

### 3.3 安装 8 和 21（对应你现有的两套）

```powershell
scoop install temurin8-jdk
scoop install temurin21-jdk
```

以后若要 17：

```powershell
scoop install temurin17-jdk
```

安装位置示例：

```
D:\Scoop\apps\temurin8-jdk\current
D:\Scoop\apps\temurin21-jdk\current
```

`current` 是指向具体版本号目录的链接，**以后把 JAVA_HOME 指到 `...\current` 即可**，升级更省事。

### 3.4 安装后立刻自检

```powershell
scoop list
scoop which java
java -version
javac -version
```

---

## 四、配置环境变量（从旧路径切到 Scoop）

> 改的是 **系统/用户环境变量**。改完后：**关掉所有终端和 Cursor，再重开**，否则还是旧 PATH。

### 4.1 建议策略

| 变量 | 建议 |
|------|------|
| `JAVA_HOME` | 指到「当前默认要用的」那套，例如日常默认 8：`D:\Scoop\apps\temurin8-jdk\current` |
| `Path` | **删掉**旧的 `D:\Java\jdks\...` 相关项；**保留** `D:\Scoop\shims`（安装 Scoop 时一般已加） |
| Maven | 继续 `D:\Java\maven\apache-maven-3.9.16\bin`，不动 |

Scoop 的 `shims` 提供 `java`/`javac` 命令；`JAVA_HOME` 给 Maven、部分 IDE、脚本用。

### 4.2 用图形界面改（不容易写错）

1. Win 搜索 → **编辑系统环境变量** → **环境变量**  
2. **系统变量**里找到 `JAVA_HOME`：  
   - 旧值：`D:\Java\jdks\jdk-8.0.504.1-hotspot`  
   - 新值：`D:\Scoop\apps\temurin8-jdk\current`  
3. **系统变量** / **用户变量**的 `Path` 里删除或改掉：  
   - `D:\Java\jdks\jdk-8.0.504.1-hotspot\bin`  
   - `D:\Java\jdks\jdk-21.0.11_10\bin`  
   - `D:\Java\jdks\jdk-21.0.11_10\`（若有）  
4. 确认存在：  
   - `D:\Scoop\shims`  
   - `D:\Scoop\apps\temurin8-jdk\current\bin`（可选；有 shims 通常够用）  
5. 确定保存 → **重开终端**。

### 4.3 用 PowerShell 改（需管理员改 Machine 级）

你当前 `JAVA_HOME` 在 **Machine（系统）** 级，改系统变量需要**管理员 PowerShell**：

```powershell
# --- 管理员 PowerShell ---

# 1) JAVA_HOME → Scoop 的 8（日常默认）
[Environment]::SetEnvironmentVariable(
  "JAVA_HOME",
  "D:\Scoop\apps\temurin8-jdk\current",
  "Machine"
)

# 2) 从系统 Path 去掉旧 JDK 路径（保留其它）
$oldPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$parts = $oldPath -split ';' | Where-Object {
  $_ -and
  $_ -notmatch 'D:\\Java\\jdks\\jdk-8' -and
  $_ -notmatch 'D:\\Java\\jdks\\jdk-21'
}
[Environment]::SetEnvironmentVariable("Path", ($parts -join ';'), "Machine")
```

用户级确认 Scoop 在 PATH（一般安装已写好）：

```powershell
# 普通用户 PowerShell 即可
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notmatch 'D:\\Scoop\\shims') {
  [Environment]::SetEnvironmentVariable(
    "Path",
    "D:\Scoop\shims;$userPath",
    "User"
  )
}
```

### 4.4 验证环境（新开终端）

```powershell
echo $env:JAVA_HOME
# 期望：D:\Scoop\apps\temurin8-jdk\current

where.exe java
# 期望优先出现：D:\Scoop\shims\java.exe

java -version
# openjdk version "1.8.0_xxx" 或你 reset 后的版本

mvn -version
# Java version 应来自当前 JAVA_HOME
```

---

## 五、日常如何切换 8 / 17 / 21

### 5.1 手动两步（理解原理）

```powershell
# 把 shims 里的 java 切到 21
scoop reset temurin21-jdk

# Maven 等还看 JAVA_HOME，必须一起改（当前终端临时）
$env:JAVA_HOME = "D:\Scoop\apps\temurin21-jdk\current"
$env:Path = "D:\Scoop\shims;D:\Scoop\apps\temurin21-jdk\current\bin;" + $env:Path

java -version
mvn -version
```

切回 8：

```powershell
scoop reset temurin8-jdk
$env:JAVA_HOME = "D:\Scoop\apps\temurin8-jdk\current"
```

若希望**全局默认**也变成 21：把系统 `JAVA_HOME` 改成 `temurin21-jdk\current`，并再执行一次 `scoop reset temurin21-jdk`。

### 5.2 一键脚本（推荐）

把下面存为 `D:\Java\use-jdk.ps1`：

```powershell
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("8", "17", "21")]
  [string]$Version
)

$map = @{
  "8"  = "temurin8-jdk"
  "17" = "temurin17-jdk"
  "21" = "temurin21-jdk"
}

$app = $map[$Version]
$home = "D:\Scoop\apps\$app\current"

if (-not (Test-Path "$home\bin\java.exe")) {
  Write-Error "未找到 $home 。请先: scoop install $app"
  exit 1
}

scoop reset $app | Out-Null
$env:JAVA_HOME = $home

# 把本 JDK 的 bin 提到 PATH 前面，并去掉其它 temurin*\current\bin，避免混乱
$rest = ($env:Path -split ';' | Where-Object {
  $_ -and $_ -notmatch 'D:\\Scoop\\apps\\temurin\d+-jdk\\current\\bin'
}) -join ';'
$env:Path = "D:\Scoop\shims;$home\bin;$rest"

Write-Host "JAVA_HOME=$env:JAVA_HOME"
& "$home\bin\java.exe" -version
```

用法（当前终端生效）：

```powershell
# 若提示无法运行脚本：
# Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

D:\Java\use-jdk.ps1 21
D:\Java\use-jdk.ps1 8
```

> 脚本只改**当前终端**的 `JAVA_HOME`。要改「新开终端的默认」，仍需改系统环境变量里的 `JAVA_HOME`。

---

## 六、Cursor / 本项目（diagnostic-lab）怎么配

`diagnostic-lab` 需要 **21**。在项目下建 `.vscode/settings.json`：

```json
{
  "java.configuration.runtimes": [
    {
      "name": "JavaSE-1.8",
      "path": "D:\\Scoop\\apps\\temurin8-jdk\\current"
    },
    {
      "name": "JavaSE-21",
      "path": "D:\\Scoop\\apps\\temurin21-jdk\\current",
      "default": true
    }
  ],
  "java.jdt.ls.java.home": "D:\\Scoop\\apps\\temurin21-jdk\\current",
  "terminal.integrated.env.windows": {
    "JAVA_HOME": "D:\\Scoop\\apps\\temurin21-jdk\\current"
  }
}
```

说明：

- 扩展 Run/Debug → 用上面的 21  
- 该工作区集成终端 → `JAVA_HOME` 指向 21  
- 打开工作区后若终端已开过，**再开一个新终端**再跑 `mvn`

---

## 七、迁完验收清单（删旧目录之前）

在**新开**的 PowerShell 里逐项打勾：

```powershell
# 1) 不应再出现 D:\Java\jdks
where.exe java
echo $env:JAVA_HOME

# 2) 默认 8（若你按本文把默认设为 8）
java -version
mvn -version

# 3) 能切到 21
D:\Java\use-jdk.ps1 21
java -version
mvn -version

# 4) 能切回 8
D:\Java\use-jdk.ps1 8

# 5) diagnostic-lab
cd "D:\code-self\thinking-space\AI\后端\Java\进阶\jvm排查\diagnostic-lab"
D:\Java\use-jdk.ps1 21
mvn -q -DskipTests package
```

全部正常后，再删旧 JDK。

---

## 八、删除旧 JDK（确认后再做）

1. 确认没有程序、服务、计划任务还写死 `D:\Java\jdks\...`  
2. 删除文件夹：  
   - `D:\Java\jdks\jdk-8.0.504.1-hotspot`  
   - `D:\Java\jdks\jdk-21.0.11_10`  
3. `D:\Java\maven` **不要删**  
4. 可保留空的 `D:\Java\jdks` 或整目录删掉（若已空）

---

## 九、常用 Scoop 命令速查

```powershell
scoop list                          # 已装软件
scoop update                        # 更新 Scoop 自己
scoop update temurin21-jdk          # 更新某个 JDK
scoop reset temurin21-jdk           # 切换 shim 到该 JDK
scoop uninstall temurin17-jdk       # 卸载某版本
scoop cleanup temurin21-jdk         # 清旧版本缓存
```

---

## 十、常见问题

### Q1：`scoop` 不是内部或外部命令

- 重开终端  
- 检查用户 PATH 是否有 `D:\Scoop\shims`  
- 确认曾设置用户环境变量 `SCOOP=D:\Scoop`

### Q2：`java -version` 是 21，但 `mvn -version` 还是 8

- Maven 看 `JAVA_HOME`，只 `scoop reset` 不够  
- 执行 `use-jdk.ps1` 或手动改 `JAVA_HOME` 后重开终端

### Q3：Cursor 终端里还是旧 JDK

- 改环境变量后必须重启 Cursor  
- 或看工作区 `terminal.integrated.env.windows` 是否覆盖了 `JAVA_HOME`

### Q4：公司代理导致 scoop install 失败

- 配置系统代理或 Scoop proxy（`scoop help proxy`）  
- 或临时用手机热点试网络

### Q5：还要不要留一份「免安装」解压版？

- 一般不必。Scoop 的 `current` 目录本身就能当 `JAVA_HOME`  
- 若极端环境不能用 Scoop，再保留一个官方 zip 备份即可

---

## 十一、推荐操作顺序（照着做）

1. 安装 Scoop 到 `D:\Scoop`  
2. `scoop bucket add java` → 安装 `temurin8-jdk`、`temurin21-jdk`  
3. 改系统 `JAVA_HOME` + 清理 Path 里旧 `D:\Java\jdks`  
4. 新开终端验收 `java` / `mvn`  
5. 写好 `D:\Java\use-jdk.ps1`  
6. Cursor 项目里配 21（如 diagnostic-lab）  
7. 全部 OK 后再删 `D:\Java\jdks` 下旧目录  

---

## 十二、和「不迁 Scoop」的对比（心里有数）

| | 继续用 `D:\Java\jdks` | 迁到 Scoop |
|--|----------------------|------------|
| 可靠性 | 高（你已在用） | 同样高（Temurin） |
| 多版本切换 | 脚本改 JAVA_HOME | `scoop reset` + JAVA_HOME |
| 升级 | 自己下包解压 | `scoop update temurinXX-jdk` |
| 磁盘 | 不占双份 | 迁移期会双份，删旧后恢复 |

迁完后你就和多数 Windows 用 Scoop 管 JDK 的人同一套习惯了。
