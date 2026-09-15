# 阶段 A：软件 / 语言清单与安装教程（Windows）

> 对应选型文档：**先仿真 + Python 主链路**。  
> 仿真栈定稿：**WSL2 Ubuntu 24.04 + ROS2 Jazzy + Gazebo Harmonic**。  
> Node / Ollama / Vue 可在 **Windows 本机**。（你本机已有 Git、Node、Ollama、Qwen，可跳过对应安装。）

---

## 0. 装在哪（先记住）

| 环境 | 装什么 |
| ---- | ---- |
| **Windows 本机** | Git、Node.js、Vue 脚手架、Ollama、VS Code / Cursor、（可选）MQTTX |
| **WSL2 · Ubuntu 24.04** | Python3、ROS2 Jazzy、Gazebo Harmonic（`ros-jazzy-ros-gz`）、Mosquitto、YOLO/Whisper/Piper 的 Python 包 |

原则：**机器人仿真与 ROS 全在 WSL2**；**前端控制台在 Windows**；两边用局域网 IP / `localhost` 互通（WSL2 下 MQTT 注意端口）。

---

## 1. 语言与软件总表

### 语言

| 语言 | 用途 | 是否必须（阶段 A） |
| ---- | ---- | ---- |
| **Python 3.10+**（24.04 自带 3.12 即可） | ROS2 节点、MQTT 服务、Ollama 调用、YOLO、Whisper、Piper | **必须** |
| **JavaScript / TypeScript** | Vue3 + Three.js 控制台 | **必须**（控制台） |
| Java | 管理后台 | 阶段 A **先不装不学** |
| C++ | ROS2 底层可选 | 阶段 A **可后补** |

### 软件 / 工具

| 软件 | 用途 | 环境 |
| ---- | ---- | ---- |
| Git | 拉代码 | Win + WSL |
| WSL2 + Ubuntu 24.04 | 跑 ROS2 / 仿真 | Win 功能（你已有） |
| ROS2 Jazzy | 导航、节点、话题 | WSL（待装） |
| Gazebo Harmonic（经 ros-gz） | 家庭场景仿真 | WSL（待装） |
| Mosquitto | MQTT Broker | WSL（待装） |
| Ollama | 本地 LLM（Qwen） | Win（你已有） |
| Node.js 20+ | Vue 项目 | Win（你已有 22） |
| Vue3 + Vite | 控制台 | Win |
| Three.js | 3D / 地图可视化 | npm 依赖 |
| Cursor / VS Code + WSL 插件 | 开发 | Win |
| MQTTX（可选） | 手动看 MQTT 消息 | Win |
| Redis（可选） | 原型缓存 | 后期 |
| SQLite | 原型存储 | Python 自带/轻量 |

### Python 包（阶段 A 会用到，先知道名字）

| 包 | 用途 |
| ---- | ---- |
| `paho-mqtt` 或 `aiomqtt` | MQTT 客户端 |
| `ollama`（或 HTTP 调本地 API） | 调本地大模型 |
| `ultralytics` | YOLOv8/v11 |
| `openai-whisper` 或更快的 `faster-whisper` | ASR |
| Piper（二进制 + 模型） | TTS |

> 这些包等 ROS2 / Ollama 就绪后再装，避免环境乱。

---

## 2. 推荐安装顺序（按你当前环境）

```text
你已有：Win Git / Node / Ollama+Qwen / WSL Ubuntu 24.04 / Cursor
还缺：WSL 里 pip、ROS2 Jazzy、Gazebo Harmonic、Mosquitto

1. WSL 装基础：python3-pip、venv、编译工具
2. WSL 装 ROS2 Jazzy + ros-jazzy-ros-gz + Mosquitto
3. 验证：ros2 / gz / mosquitto / ollama / node
4. 再建 Vue 项目 + 装 Python AI 包
```

---

## 3. 安装教程

### 3.1 Git / Node / Ollama（Windows）

你这边多数已就绪，自检即可：

```powershell
git --version
node -v
npm -v
ollama list
# 应能看到 qwen2.5:7b-instruct-q4_K_M 等
```

缺什么再装：

- Git：https://git-scm.com/download/win  
- Node：https://nodejs.org/（20 LTS 或你现有的 22 均可）  
- Ollama：https://ollama.com/download  

```powershell
ollama pull qwen2.5:7b-instruct-q4_K_M   # 你已有可跳过
```

API 默认：`http://localhost:11434`

---

### 3.2 WSL2 + Ubuntu 24.04

你已有发行版名为 `Ubuntu`，版本 **24.04.1**，**不必再装 22.04**。

自检：

```powershell
wsl -l -v
wsl -d Ubuntu -- cat /etc/os-release
# 确认 VERSION_ID="24.04"
```

进入 WSL 后补齐基础包（你目前缺 pip）：

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl wget git \
  python3 python3-pip python3-venv python3-colcon-common-extensions
python3 --version   # 期望 3.12.x
pip3 --version
```

> Win10/11 + 较新 WSL 可用 WSLg 弹 Gazebo 窗口。若黑屏/无界面，再查「WSLg / 显卡驱动」。

**Cursor / VS Code**：装扩展 `WSL`，用「在 WSL 中打开文件夹」开发。

---

### 3.3 ROS2 Jazzy（WSL · Ubuntu 24.04）

官方文档：https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html  

在 **Ubuntu 终端**执行：

```bash
# 语言环境
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt install -y software-properties-common
sudo add-apt-repository universe -y

