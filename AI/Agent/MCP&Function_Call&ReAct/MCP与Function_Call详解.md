# MCP 与 Function Call 详解

## 一、概念定义

### 1.1 Function Call（函数调用）

**Function Call** 是 LLM（大语言模型）的一项原生能力，允许模型在生成回复时"决定"调用一个预定义的函数，并输出结构化的参数。

> 严格来说，模型并不会真正执行函数，而是输出一个**调用意图**（通常是 JSON 格式），由你的应用代码接收、解析、执行，然后把结果回传给模型。

**关键角色：**
- **LLM 提供商**（OpenAI / Anthropic / 通义千问等）定义 Function Call 的协议
- **开发者**在请求中声明可用的函数列表（名称、描述、参数 JSON Schema）
- **模型**决定是否调用、调用哪个、传什么参数
- **应用层**实际执行函数，拿到结果后拼入下一轮对话

**核心原理图：**

```
用户提问
   │
   ▼
┌──────────────┐
│   LLM 模型    │ ◄── 声明可用函数: [get_weather, search_database, ...]
└──────┬───────┘
       │ 输出: { "function_call": "get_weather", "arguments": { "city": "北京" } }
       ▼
┌──────────────┐
│  应用层代码   │ 解析 function_call → 调用真实 API → 拿到结果
└──────┬───────┘
       │ 结果回传: { "temperature": 25, "condition": "晴" }
       ▼
┌──────────────┐
│   LLM 模型    │ 基于结果生成自然语言回复
└──────────────┘
       │
       ▼
   "北京今天晴天，气温25°C"
```

---

### 1.2 MCP（Model Context Protocol）

**MCP** 是 Anthropic 于 2024 年底提出的一种**开放协议标准**，旨在统一 LLM 与外部工具/数据源之间的交互方式。

> 类比：如果 Function Call 是"USB 接口"，那 MCP 就是"USB 标准协议"——它不定义接口本身，而是定义一套规范，让任何模型、任何工具都能用同一种方式对接。

**MCP 的架构：**

```
┌──────────────────────────────────────────────┐
│               MCP Host（宿主应用）               │
│        例如：Claude Desktop、VS Code、你的 App   │
│                   │                            │
│         ┌─────────┴─────────┐                  │
│         │   MCP Client      │                  │
│         │  (协议客户端层)    │                  │
│         └────────┬─────────┘                  │
└──────────────────┼────────────────────────────┘
                   │ JSON-RPC over stdio / HTTP SSE
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  MCP     │ │  MCP     │ │  MCP     │
│ Server A │ │ Server B │ │ Server C │
│ (文件)   │ │ (数据库)  │ │ (API)    │
└──────────┘ └──────────┘ └──────────┘
```

**MCP 三大核心概念：**

| 概念 | 说明 | 类比 |
|------|------|------|
| **Resources（资源）** | 暴露数据给模型读取（如文件内容、数据库记录） | GET 请求 |
| **Tools（工具）** | 让模型可以执行操作（如创建文件、发送请求） | POST 请求 |
| **Prompts（提示模板）** | 预定义的提示词模板，方便用户快速调用 | 快捷指令 |

---

## 二、核心区别对比

| 维度 | Function Call | MCP |
|------|--------------|-----|
| **定义者** | LLM 提供商（OpenAI、Anthropic 等） | Anthropic 提出的开放协议 |
| **范围** | 单个模型的能力 | 模型无关的通用协议 |
| **绑定方式** | 紧耦合，和特定 API 绑定 | 松耦合，通过标准协议对接 |
| **工具发现** | 开发者在请求中硬编码函数列表 | MCP Server 自己声明能提供什么 |
| **通信机制** | 嵌入在 Chat Completion 请求/响应中 | JSON-RPC 2.0 over stdio / HTTP SSE |
| **复用性** | 每个应用需要自己对接 | 一次编写 MCP Server，多处使用 |
| **生态** | 各厂商各自为政 | 统一生态，社区共建 |

---

## 三、MCP vs Function Call 详细对比

### 3.1 架构层面

**Function Call：** 模型内嵌能力，工具定义随 API 请求一起发送，模型在推理时"顺便"决定调用。

**MCP：** 在模型和工具之间加了一层**中间协议层**。MCP Server 独立运行，通过标准协议暴露资源和工具。MCP Client 连接 Server，收集可用工具列表，再交给 LLM 决策。

### 3.2 执行流程对比

**Function Call 流程：**

```
① 开发者硬编码函数定义
       │
       ▼
② 发送给 LLM（随聊天请求一起）
       │
       ▼
③ LLM 推理 → 输出 function_call
       │
       ▼
④ 应用层解析 → 执行函数
       │
       ▼
⑤ 结果回传给 LLM → 生成最终回复
```

**MCP 流程：**

```
① MCP Server 启动，暴露 Tools 列表
       │
       ▼
② MCP Client 连接 Server → 自动发现可用工具
       │
       ▼
③ 将工具列表转为 LLM Function Call 格式 → 发送给模型
       │
       ▼
④ LLM 推理 → 输出 function_call
       │
       ▼
⑤ MCP Client 将 function_call 转为 JSON-RPC → 发给 MCP Server
       │
       ▼
⑥ MCP Server 执行 → 返回结果
       │
       ▼
⑦ 结果回传给 LLM → 生成最终回复
```

**核心差异：** 步骤⑤⑥中，MCP 通过标准协议转发调用，而非直接在应用层执行。

### 3.3 实际收益

