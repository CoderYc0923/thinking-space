# Agent 标准开发流程 —— 完整知识详解（TypeScript 版）

> 本文档系统讲解 Agent 标准开发流程，涵盖 LLM 底层原理、LangChain 架构、Prompt Engineering、RAG 全链路、Agent 核心机制、Memory 记忆管理及生产环境注意事项，基于 TypeScript 实现。

---

## 目录

- [一、LLM 的本质与局限](#一llm-的本质与局限)
- [二、LangChain 架构深度拆解](#二langchain-架构深度拆解)
- [三、Prompt Engineering 核心概念](#三prompt-engineering-核心概念)
- [四、RAG 全链路原理深度拆解](#四rag-全链路原理深度拆解)
- [五、Agent 核心机制彻底剖析](#五agent-核心机制彻底剖析)
- [六、Memory（记忆）深度解析](#六memory记忆深度解析)
- [七、完整的 Agent 项目架构](#七完整的-agent-项目架构)
- [八、生产环境注意事项](#八生产环境注意事项)

---

## 一、LLM 的本质与局限

在讲 Agent 之前，必须先理解它操控的"大脑"——LLM（大语言模型）到底是什么。

### 1.1 LLM 的本质：一个"概率预测机"

LLM 的本质是一个**自回归语言模型**。它的核心任务非常简单：

> 给定一段文本（prompt），预测下一个最可能出现的 token（词元）。

数学表达为：

```
P(token_n | token_1, token_2, ..., token_{n-1})
```

**关键概念——Token（词元）**：

- 不是"单词"，而是更小的语言单元。比如 `"ChatGPT"` 可能被拆成 `["Chat", "G", "PT"]` 三个 token
- 中文一个汉字通常就是一个 token，英文一个常见词可能 1-2 个 token
- Token 数量决定了 API 费用和上下文长度上限

**关键概念——Context Window（上下文窗口）**：

- 模型一次性最多能"看到"的 token 总数（输入+输出）
- GPT-4 Turbo 是 128K tokens，Claude 3 是 200K tokens
- 这决定了你能塞给模型多少背景知识

### 1.2 LLM 的三大先天缺陷 → 催生了 Agent 和 RAG

| 缺陷 | 表现 | 解决方案 |
|------|------|---------|
| **知识截止** | 训练数据有时间上限，不知道最新信息 | **RAG**：动态检索外部知识 |
| **幻觉（Hallucination）** | 会自信地编造不存在的事实 | **RAG**：用真实文档约束回答 |
| **无行动能力** | 只会"说"，不会"做"（查数据库、调 API、计算） | **Agent + Tools**：赋予调用外部工具的能力 |
| **无规划能力（纯推理）** | 只能一次生成，无法分解复杂任务 | **Agent ReAct 循环**：思考→行动→观察 |

---

## 二、LangChain 架构深度拆解

### 2.1 LangChain 是什么？为什么需要它？

**一句话定义**：LangChain 是一个**将 LLM 与外部世界（数据、工具、记忆）连接的编排框架**。

**没有 LangChain 时你要做的事**：

```typescript
// 原始调用：你要手动管理一切
const messages = [
  { role: "system", content: "你是助手，可以使用这些工具：计算器..." },
  { role: "user", content: "1+1等于多少" },
  { role: "assistant", content: "我需要用计算器", tool_calls: [...] },
  { role: "tool", content: "2", tool_call_id: "xxx" },
  { role: "assistant", content: "答案是2" },
];
// 手动拼接 → 调 API → 解析 → 执行工具 → 再拼接 → 再调 API...
// 这是一个极其繁琐的状态机
```

**LangChain 帮你做的事**：

- 自动管理消息拼接和状态流转
- 统一封装各种 LLM 的调用接口
- 提供标准化的工具定义和调用协议
- 内置多种记忆管理策略
- 处理错误重试、输出解析等边界情况

### 2.2 LangChain 核心模块详解

```
LangChain 架构
├── Model I/O          ← LLM 的输入输出统一封装
│   ├── Prompt Templates    ← 结构化提示词模板
│   ├── Chat Models         ← 各种聊天模型统一接口
│   └── Output Parsers      ← 把 LLM 输出解析成结构化数据
│
├── Retrieval          ← RAG 的数据管道
│   ├── Document Loaders    ← 加载各种格式文件
│   ├── Text Splitters      ← 智能文本分割
│   ├── Embeddings          ← 文本转向量
│   ├── Vector Stores       ← 向量存储与相似搜索
│   └── Retrievers          ← 检索器统一接口
│
├── Chains             ← 串联多个步骤形成流水线
│   ├── LLMChain            ← 基础：Prompt → LLM → Output
│   ├── SequentialChain     ← 顺序执行多条链
│   └── RetrievalQAChain    ← 检索+生成的专用链
│
├── Agents & Tools     ← 智能体循环决策
│   ├── Agent Types         ← ReAct / OpenAI Functions / Plan-Execute
│   ├── Tools               ← 计算器、搜索、API、数据库等
│   └── AgentExecutor       ← 运行 Agent 循环的引擎
│
├── Memory             ← 对话状态管理
│   ├── BufferMemory        ← 全量存储历史
│   ├── SummaryMemory       ← 自动摘要压缩
│   └── VectorStoreMemory   ← 向量检索历史
│
└── Callbacks          ← 事件钩子（日志、监控、流式输出）
```

### 2.3 环境准备

```bash
mkdir agent-dev-tutorial
cd agent-dev-tutorial
npm init -y
npm install langchain @langchain/openai @langchain/community
npm install -D typescript @types/node ts-node dotenv
npx tsc --init
```

在 `tsconfig.json` 中确保：

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "esModuleInterop": true,
    "outDir": "./dist",
    "strict": true
  }
}
```

`.env` 文件：

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx
```

---

## 三、Prompt Engineering 核心概念

Prompt 是你和大模型沟通的唯一语言。理解 Prompt 的设计原理是构建 Agent 的基础。

### 3.1 Prompt Template（提示词模板）

**核心思想**：把变化的部分（用户输入）和不变的部分（指令）分离。

```typescript
import { PromptTemplate } from "@langchain/core/prompts";

const template = new PromptTemplate({
  template: `
你是一个{role}，擅长{skill}。
请用{style}的风格回答以下问题。

问题：{question}
回答：`,
  inputVariables: ["role", "skill", "style", "question"],
});

const formatted = await template.format({
  role: "法律顾问",
  skill: "合同法",
  style: "严谨专业",
  question: "劳动合同解除需要注意什么？"
});
```

### 3.2 LangChain 中三种常用 Prompt 类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `PromptTemplate` | 纯文本模板 | 简单问答 |
| `ChatPromptTemplate` | 结构化消息列表 | 多轮对话，区分 system/user/assistant |
| `MessagesPlaceholder` | 占位符（注入历史消息） | Agent 的记忆注入点 |

```typescript
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";

const chatTemplate = ChatPromptTemplate.fromMessages([
  ["system", "你是一个{role}，你可以使用以下工具：{tools}"],
  ["user", "{input}"],
  new MessagesPlaceholder("agent_scratchpad"), // ← Agent 的思考轨迹注入点
]);
```

---

## 四、RAG 全链路原理深度拆解

RAG（Retrieval-Augmented Generation）不是简单的"搜一下再回答"，而是一个**数据工程管道**。

### 4.1 RAG 的完整数据流

```
┌─────────────────────────────────────────────────────────────┐
│                      离线阶段（数据预处理）                    │
├─────────────────────────────────────────────────────────────┤
│ 原始文档 → Document Loader → Text Splitter → Embeddings     │
│                                              ↓               │
│                                    Vector Store (持久化)     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      在线阶段（查询时）                       │
├─────────────────────────────────────────────────────────────┤
│ 用户问题 → Embedding → 向量相似搜索 → 召回Top-K文档片段       │
│                                              ↓               │
│                    把文档片段注入 Prompt                      │
│                                              ↓               │
│                                  LLM 基于参考资料生成答案     │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Document Loader（文档加载器）

负责把各种格式的原始数据加载成 LangChain 的 `Document` 对象。

```typescript
// Document 结构
interface Document {
  pageContent: string;  // 文档正文
  metadata: {           // 元数据（来源、页码、作者等）
    source: string;
    page?: number;
    [key: string]: any;
  };
}
```

支持的加载器（TypeScript）：

- `TextLoader` - 纯文本
- `PDFLoader` - PDF（需要 `pdf-parse`）
- `CSVLoader` - CSV 表格
- `JSONLoader` - JSON 数据
- `DirectoryLoader` - 批量加载目录
- `CheerioWebBaseLoader` - 爬取网页
- `NotionLoader`、`GitHubRepoLoader` 等

```typescript
import { TextLoader } from "langchain/document_loaders/fs/text";

const loader = new TextLoader("./knowledge-base.txt");
const docs = await loader.load();
```

### 4.3 Text Splitter（文本分割器）—— 最容易被忽视的关键环节

**为什么需要分割？**

1. LLM 的上下文窗口有限（塞不下整本书）
2. 太长的文本会让 Embedding 语义稀释
3. 精准检索需要适中的粒度

**分割的核心矛盾**：太小丢失上下文，太大检索不准。

**LangChain 提供的分割策略**：

| 分割器 | 原理 | 适用场景 |
|--------|------|---------|
| `RecursiveCharacterTextSplitter` | 按 `\n\n→\n→空格→字符` 优先级递归切分 | **通用首选** |
| `MarkdownTextSplitter` | 保持标题和段落的层次结构 | Markdown 文档 |
| `TokenTextSplitter` | 按 Token 数量精确控制 | 需严格控制 token 预算 |
| `CodeTextSplitter` | 按代码语义（函数/类边界）切分 | 代码库 |

```typescript
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,    // 每块最多 500 字符
  chunkOverlap: 50,  // 相邻块重叠 50 字符（保证语义连贯）
  separators: ["\n\n", "\n", "。", ".", " ", ""], // 切分优先级
});

const splitDocs = await splitter.splitDocuments(docs);
```

**chunkOverlap 的作用**：防止关键信息恰好在切割边界被截断。比如 "张三...（切割）...获得了诺贝尔奖"，检索时可能分别命中两个 chunk，LLM 就看不到完整信息。

### 4.4 Embeddings（嵌入）—— 文本如何变成可计算的向量

**本质**：把一个高维离散的文本空间映射到低维连续向量空间，语义相似的文本在向量空间中距离更近。

```
"苹果是一种水果" → Embedding模型 → [0.023, -0.451, 0.892, ..., 0.134]
                                     ↑ 1536维浮点数向量
"苹果是一家科技公司" → [0.031, -0.398, 0.901, ..., 0.089]
                         ↑ 语义不同，向量也不同
```

**常用 Embedding 模型对比**：

| 模型 | 维度 | 特点 |
|------|------|------|
| OpenAI `text-embedding-3-small` | 1536 | 性价比高，支持缩短维度 |
| OpenAI `text-embedding-3-large` | 3072 | 精度最高 |
| Cohere `embed-multilingual-v3` | 1024 | 多语言效果好 |
| 本地 `all-MiniLM-L6-v2` | 384 | 免费离线，精度一般 |

**向量相似度计算**（检索时的核心操作）：

- **余弦相似度**：只看方向不看长度，最常用
- **欧氏距离**：直线距离
- **点积**：考虑方向和长度

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings();
```

### 4.5 Vector Store（向量数据库）

把海量向量存起来并支持快速检索。

**类型对比**：

| 存储 | 适用阶段 | 特点 |
|------|---------|------|
| `MemoryVectorStore` | 开发/测试 | 内存存储，重启即丢失 |
| `Chroma` | 小型生产 | 轻量开源，可持久化 |
| `Pinecone` | 生产 | 全托管，免运维 |
| `Weaviate` | 生产 | 支持混合搜索 |
| `pgvector` (PostgreSQL) | 混合场景 | 在现有 PG 中加向量能力 |

```typescript
import { MemoryVectorStore } from "langchain/vectorstores/memory";

const vectorStore = await MemoryVectorStore.fromDocuments(splitDocs, embeddings);
```

### 4.6 检索策略：不只是相似度搜索

**基础检索**：

```typescript
const retriever = vectorStore.asRetriever({
  k: 4,  // 返回最相似的 4 个文档
  filter: { source: "handbook-2024" }, // 元数据过滤
});
```

**高级检索策略**：

**1. MMR（最大边际相关性）**：平衡相关性和多样性，避免返回高度重复的文档

```typescript
const retriever = vectorStore.asRetriever({
  searchType: "mmr",
  searchKwargs: { fetchK: 20, lambda: 0.5 },
  // fetchK: 先召回20个候选
  // lambda: 0=最大多样性, 1=最大相关性
});
```

**2. Self-Querying（自查询检索）**：LLM 自动从问题中提取过滤条件

```
用户问："2024年关于加薪的政策"
→ LLM 自动提取：year=2024, topic="加薪"
→ 先用元数据过滤，再做语义搜索
```

**3. Multi-Vector Retrieval（多向量检索）**：每个文档存储多个向量（摘要向量、关键词向量等），提升召回率。

### 4.7 构建 RetrievalQA 链

```typescript
import { RetrievalQAChain } from "langchain/chains";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({ modelName: "gpt-4", temperature: 0 });

const chain = RetrievalQAChain.fromLLM(model, vectorStore.asRetriever());

const response = await chain.call({
  query: "我们公司的请假流程是怎样的？",
});
console.log(response.text);
```

这样，LLM 在回答时会先到向量库中查找相关文本片段，再基于这些内容生成答案——这就是 RAG 的核心理念。**这个链本身就可以作为 Agent 的一个工具**。

---

## 五、Agent 核心机制彻底剖析

### 5.1 Agent 的"思考-行动-观察"循环

Agent 的本质是一个**在循环中做决策的程序**：

```
┌─────────────────────────────────────────┐
│            AgentExecutor 循环             │
│                                          │
│  ① 构建 Prompt（系统指令 + 工具列表       │
│     + 对话历史 + 用户输入）               │
│          ↓                               │
│  ② 调用 LLM，获取响应                    │
│          ↓                               │
│  ③ 解析响应 ─┬─ Final Answer → 结束      │
│              │                            │
│              └─ Tool Call → ④ 执行工具    │
│                              ↓            │
│                    ⑤ 获取 Observation    │
│                              ↓            │
│                    ⑥ 追加到消息历史       │
│                              ↓            │
│                        回到 ①             │
└─────────────────────────────────────────┘
```

这个循环会持续执行，直到 LLM 输出最终答案或达到最大迭代次数。

### 5.2 Agent 的两种核心范式

**范式一：ReAct（Reasoning + Acting）**

基于提示词工程，让 LLM 输出特定格式文本：

```
Thought: 我需要计算1+1
Action: calculator
Action Input: 1+1
Observation: 2
Thought: 我得到了结果，可以回答了
Final Answer: 1+1等于2
```

**范式二：Function Calling（工具调用/函数调用）**

利用模型原生的 API 能力，不靠提示词硬约束：

```json
// LLM 响应中直接包含工具调用的结构化数据
{
  "tool_calls": [
    {
      "function": {
        "name": "calculator",
        "arguments": "{\"expression\": \"1+1\"}"
      }
    }
  ]
}
```

**对比**：

| 维度 | ReAct | Function Calling |
|------|-------|-----------------|
| 可靠性 | 可能格式错误 | 原生支持，极可靠 |
| 模型要求 | 任意模型 | 需支持 function calling |
| 并行调用 | 不支持 | 支持一次调多个工具 |
| 灵活性 | 可完全自定义 | 受模型能力限制 |

### 5.3 Agent 类型详解

LangChain 中常用的 Agent 类型：

| Agent 类型 | 底层机制 | 适用场景 |
|-----------|---------|---------|
| `openai-functions` | Function Calling | GPT-3.5/4，首选 |
| `chat-zero-shot-react-description` | ReAct | 不支持 function calling 的模型 |
| `chat-conversational-react-description` | ReAct + 对话记忆优化 | 多轮对话 |
| `openai-tools` | Tools API（新版） | GPT-4 Turbo 及以上 |
| `structured-chat-zero-shot-react-description` | ReAct + 结构化工具输入 | 需要多参数工具 |

### 5.4 工具设计的黄金法则

工具是 Agent 的手和脚。设计质量直接决定 Agent 的可用性。

**工具定义的三要素**：

```typescript
const tool = new Tool({
  name: "search_customer",        // ① 唯一标识名（LLM 用来选择工具）
  description: `                   // ② 详细描述（LLM 用来判断何时调用）
用于根据客户ID或姓名查询客户信息。
当用户询问某个特定客户的订单、联系方式、地址时使用。
输入格式：客户ID（数字）或客户姓名（字符串）`,
  func: async (input: string) => { // ③ 执行函数
    // ...
    return "格式化的字符串结果";
  }
});
```

**Description 编写原则**（这决定了 LLM 能否正确调用）：

1. **明确触发条件**："当...时使用此工具"
2. **说明输入格式**："输入应为..."
3. **说明返回值**："返回..."
4. **举一个使用示例**（可选但强烈推荐）

**工具的函数返回值格式**：一定要返回**清晰的自然语言字符串**，因为 LLM 需要理解这个结果。不要返回复杂的 JSON 对象（除非通过 StructuredTool 处理）。

### 5.5 工具定义示例

```typescript
import { DynamicTool } from "langchain/tools";

// 定义一个简单的计算工具
const calculatorTool = new DynamicTool({
  name: "calculator",
  description: "用于执行数学计算。输入一个数学表达式，返回计算结果。",
  func: async (input: string) => {
    try {
      return eval(input).toString(); // 生产环境请用安全的 math.js
    } catch (e) {
      return "计算错误";
    }
  },
});

// 把 RAG 检索包装成工具
import { Tool } from "langchain/tools";

const retrieverTool = new Tool({
  name: "knowledge-base",
  description:
    "查询公司内部知识库。当需要了解公司政策、流程、技术文档时使用此工具。输入一个具体问题。",
  func: async (query: string) => {
    const docs = await vectorStore.similaritySearch(query, 2);
    return docs.map((doc) => doc.pageContent).join("\n\n");
  },
});
```

### 5.6 组装 Agent

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { initializeAgentExecutorWithOptions } from "langchain/agents";
import { Calculator } from "langchain/tools/calculator"; // 内置安全计算器
import { BufferMemory } from "langchain/memory";

const model = new ChatOpenAI({
  modelName: "gpt-4",
  temperature: 0,
});

// 工具集
const tools = [new Calculator(), retrieverTool];

// 初始化 Agent 执行器
const executor = await initializeAgentExecutorWithOptions(tools, model, {
  agentType: "chat-zero-shot-react-description", // ReAct 风格
  verbose: true, // 打印思考过程
  memory: new BufferMemory({
    memoryKey: "chat_history",
    returnMessages: true,
  }),
});

// 运行 Agent
const result = await executor.call({
  input: "如果我有3天年假，加上周末，我最长可以连休几天？并告诉我年假申请流程。",
});

console.log("最终回答：", result.output);
```

**控制台会输出类似以下的过程**：

```
> Entering new AgentExecutor chain...
Thought: 我需要计算日期，还要查询年假流程。先算日期吧。
Action:
{
  "action": "calculator",
  "action_input": "3 + 2"
}
Observation: 5
Thought: 现在需要查询年假申请流程。
Action:
{
  "action": "knowledge-base",
  "action_input": "年假申请流程"
}
Observation: 年假需提前3天在OA系统提交，经理审批后生效...
Thought: 我现在知道计算结果是5天，且有申请流程。可以给出最终答案了。
Final Answer: 如果你有3天年假，加上周末最多可以连休5天。申请流程是...
```

---

## 六、Memory（记忆）深度解析

### 6.1 为什么需要记忆？Token 预算困境

LLM 是**无状态**的——每次 API 调用都是独立的。要实现多轮对话，必须把历史消息带回给模型。

但问题来了：上下文窗口有限（128K tokens），对话越来越长后塞不下。

**Token 消耗的演进**：

```
第1轮：system(500) + user(50) + assistant(100) = 650 tokens
第2轮：上面650 + user(50) + assistant(100) = 800 tokens
...
第50轮：可能已经 15000+ tokens，不但贵而且慢
```

### 6.2 记忆策略全景

| 策略 | 原理 | Token 特征 | 适用场景 |
|------|------|-----------|---------|
| **BufferMemory** | 完整存储所有消息 | 线性增长 | 短对话，精确记忆 |
| **BufferWindowMemory** | 只保留最近 K 轮 | 固定上限 | 只需近期上下文 |
| **SummaryMemory** | LLM 自动摘要旧消息 | 摘要占固定 token | 长对话，降低 token |
| **SummaryBufferMemory** | 近期保留原文+远期做摘要 | 平衡精确和长度 | 生产环境首选 |
| **VectorStoreRetrieverMemory** | 所有记忆存向量库，检索相关 | 按需检索 | 超长对话，精准回忆 |

### 6.3 SummaryBufferMemory 示例（生产环境推荐）

```typescript
import { ConversationSummaryBufferMemory } from "langchain/memory";

const memory = new ConversationSummaryBufferMemory({
  llm: model,
  maxTokenLimit: 2000,  // 记忆占用的最大 token 数
  memoryKey: "chat_history",
  returnMessages: true,
});

// 工作原理：
// 1. 总 token 超过 maxTokenLimit 时，自动把最早的几轮对话做摘要
// 2. 保留最近的原始消息 + 早期的摘要
// 3. LLM 看到的是 "摘要... 原始消息... 最新消息"
```

---

## 七、完整的 Agent 项目架构

### 7.1 标准项目分层

```
agent-project/
├── src/
│   ├── agents/          # Agent 定义与配置
│   │   └── customer-service.agent.ts
│   ├── tools/           # 自定义工具
│   │   ├── calculator.tool.ts
│   │   ├── database.tool.ts
│   │   └── knowledge-base.tool.ts
│   ├── prompts/         # 提示词模板
│   │   └── system.prompt.ts
│   ├── memory/          # 记忆配置
│   │   └── chat.memory.ts
│   ├── rag/             # RAG 管道
│   │   ├── loaders/
│   │   ├── splitters/
│   │   ├── embeddings/
│   │   └── vector-store/
│   ├── chains/          # 复合链
│   └── index.ts         # 入口
├── knowledge-base/      # 知识库源文件
└── data/                # 持久化数据（如 Chroma 本地存储）
```

### 7.2 完整示例：带数据库、RAG、计算的客服 Agent

**工具一：知识库工具**

```typescript
// src/tools/knowledge-base.tool.ts
import { Tool } from "langchain/tools";
import { MemoryVectorStore } from "langchain/vectorstores/memory";

export function createKnowledgeBaseTool(vectorStore: MemoryVectorStore): Tool {
  return new Tool({
    name: "knowledge_base",
    description: `
查询公司内部知识库。当用户询问以下内容时使用：
- 公司政策、流程、规章制度
- 产品使用说明、技术文档
- 常见问题解答

输入：一个具体的问题字符串
输出：相关的文档片段，如果未找到则返回"未找到相关信息"`,
    func: async (query: string) => {
      const docs = await vectorStore.similaritySearch(query, 3);
      if (docs.length === 0) return "未找到相关信息";
      return docs.map((d, i) => `[参考${i+1}] ${d.pageContent}`).join("\n\n");
    },
  });
}
```

**工具二：数据库工具**

```typescript
// src/tools/database.tool.ts
import { Tool } from "langchain/tools";

export function createDatabaseTool(): Tool {
  return new Tool({
    name: "query_orders",
    description: `
查询用户的订单信息。当用户询问订单状态、订单详情、历史订单时使用。
输入：用户ID（数字）
输出：该用户的订单列表，包含订单号、状态、金额、时间`,
    func: async (userId: string) => {
      // 实际项目中连接真实数据库
      const mockOrders = [
        { id: "ORD-001", status: "已发货", amount: 299, time: "2024-01-15" },
        { id: "ORD-002", status: "处理中", amount: 599, time: "2024-01-20" },
      ];
      return JSON.stringify(mockOrders);
    },
  });
}
```

**系统提示词**

```typescript
// src/prompts/system.prompt.ts
export const SYSTEM_PROMPT = `你是一个专业的客服助手，名叫"小智"。你的职责是帮助用户解答问题。

行为准则：
1. 先用知识库工具查询公司政策，再回答
2. 涉及订单时，必须使用 query_orders 工具查询真实数据
3. 遇到数学计算，使用 calculator 工具
4. 回答要简洁、准确、友好
5. 如果知识库中没有相关信息，诚实告知并建议联系人工客服

当前时间：{current_time}`;
```

**主入口**

```typescript
// src/index.ts
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { initializeAgentExecutorWithOptions } from "langchain/agents";
import { Calculator } from "langchain/tools/calculator";
import { BufferMemory } from "langchain/memory";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { TextLoader } from "langchain/document_loaders/fs/text";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
import { createKnowledgeBaseTool } from "./tools/knowledge-base.tool";
import { createDatabaseTool } from "./tools/database.tool";
import { SYSTEM_PROMPT } from "./prompts/system.prompt";

async function bootstrap() {
  // 1. 初始化模型
  const model = new ChatOpenAI({
    modelName: "gpt-4",
    temperature: 0.3,
  });

  // 2. 构建 RAG
  const loader = new TextLoader("./knowledge-base/faq.txt");
  const docs = await loader.load();
  const splitter = new RecursiveCharacterTextSplitter({
    chunkSize: 500,
    chunkOverlap: 50,
  });
  const splitDocs = await splitter.splitDocuments(docs);
  const embeddings = new OpenAIEmbeddings();
  const vectorStore = await MemoryVectorStore.fromDocuments(splitDocs, embeddings);

  // 3. 组装工具
  const tools = [
    new Calculator(),
    createKnowledgeBaseTool(vectorStore),
    createDatabaseTool(),
  ];

  // 4. 创建记忆
  const memory = new BufferMemory({
    memoryKey: "chat_history",
    returnMessages: true,
  });

  // 5. 初始化 Agent
  const executor = await initializeAgentExecutorWithOptions(tools, model, {
    agentType: "openai-functions", // 优先用 function calling
    verbose: true,
    memory,
    maxIterations: 5,
    agentArgs: {
      prefix: SYSTEM_PROMPT,
    },
  });

  // 6. 运行
  const res = await executor.call({
    input: "我上周买的订单发货了吗？顺便帮我算一下如果满300减50，我的订单599能省多少？",
  });
  console.log("Answer:", res.output);
}

bootstrap().catch(console.error);
```

### 7.3 Agent 标准开发流程总结

一个生产级 Agent 的开发流程通常遵循以下步骤：

1. **需求分析与任务拆解**
   - 明确 Agent 要解决的业务问题
   - 列出完成该问题所需的外部工具/数据源（计算、搜索、数据库、RAG 等）

2. **工具开发与注册**
   - 每个工具都必须有清晰的 `name` 和 `description`（这直接影响 LLM 能否正确调用）
   - 编写具体的执行函数，返回字符串结果

3. **选择/设计 Agent 类型与提示词**
   - 使用 LangChain 内置 Agent（如 `chat-zero-shot-react-description`）或自定义 Agent
   - 若内置提示词不满足需求，可以编写自定义 Prompt 模板，注入角色、限制规则等

4. **配置记忆系统**
   - 选择合适的记忆类型（Buffer、Summary、Vector等）
   - 注意记忆的 token 管理

5. **组装并测试 AgentExecutor**
   - `AgentExecutor` 是核心运行器，它管理循环、错误处理和最终返回
   - 开启 `verbose: true` 调试，观察每一步的推理

6. **集成 RAG 作为动态知识工具**
   - 构建检索管道（加载→切分→向量化→存储→检索器）
   - 包装成 Tool，供 Agent 调用

7. **添加安全护栏与流控**
   - 设置最大迭代次数 `maxIterations`
   - 过滤危险工具输入（如 eval 风险）
   - 添加人工确认步骤（`human-in-the-loop`）

8. **部署与监控**
   - 通过 LangServe 或自建 API 暴露
   - 记录 Agent 决策轨迹，用于分析优化

---

## 八、生产环境注意事项

### 8.1 错误处理与重试

```typescript
const executor = await initializeAgentExecutorWithOptions(tools, model, {
  maxIterations: 5,           // 防止无限循环
  earlyStoppingMethod: "generate", // 达到最大迭代时强制生成答案
  handleParsingErrors: true,  // 处理格式解析错误
  returnIntermediateSteps: true, // 返回中间步骤用于调试
});
```

### 8.2 成本控制

- 用 `gpt-3.5-turbo` 做简单任务的 Agent
- 对 RAG 检索结果做排序/过滤，减少注入的 token
- 使用 `ConversationSummaryBufferMemory` 控制记忆 token
- 监控每次调用的 token 消耗

### 8.3 安全防护

- **永远不要**在生产环境使用 `eval()` 做计算
- 对数据库工具做 SQL 注入防护
- 对 API 调用工具做参数校验和白名单
- 考虑加入人工确认步骤（Human-in-the-Loop）

### 8.4 拓展方向

- **Plan-and-Execute Agent**：先制定完整计划，再逐步执行。LangChain 提供了 `PlanAndExecuteAgentExecutor`，适合复杂多步任务。
- **多 Agent 协作**：用 `AutoGPT`、`BabyAGI` 或 LangGraph 构建状态图，让多个 Agent 分工合作。

> 建议先把标准 ReAct Agent + RAG 的流程吃透，这是绝大部分生产场景的基础。

---

## 附录：关键概念速查表

| 概念 | 一句话解释 |
|------|----------|
| **Token** | LLM 处理的最小文本单元，不是单词而是更细粒度的语言片段 |
| **Context Window** | 模型一次能"看到"的 Token 上限 |
| **Embedding** | 将文本转换为向量，语义相似的文本向量距离近 |
| **RAG** | 检索增强生成，先检索外部知识再让 LLM 基于参考资料回答 |
| **ReAct** | Reasoning + Acting，让 LLM 交替输出思考和行动 |
| **Function Calling** | 模型原生支持的工具调用能力，比 ReAct 更可靠 |
| **AgentExecutor** | Agent 的运行引擎，管理思考-行动-观察循环 |
| **chunkOverlap** | 文本分割时相邻块的字符重叠量，保证语义连贯 |
| **MMR** | 最大边际相关性检索，平衡结果的相关性和多样性 |
| **SummaryBufferMemory** | 近期保留原文+远期做摘要的记忆策略，生产首选 |

---

> 本文档基于 TypeScript + LangChain 技术栈，涵盖了从 LLM 底层原理到 Agent 生产部署的完整知识链路。建议按 **LLM 本质 → Prompt → RAG 管道 → Agent 循环 → 记忆管理 → 工程化** 的顺序逐步消化。