sudo apt update && sudo apt install -y curl gnupg lsb-release

# 添加 ROS2 apt 源
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt upgrade -y

# 桌面版（学习/仿真推荐）
sudo apt install -y ros-jazzy-desktop
sudo apt install -y ros-dev-tools
```

每次开终端加载 ROS（写入 `~/.bashrc`）：

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

验证：

```bash
printenv ROS_DISTRO    # 应为 jazzy
ros2 --help
# 开两个终端：
# 终端1: ros2 run demo_nodes_cpp talker
# 终端2: ros2 run demo_nodes_py listener
```

---

### 3.4 Gazebo（Jazzy 官方配 Harmonic）

Jazzy 官方配套是 **Gazebo Harmonic**。用 ROS 源装桥接即可，**不要**再混装 Fortress / Classic 等冲突包：

```bash
sudo apt update
sudo apt install -y ros-jazzy-ros-gz
```

启动仿真：

```bash
source /opt/ros/jazzy/setup.bash
gz sim
```

能出仿真窗口即成功。家庭场景模型以后再加，先保证能开。

> 网上若仍写 `ign gazebo`，那是旧 Fortress 习惯；Jazzy + Harmonic 优先用 `gz sim`。

---

### 3.5 Mosquitto（MQTT Broker，WSL）

```bash
sudo apt install -y mosquitto mosquitto-clients
sudo service mosquitto start
# 若用 systemd：
# sudo systemctl enable --now mosquitto

# 本机测通
mosquitto_sub -t 'test/topic' -v &
mosquitto_pub -t 'test/topic' -m 'hello'
```

Windows 上的 Vue 若要连 WSL 里的 Mosquitto：

```bash
hostname -I    # 在 Ubuntu 里看 WSL IP
```

前端连：`mqtt://<WSL的IP>:1883`。  
或在 Windows 另装 Mosquitto，统一 `localhost:1883`（二选一，别两套一起乱连）。

---

### 3.6 Vue3 控制台（Windows）

```powershell
npm create vite@latest pet-robot-console -- --template vue
cd pet-robot-console
npm install
npm install three mqtt
npm run dev
```

Three.js 用于 3D/地图；`mqtt` 用于连 Broker。

---

### 3.7 Python AI 包（WSL 虚拟环境，装完 ROS 再做）

```bash
mkdir -p ~/pet-robot && cd ~/pet-robot
python3 -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install paho-mqtt ultralytics faster-whisper
# Ollama：pip install ollama，或 requests 调 http://<Windows主机IP>:11434
```

从 WSL 访问 Windows 上的 Ollama：在 Ubuntu 执行 `cat /etc/resolv.conf` 看 `nameserver`（多为 Win 主机 IP），浏览器/curl 测 `http://该IP:11434`。若连不上，检查 Windows 防火墙是否放行 11434。

Piper TTS：https://github.com/rhasspy/piper/releases 下 Linux 二进制与语音模型。

> ROS 节点多用系统/`rosdep` 习惯；**AI 推理包放 venv**，避免一个环境硬揉所有依赖。

---

## 4. 装完验收清单

| 检查项 | 命令 / 动作 | 期望 |
| ---- | ---- | ---- |
| WSL | `wsl -l -v` | `Ubuntu` Running，VERSION=2，系统 24.04 |
| Python | `python3 --version` / `pip3 --version` | 3.12+ / pip 可用 |
| ROS2 | `printenv ROS_DISTRO` / `ros2 doctor` | `jazzy`，无明显致命错误 |
| Gazebo | `gz sim` | 出窗口 |
| MQTT | `mosquitto_pub/sub` | 能收到 hello |
| Ollama | `ollama list`（Win） | 有 qwen 等模型 |
| Node | `npm run dev` | 浏览器打开 Vite 页 |

---

## 5. 你近期最小闭环

```text
WSL: Gazebo Harmonic + ROS2 Jazzy + Mosquitto +（稍后）Python MQTT/假指令
Win: Ollama(已有) + Vue 控制台
     ↓
先打通：假 AI 指令 → MQTT → 仿真车动起来
再换真：Ollama / YOLO / 语音
最后：买带 WiFi 的 ROS2/Micro-ROS 小车
```

---

## 6. 先不要装的（省时间）

- 再装 Ubuntu 22.04 / ROS2 Humble（与当前路线重复）  
- RK3566 / RK3588 与 RKNN  
- Android/iOS 本地推理  
- Java 后台、PostgreSQL 集群  
- 4G / 物联网卡相关  

---

## 7. 官方文档速查

- ROS2 Jazzy：https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html  
- Gazebo + ROS（Harmonic / Jazzy）：https://gazebosim.org/docs/harmonic/ros_installation/  
- Ollama：https://ollama.com  
- Mosquitto：`sudo apt install mosquitto`  
- Vite + Vue：https://vitejs.dev/guide/  

若某一步报错，把**完整终端输出**贴出来再继续；不要混装 Humble 与 Jazzy，也不要混装多个 Gazebo 大版本。