**MCP 解决的核心问题：**

1. **工具复用：** 一个 MCP Server（如"文件系统 Server"）写好之后，Claude Desktop、VS Code、你的自建 App 都能用，不需要每个应用都写一遍文件读写逻辑。
2. **解耦模型和工具：** 换模型不需要改工具代码，换工具实现也不需要改模型调用层。
3. **统一安全边界：** MCP Server 独立进程运行，可以做权限控制、沙箱隔离。
4. **社区生态：** 像 npm 一样，MCP 社区可以共享 Server 实现。

---

## 四、应用场景

### 4.1 Function Call 的典型场景

| 场景 | 说明 |
|------|------|
| **天气查询** | 用户问"北京今天天气"→ 模型调用 get_weather(city="北京") → 返回结果 |
| **数据库查询** | 用户问"上周订单总数"→ 模型调用 query_database(sql="SELECT...") |
| **发送邮件** | 用户说"帮我发邮件给张三"→ 模型调用 send_email(to, subject, body) |
| **控制智能家居** | 用户说"把客厅灯关了"→ 模型调用 control_device(room="客厅", action="off") |
| **RAG 检索** | Agent 需要查知识库 → 调用 search_knowledge_base(query) |

### 4.2 MCP 的典型场景

| 场景 | 说明 |
|------|------|
| **AI 编程助手** | MCP Server 暴露文件系统，Claude/VSCode 都能直接操作项目文件 |
| **企业数据中台** | 一个 MCP Server 封装所有数据库/API，不同 AI 应用统一接入 |
| **浏览器自动化** | MCP Server 封装 Puppeteer/Playwright，让 LLM 操作浏览器 |
| **多 Agent 协作** | 多个 Agent 通过不同 MCP Server 获取不同能力 |
| **企业内部工具集成** | 把 Jira、Confluence、GitLab 各封装为 MCP Server，AI 统一调度 |

---

## 五、代码示例

### 5.1 Function Call 示例（OpenAI 风格）

```javascript
// 定义可用函数
const tools = [
  {
    type: "function",
    function: {
      name: "get_weather",
      description: "获取指定城市的天气",
      parameters: {
        type: "object",
        properties: {
          city: { type: "string", description: "城市名，如'北京'" }
        },
        required: ["city"]
      }
    }
  }
];

// 发送请求
const response = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [{ role: "user", content: "北京今天天气怎么样？" }],
  tools: tools
});

// 模型返回 function_call
const toolCall = response.choices[0].message.tool_calls[0];
console.log(toolCall.function.name);      // "get_weather"
console.log(toolCall.function.arguments); // '{"city":"北京"}'

// 应用层执行函数
const result = await realGetWeather("北京");

// 把结果回传给模型
const finalResponse = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [
    { role: "user", content: "北京今天天气怎么样？" },
    { role: "assistant", tool_calls: [toolCall] },
    { role: "tool", tool_call_id: toolCall.id, content: JSON.stringify(result) }
  ]
});
```

### 5.2 MCP 客户端示例（TypeScript）

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

// 启动 MCP Server 并建立连接
const transport = new StdioClientTransport({
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
});

const client = new Client({ name: "my-app", version: "1.0.0" });
await client.connect(transport);

// 自动发现工具列表
const tools = await client.listTools();
console.log(tools);
// → [{ name: "read_file", description: "读取文件", inputSchema: {...} },
//    { name: "write_file", description: "写入文件", inputSchema: {...} }]

// LLM 决定调用 read_file 后，执行工具
const result = await client.callTool({
  name: "read_file",
  arguments: { path: "/path/to/allowed/dir/notes.txt" }
});
console.log(result);
// → [{ type: "text", text: "文件内容..." }]
```

---

## 六、MCP 目前的问题

| 问题 | 说明 |
|------|------|
| **协议较新** | 2024 年底才发布，生态还在早期阶段 |
| **工具实现少** | 官方和社区 Server 数量有限，需要自行开发 |
| **主要支持 Anthropic** | OpenAI 尚未官方支持 MCP，但可通过适配层对接 |
| **安全风险** | MCP Server 独立进程运行，需注意权限控制和沙箱 |
| **调试困难** | 协议链路过长（LLM → Client → Server），问题排查复杂 |

---

## 七、总结

```
┌─────────────────────────────────────────────────────────────────┐
│                      一句话总结                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Function Call = LLM 输出调用意图，应用层执行                        │
│                                                                  │
│  MCP = 标准化 LLM 和工具之间的交互协议（模型无关、工具复用）          │
│                                                                  │
│  关系：MCP Server 暴露的 Tools，最终也会转为 Function Call 格式       │
│       喂给 LLM。MCP 是 Function Call 的上层封装和标准化。            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**选择建议：**

| 场景 | 推荐 |
|------|------|
| 快速原型、单个应用、简单工具 | 直接使用 Function Call |
| 多应用共享工具、企业级架构、长期维护 | 使用 MCP 标准化 |
| 需要对接多种 LLM 提供商 | MCP（模型无关） |
| 使用 Claude Desktop / Cursor 等 MCP 原生应用 | MCP |

> **实际开发中：** MCP 和 Function Call 不是二选一的关系。你在 Agent 里用 MCP Client 连接各个 MCP Server，拿到工具列表，然后转换成 Function Call 格式传给 LLM——MCP 是工具管理层的标准，Function Call 是 LLM 推理层的机制，两者协作使用。

---

*文档生成时间：2026年7月14日*
