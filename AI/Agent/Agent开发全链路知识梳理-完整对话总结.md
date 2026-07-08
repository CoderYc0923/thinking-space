# Agent 标准开发流程 —— 完整对话知识梳理

> 本文档系统整理了 Agent 标准开发流程的全部知识点，涵盖 LLM 底层原理、LangChain 架构、Prompt Engineering、RAG 全链路、Agent 核心机制、Memory 记忆管理、RAG vs Memory 区别、以及生产环境注意事项。基于 TypeScript 技术栈。

---

## 目录

- [一、LLM 的本质与局限](#一llm-的本质与局限)
- [二、LangChain 架构深度拆解](#二langchain-架构深度拆解)
- [三、Prompt Engineering 核心概念](#三prompt-engineering-核心概念)
- [四、RAG 全链路原理深度拆解](#四rag-全链路原理深度拆解)
- [五、Agent 核心机制彻底剖析](#五agent-核心机制彻底剖析)
- [六、Memory（记忆）深度解析](#六memory记忆深度解析)
- [七、RAG 和 Memory 的区别](#七rag-和-memory-的区别)
- [八、LangChain 整个工作原理流程（通俗版）](#八langchain-整个工作原理流程通俗版)
- [九、Agent 开发需要注意的点](#九agent-开发需要注意的点)
- [十、完整代码示例](#十完整代码示例)
- [十一、Vector Store 选型](#十一vector-store-选型)
- [十二、生产环境注意事项](#十二生产环境注意事项)
- [附录：关键概念速查表](#附录关键概念速查表)

---

## 一、LLM 的本质与局限

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
| **无规划能力** | 只能一次生成，无法分解复杂任务 | **Agent ReAct 循环**：思考→行动→观察 |

---

## 二、LangChain 架构深度拆解

### 2.1 LangChain 是什么？

**一句话定义**：LangChain 是一个**将 LLM 与外部世界（数据、工具、记忆）连接的编排框架**。

**LangChain 帮你做的事**：

- 自动管理消息拼接和状态流转
- 统一封装各种 LLM 的调用接口
- 提供标准化的工具定义和调用协议
- 内置多种记忆管理策略
- 处理错误重试、输出解析等边界情况

### 2.2 核心模块总览

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

`tsconfig.json`：

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

---

## 三、Prompt Engineering 核心概念

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
```

### 3.2 三种常用 Prompt 类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `PromptTemplate` | 纯文本模板 | 简单问答 |
| `ChatPromptTemplate` | 结构化消息列表 | 多轮对话，区分 system/user/assistant |
| `MessagesPlaceholder` | 占位符（注入历史消息） | Agent 的记忆注入点 |

---

## 四、RAG 全链路原理深度拆解

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

支持的加载器：`TextLoader`、`PDFLoader`、`CSVLoader`、`JSONLoader`、`DirectoryLoader`、`CheerioWebBaseLoader` 等。

```typescript
import { TextLoader } from "langchain/document_loaders/fs/text";

const loader = new TextLoader("./knowledge-base.txt");
const docs = await loader.load();
```

### 4.3 Text Splitter（文本分割器）

**分割的核心矛盾**：太小丢失上下文，太大检索不准。

| 分割器 | 原理 | 适用场景 |
|--------|------|---------|
| `RecursiveCharacterTextSplitter` | 按 `\n\n→\n→空格→字符` 优先级递归切分 | **通用首选** |
| `MarkdownTextSplitter` | 保持标题和段落的层次结构 | Markdown 文档 |
| `TokenTextSplitter` | 按 Token 数量精确控制 | 需严格控制 token 预算 |
| `CodeTextSplitter` | 按代码语义（函数/类边界）切分 | 代码库 |

```typescript
const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,    // 每块最多 500 字符
  chunkOverlap: 50,  // 相邻块重叠 50 字符（保证语义连贯）
});
```

### 4.4 Embeddings（嵌入）

**本质**：把文本映射到向量空间，语义相似的文本向量距离更近。

**常用模型**：

| 模型 | 维度 | 特点 |
|------|------|------|
| OpenAI `text-embedding-3-small` | 1536 | 性价比高 |
| OpenAI `text-embedding-3-large` | 3072 | 精度最高 |
| 本地 `all-MiniLM-L6-v2` | 384 | 免费离线 |

### 4.5 Vector Store（向量数据库）

| 存储 | 适用阶段 | 特点 |
|------|---------|------|
| `MemoryVectorStore` | 开发/测试 | 内存存储，重启丢失 |
| `Chroma` | 小型生产 | **免费开源**，可 Docker 部署 |
| `Pinecone` | 生产 | 全托管，商业收费 |
| `pgvector` (PostgreSQL) | 混合场景 | 在现有 PG 中加向量能力 |

### 4.6 检索策略

**基础检索**：
```typescript
const retriever = vectorStore.asRetriever({ k: 4 });
```

**MMR（最大边际相关性）**：平衡相关性和多样性
```typescript
const retriever = vectorStore.asRetriever({
  searchType: "mmr",
  searchKwargs: { fetchK: 20, lambda: 0.5 },
});
```

---

## 五、Agent 核心机制彻底剖析

### 5.1 Agent 的"思考-行动-观察"循环

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

### 5.2 Agent 的两种核心范式

| 维度 | ReAct | Function Calling |
|------|-------|-----------------|
| 可靠性 | 可能格式错误 | 原生支持，极可靠 |
| 模型要求 | 任意模型 | 需支持 function calling |
| 并行调用 | 不支持 | 支持一次调多个工具 |
| 灵活性 | 可完全自定义 | 受模型能力限制 |

### 5.3 工具设计的黄金法则

**Description 编写原则**（决定 LLM 能否正确调用）：

1. **明确触发条件**："当...时使用此工具"
2. **说明输入格式**："输入应为..."
3. **说明返回值**："返回..."
4. **举一个使用示例**（强烈推荐）

**❌ 糟糕的描述**：
```typescript
{ name: "tool_1", description: "查询数据" }
```

**✅ 好的描述**：
```typescript
{
  name: "search_orders",
  description: `查询用户的订单信息。
  当用户询问"我的订单"、"订单状态"、"物流到哪里了"时使用此工具。
  输入：用户ID（纯数字）
  返回：订单列表，包含订单号、状态、金额、物流信息`,
}
```

---

## 六、Memory（记忆）深度解析

### 6.1 Token 预算困境

LLM 是无状态的，每次 API 调用都独立。对话越来越长后：

- 第1轮：~650 tokens
- 第10轮：~5000+ tokens
- 第50轮：~15000+ tokens（又贵又慢）

### 6.2 记忆策略全景

| 策略 | 原理 | Token 特征 | 适用场景 |
|------|------|-----------|---------|
| **BufferMemory** | 完整存储所有消息 | 线性增长 | 短对话 |
| **BufferWindowMemory** | 只保留最近 K 轮 | 固定上限 | 只需近期上下文 |
| **SummaryMemory** | LLM 自动摘要旧消息 | 摘要占固定 token | 长对话 |
| **SummaryBufferMemory** | 近期保留原文+远期做摘要 | 平衡精确和长度 | **生产首选** |
| **VectorStoreRetrieverMemory** | 所有记忆存向量库 | 按需检索 | 超长对话 |

---

## 七、RAG 和 Memory 的区别

这是最容易混淆的两个概念，用生活场景类比：

### RAG（检索增强生成）= 你去图书馆查资料

- **场景**：客户问你"公司年假政策是什么？"
- 你起身去**档案室**（Vector Store），翻出《员工手册》
- 把原文复印下来，对着这张纸回答客户
- **本质**：**知识来源**，解决"我不知道，让我查一下"

### Memory（记忆）= 你随身带的小本本

- **场景**：客户说"我叫张三，工号9527"
- 你**拿小本本记下来**
- 第5轮对话时你说"张三，你的订单查到了"
- **本质**：**对话状态**，解决"我之前说了什么"

### 一张表看懂区别

| 维度 | RAG（检索增强生成） | Memory（记忆） |
|------|-------------------|---------------|
| **类比** | 去图书馆查书 | 随身笔记本 |
| **存什么** | 外部知识（文档、手册、百科） | 对话历史（用户说了啥） |
| **目的** | 弥补 LLM 知识盲区，防止幻觉 | 维持多轮对话上下文 |
| **数据来源** | PDF、网页、数据库等离线文档 | 用户实时输入 + 助手回复 |
| **存储方式** | 向量数据库（Chroma/Pinecone） | 消息列表或摘要 |
| **查询方式** | 语义相似度搜索 | 按时间顺序取回 |
| **生命周期** | 长期固定，很少变 | 短期，随对话结束可清空 |
| **在 Agent 中** | 作为一个**工具**被调用 | 自动注入到每次 LLM 调用 |

### 如何配合？

1. 客户说"我上个月买的订单到哪了？" → **Memory** 知道这个客户叫张三
2. LLM 决定去查订单数据库 → **工具调用**
3. 客户问"退货政策是什么？" → LLM 调用 **RAG 工具**去知识库检索
4. 客户说"帮我退了吧" → **Memory** 知道前面讨论的是订单 ORD-001，**RAG** 提供了退货流程

---

## 八、LangChain 整个工作原理流程（通俗版）

用**"智能餐厅后厨"**的故事来理解：

### 角色设定

| LangChain 组件 | 餐厅角色 | 职责 |
|:---|:---|:---|
| **LLM** | 主厨大脑 | 决策和生成回答 |
| **Prompt Template** | 点菜单 | 标准化指令格式 |
| **Tools** | 厨具/设备 | 计算器、搜索引擎、数据库 |
| **Agent** | 主厨本人 | 结合大脑和工具完成任务 |
| **AgentExecutor** | 厨房调度员 | 管理整个做菜流程 |
| **Memory** | 便签纸 | 记住客人之前说了什么 |
| **Vector Store** | 菜谱档案室 | 存放所有菜谱供查阅 |
| **RAG** | 去档案室查菜谱的助手 | 检索知识 |

### 完整流程

```
用户输入
    ↓
┌──────────────────────────────────┐
│  AgentExecutor（调度员）          │
│                                  │
│  组装 Prompt =                    │
│    系统指令 + 工具列表 +          │
│    对话历史(Memory) + 用户输入    │
│         ↓                        │
│  调用 LLM（主厨思考）             │
│         ↓                        │
│  LLM 返回什么？                  │
│  ├─ Final Answer → 返回给用户    │
│  └─ Tool Call → 执行工具          │
│         ↓                        │
│  把工具结果喂回 LLM               │
│         ↓                        │
│  更新 Memory（记便签）            │
│         ↓                        │
│  回到"调用 LLM"步骤继续循环       │
└──────────────────────────────────┘
```

**一句话总结**：
> LangChain 就是一个聪明的调度系统：它把你的问题、历史记录、可用工具一起交给 LLM，LLM 决定"要不要用工具 → 用哪个工具 → 拿到结果后怎么回答"，循环这个流程直到能给出最终答案。

---

## 九、Agent 开发需要注意的点

### 1. 工具描述是命脉

LLM 只能根据 `name` 和 `description` 来决定何时调用工具。写清楚**何时用、输入什么、输出什么**。

### 2. 防止死循环

```typescript
const executor = await initializeAgentExecutorWithOptions(tools, model, {
  maxIterations: 5,           // 最多执行5轮，强制停止
  earlyStoppingMethod: "generate", // 超时后强制生成答案
});
```

### 3. 工具返回值必须"说人话"

**❌ 不好**：`{"code":200,"data":[{"oid":"001","st":3,"amt":299}]}`

**✅ 好的**：`用户张三有2个订单：订单号 ORD-001，状态：已发货，金额：299元`

### 4. 用"角色+规则"约束行为

```typescript
const SYSTEM_PROMPT = `
你是一个客服助手。必须遵守以下规则：
1. 涉及订单查询时，必须使用 search_orders 工具，不能编造
2. 涉及公司政策时，必须使用 knowledge_base 工具查询
3. 如果工具返回"未找到"，诚实告诉用户，不要猜测
`;
```

### 5. 记忆管理要精打细算

| 策略 | 适用场景 |
|------|---------|
| `BufferMemory` | 短对话（<10轮），记得最准 |
| `BufferWindowMemory` | 只需要最近几轮上下文 |
| `SummaryBufferMemory` | **生产首选**：老消息自动摘要 |

### 6. 安全三原则

- **不要用 `eval()` 做计算** → 用 `math.js` 或 LLM 自带计算
- **数据库查询要防注入** → 参数化查询
- **敏感工具加人工确认** → 删除、付款等操作要用户二次确认

---

## 十、完整代码示例

### 项目结构

```
agent-project/
├── src/
│   ├── agents/
│   ├── tools/
│   │   ├── knowledge-base.tool.ts
│   │   └── database.tool.ts
│   ├── prompts/
│   │   └── system.prompt.ts
│   ├── memory/
│   ├── rag/
│   └── index.ts
├── knowledge-base/
└── data/
```

### 知识库工具

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
输出：相关的文档片段`,
    func: async (query: string) => {
      const docs = await vectorStore.similaritySearch(query, 3);
      if (docs.length === 0) return "未找到相关信息";
      return docs.map((d, i) => `[参考${i+1}] ${d.pageContent}`).join("\n\n");
    },
  });
}
```

### 系统提示词

```typescript
// src/prompts/system.prompt.ts
export const SYSTEM_PROMPT = `你是一个专业的客服助手，名叫"小智"。

行为准则：
1. 先用知识库工具查询公司政策，再回答
2. 涉及订单时，必须使用 query_orders 工具查询真实数据
3. 遇到数学计算，使用 calculator 工具
4. 回答要简洁、准确、友好
5. 如果知识库中没有相关信息，诚实告知并建议联系人工客服`;
```

### 主入口

```typescript
// src/index.ts
import "dotenv/config";
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
    agentType: "openai-functions",
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

---

## 十一、Vector Store 选型

### Chroma —— 免费开源首选

**Chroma 完全免费**，Apache 2.0 开源协议。

**Docker 部署**：

```bash
docker run -d \
  --name chroma \
  -p 8000:8000 \
  -v chroma-data:/chroma/chroma \
  chromadb/chroma
```

**TypeScript 连接**：

```typescript
import { ChromaClient } from "chromadb";

const client = new ChromaClient({ path: "http://你的服务器IP:8000" });
```

**注意**：Chroma 官方推出了云服务（Chroma Cloud），免费起步+按用量付费。但核心引擎永远开源免费，你可以选择在自己的 Docker 或服务器上免费运行。

---

## 十二、生产环境注意事项

### 成本控制

- 用 `gpt-3.5-turbo` 做简单任务的 Agent
- 对 RAG 检索结果做排序/过滤，减少注入的 token
- 使用 `ConversationSummaryBufferMemory` 控制记忆 token
- 监控每次调用的 token 消耗

### 安全防护

- **永远不要**在生产环境使用 `eval()` 做计算
- 对数据库工具做 SQL 注入防护
- 对 API 调用工具做参数校验和白名单
- 考虑加入人工确认步骤（Human-in-the-Loop）

### Agent 开发流程总结

1. **需求分析与任务拆解**：明确业务问题，列出所需工具
2. **工具开发与注册**：每个工具有清晰的 name 和 description
3. **选择/设计 Agent 类型与提示词**：注入角色、限制规则
4. **配置记忆系统**：选择合适的记忆类型
5. **组装并测试 AgentExecutor**：开启 verbose 调试
6. **集成 RAG 作为动态知识工具**：加载→切分→向量化→存储→检索
7. **添加安全护栏与流控**：maxIterations、参数校验
8. **部署与监控**：记录 Agent 决策轨迹

---

## 附录：关键概念速查表

| 概念 | 一句话解释 |
|------|----------|
| **Token** | LLM 处理的最小文本单元 |
| **Context Window** | 模型一次能"看到"的 Token 上限 |
| **Embedding** | 将文本转换为向量，语义相似的文本向量距离近 |
| **RAG** | 检索增强生成，先检索外部知识再让 LLM 基于参考资料回答 |
| **ReAct** | Reasoning + Acting，让 LLM 交替输出思考和行动 |
| **Function Calling** | 模型原生支持的工具调用能力，比 ReAct 更可靠 |
| **AgentExecutor** | Agent 的运行引擎，管理思考-行动-观察循环 |
| **chunkOverlap** | 文本分割时相邻块的字符重叠量，保证语义连贯 |
| **MMR** | 最大边际相关性检索，平衡结果的相关性和多样性 |
| **SummaryBufferMemory** | 近期保留原文+远期做摘要的记忆策略，生产首选 |
| **Memory** | 记忆对话历史（"我之前说了什么"） |
| **RAG vs Memory** | RAG 是查外部知识库（"我不知道，让我查"），Memory 是记对话历史（"我之前说了什么"） |
| **Chroma** | 免费开源的向量数据库，Apache 2.0 协议，支持 Docker 自部署 |

---

> 本文档基于 TypeScript + LangChain 技术栈，涵盖了从 LLM 底层原理到 Agent 生产部署的完整知识链路。
> 建议学习路径：**LLM 本质 → Prompt → RAG 管道 → Agent 循环 → Memory 管理 → 工程化部署**
