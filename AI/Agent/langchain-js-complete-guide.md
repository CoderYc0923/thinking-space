# LangChain.js 完全指南 — 从原理到实战（TypeScript / Node.js）

> 适合有 Node.js 后端经验、正在系统学习 Agent 开发的工程师。  
> 本文用最简单的类比讲清抽象概念，再配合可运行的 TypeScript 代码示例。

---

## 目录

1. [一句话理解 LangChain](#1-一句话理解-langchain)
2. [核心痛点：为什么需要 LangChain？](#2-核心痛点为什么需要-langchain)
3. [整体架构：一张图看懂](#3-整体架构一张图看懂)
4. [核心概念逐个击破](#4-核心概念逐个击破)
   - [4.1 Model（模型）—— 大脑](#41-model模型大脑)
   - [4.2 Prompt Template（提示模板）—— 说话的格式](#42-prompt-template提示模板说话的格式)
   - [4.3 Chain（链）—— 流水线](#43-chain链流水线)
   - [4.4 Document Loader（文档加载器）—— 数据入口](#44-document-loader文档加载器数据入口)
   - [4.5 Text Splitter（文本分割器）—— 切成小块](#45-text-splitter文本分割器切成小块)
   - [4.6 Embeddings（向量嵌入）—— 文字 → 坐标](#46-embeddings向量嵌入文字--坐标)
   - [4.7 Vector Store（向量数据库）—— 相似性搜索引擎](#47-vector-store向量数据库相似性搜索引擎)
   - [4.8 Retriever（检索器）—— 查询接口](#48-retriever检索器查询接口)
   - [4.9 Memory（记忆）—— 上下文管理](#49-memory记忆上下文管理)
   - [4.10 Tool（工具）—— 外部能力](#410-tool工具外部能力)
   - [4.11 Agent（智能体）—— 自动决策者](#411-agent智能体自动决策者)
5. [RAG 全景流程](#5-rag-全景流程)
6. [从 Chain 到 Agent 的进化](#6-从-chain-到-agent-的进化)
7. [实际项目结构建议](#7-实际项目结构建议)
8. [常见坑与最佳实践](#8-常见坑与最佳实践)

---

## 1. 一句话理解 LangChain

> **LangChain 就是一个「让 LLM 能够访问外部世界」的中间件框架。**

把大语言模型（LLM）想象成一个**超级聪明但被关在房间里的人**：

- 他知道很多知识（训练数据），但不知道今天发生了什么（没有实时信息）
- 他不能操作电脑（不能调用 API）
- 他记不住你上一句话说了什么（无状态）
- 他不能读你的私有文档（没有外部数据源）

LangChain 做的事情就是：**给这个聪明人装上电话、电脑、笔记本和文件柜**，让他能干实事。

---

## 2. 核心痛点：为什么需要 LangChain？

没有 LangChain 时，你调用 OpenAI API 大概是这样的：

```typescript
// 原生调用 — 只能一问一答，什么高级功能都要自己写
const response = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "今天天气怎么样？" }],
});
```

**问题来了：**

| 需求 | 原生 API 的困境 | LangChain 的解法 |
|------|----------------|-----------------|
| 让模型读你公司的 PDF 文档 | 要自己写 PDF 解析、文本分割、拼接 prompt | Document Loader + Retriever |
| 让模型记住多轮对话 | 要自己管理 messages 数组 | Memory 模块 |
| 让模型自动选择调用哪个 API | 要自己写 if-else 路由逻辑 | Agent + Tool |
| 组合多个 LLM 调用步骤 | 要自己写回调地狱 | Chain（链式调用） |
| 换一个模型供应商 | 要改写所有调用代码 | 统一接口，改一行配置 |

**LangChain 本质上就是把这些常见模式抽象成了标准模块。**

---

## 3. 整体架构：一张图看懂

```
┌──────────────────────────────────────────────────────────┐
│                      LangChain                          │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌───────────┐  │
│  │  Model  │  │  Prompt  │  │ Chain  │  │  Memory   │  │
│  │  模型   │  │  模板     │  │  链    │  │  记忆     │  │
│  └─────────┘  └──────────┘  └────────┘  └───────────┘  │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌───────────┐  │
│  │ Loader  │  │ Splitter │  │ Vector │  │ Retriever │  │
│  │ 加载器  │  │ 分割器   │  │ Store  │  │  检索器   │  │
│  └─────────┘  └──────────┘  └────────┘  └───────────┘  │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────────┐  │
│  │  Tool   │  │  Agent   │  │    Callback / Tracer   │  │
│  │  工具   │  │  智能体  │  │    回调 / 追踪         │  │
│  └─────────┘  └──────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**学习路线：** 按上面从左到右、从上到下的顺序学，每个模块解决一个问题。

---

## 4. 核心概念逐个击破

### 4.1 Model（模型）—— 大脑

**是什么：** 对各大 LLM 供应商的统一封装。

```bash
npm install @langchain/openai @langchain/anthropic @langchain/core
```

```typescript
import { ChatOpenAI } from "@langchain/openai";

// 就这么简单，换模型只改这里
const model = new ChatOpenAI({
  model: "gpt-4o",           // 模型名
  temperature: 0.7,           // 创造性 (0=严谨, 1=天马行空)
  maxTokens: 2048,            // 最大输出长度
  apiKey: process.env.OPENAI_API_KEY,
});

// 调用
const result = await model.invoke("用一句话解释什么是闭包");
console.log(result.content);
```

**关键理解：** LangChain 把 OpenAI、Anthropic、本地模型等的调用接口全部统一了。你换模型只需改 import 和配置，业务代码完全不用动。

---

### 4.2 Prompt Template（提示模板）—— 说话的格式

**是什么：** 把动态变量插入到预设的提示词模板中。

**为什么需要：** 你肯定不会在代码里拼接字符串 `"翻译成" + language + "：" + text`，太丑了。

```typescript
import { ChatPromptTemplate } from "@langchain/core/prompts";

const prompt = ChatPromptTemplate.fromTemplate(
  "你是一个{role}。请用{style}的风格回答：{question}"
);

// 填充变量 → 生成最终发给模型的完整消息
const formatted = await prompt.format({
  role: "前端技术专家",
  style: "通俗易懂",
  question: "React 的 useEffect 怎么用？",
});

console.log(formatted);
// "你是一个前端技术专家。请用通俗易懂的风格回答：React 的 useEffect 怎么用？"
```

**更复杂的模板（带消息角色）：**

```typescript
const chatPrompt = ChatPromptTemplate.fromMessages([
  ["system", "你是一个{role}，回答风格：{style}"],
  ["user", "{question}"],
]);
```

---

### 4.3 Chain（链）—— 流水线

**是什么：** 把多个步骤串联起来，前一步的输出变成后一步的输入。

**最简单的类比：工厂流水线。**

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { RunnableSequence } from "@langchain/core/runnables";

// 第一步：设定 prompt 模板
const prompt = ChatPromptTemplate.fromTemplate(
  "把以下内容翻译成{targetLanguage}：\n\n{input}"
);

// 第二步：指定模型
const model = new ChatOpenAI({ model: "gpt-4o" });

// 串联成链！
const chain = prompt.pipe(model);  // ← 这就是一个最简单的 Chain

// 运行
const result = await chain.invoke({
  targetLanguage: "日语",
  input: "你好，今天天气真好。",
});

console.log(result.content);
// "こんにちは、今日はいい天気ですね。"
```

**`.pipe()` 是 LangChain 最重要的方法**，它把两个 Runnable 串起来。你可以无限串联：

```typescript
const chain = prompt
  .pipe(model)          // 第1步：用模板 + 模型生成回答
  .pipe(outputParser);  // 第2步：把模型输出解析成 JSON
```

**Chain 的三种复杂度：**

| 类型 | 说明 | 场景 |
|------|------|------|
| 简单链 A → B | 一个输入一个输出，线性 | 翻译、摘要 |
| 并行链 A → (B + C) → D | 同时跑多个分支，汇总结果 | 多角度分析同一段文本 |
| 条件链 A → B 或 C | 根据条件走不同分支 | 问题分类路由 |

---

### 4.4 Document Loader（文档加载器）—— 数据入口

**是什么：** 从各种来源加载文档内容。

**支持格式：** PDF、TXT、CSV、JSON、Markdown、网页、Notion、GitHub……

```typescript
import { TextLoader } from "langchain/document_loaders/fs/text";
import { PDFLoader } from "@langchain/community/document_loaders/fs/pdf";
import { CSVLoader } from "@langchain/community/document_loaders/fs/csv";

// 加载本地文件
const loader = new TextLoader("./docs/readme.txt");
const docs = await loader.load();

// docs 是一个 Document[] 数组
// 每个 Document = { pageContent: string, metadata: { source: string, ... } }
console.log(docs[0].pageContent);   // 文件内容
console.log(docs[0].metadata.source); // 文件路径
```

---

### 4.5 Text Splitter（文本分割器）—— 切成小块

**是什么：** 把长文档按语义切成小段，每段是一个独立的检索单元。

**为什么需要：**
1. LLM 有上下文窗口限制（比如 128K token）
2. 小块检索更精准（整本书扔进去，模型找不到具体段落）
3. 小块向量嵌入更有语义代表性

```typescript
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,      // 每块最多500个字符
  chunkOverlap: 50,    // 相邻块之间重叠50个字符（保持上下文连贯）
});

const chunks = await splitter.splitDocuments(docs);
console.log(`切成了 ${chunks.length} 个块`);
```

**chunkOverlap 很重要：** 如果一段话正好被切在中间，前半句在 A 块、后半句在 B 块，检索时就可能丢信息。overlap 让相邻块有交集。

---

### 4.6 Embeddings（向量嵌入）—— 文字 → 坐标

**这是整个 RAG 最核心的概念，也是最容易被误解的。**

**类比：** 把每句话想象成地图上的一个点。意思相近的句子，坐标就靠近。

```
"苹果是一种水果"          →  [0.1, 0.8, -0.3, ...]  (一个768维的向量)
"香蕉也是一种水果"        →  [0.12, 0.79, -0.28, ...] (和上面的向量很接近！)
"今天天气真好"            →  [-0.5, 0.1, 0.7, ...]   (和上面的向量很远)
```

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-small",  // 性价比最高的嵌入模型
});

// 把一段文字变成向量
const vector = await embeddings.embedQuery("苹果是一种水果");
console.log(vector.length);  // 1536（维度）
console.log(vector.slice(0, 5));  // [0.012, -0.023, 0.034, ...]
```

**为什么需要 Embeddings：** 数据库只能做精确匹配（`WHERE keyword = 'xxx'`），但用户问的是「有没有能提神的饮料？」，文档里写的是「咖啡含有咖啡因，可以让人保持清醒」——这两个表达字面上完全不同，但语义上高度相关。**向量相似度能发现这种关联。**

---

### 4.7 Vector Store（向量数据库）—— 相似性搜索引擎

**是什么：** 专门存储和搜索向量（坐标）的数据库。

**怎么工作：**
1. 把每个文档块用 Embeddings 变成向量
2. 存到向量数据库
3. 用户提问时，也把问题变成向量
4. 找到向量距离最近的 K 个文档块（这就是「语义相似」的数学含义）

```typescript
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { OpenAIEmbeddings } from "@langchain/openai";

// 1. 准备嵌入模型
const embeddings = new OpenAIEmbeddings();

// 2. 创建向量存储（内存版，仅用于学习）
const vectorStore = new MemoryVectorStore(embeddings);

// 3. 把文档块存进去（内部会自动调用 embeddings.embedDocuments）
await vectorStore.addDocuments(chunks);

// 4. 语义搜索！
const results = await vectorStore.similaritySearch("如何优化性能？", 4);
// 返回语义上最相似的4个文档块

results.forEach((doc, i) => {
  console.log(`结果${i + 1}: ${doc.pageContent.slice(0, 100)}...`);
});
```

**生产环境推荐：** 用 Pinecone、Weaviate、Qdrant 或 Chroma 替代 MemoryVectorStore。

---

### 4.8 Retriever（检索器）—— 查询接口

**是什么：** Vector Store 的标准化查询接口。把向量数据库包装成统一的 `Retriever`，这样换存储不影响业务代码。

```typescript
// 把 vectorStore 转成 retriever
const retriever = vectorStore.asRetriever({
  k: 4,  // 返回最相似的4个文档
});

// 用 retriever 查询
const docs = await retriever.invoke("如何优化性能？");
```

**Retriever 不只一种：**

| 类型 | 说明 |
|------|------|
| VectorStoreRetriever | 基于向量相似度检索（最常用） |
| SelfQueryRetriever | LLM 先把问题转成查询条件 + 语义搜索 |
| MultiQueryRetriever | 把问题改写成多个视角再分别检索 |
| EnsembleRetriever | 组合多种检索器取并集 |

---

### 4.9 Memory（记忆）—— 上下文管理

**是什么：** 让 LLM 记住之前的对话。

**本质：** LLM 本身是无状态的，每次调用都是全新的。Memory 模块做的事就是把历史对话塞进下一次请求的 prompt 里。

```typescript
import { BufferMemory } from "langchain/memory";

const memory = new BufferMemory({
  memoryKey: "chat_history",   // 在 prompt 模板中的变量名
  returnMessages: true,         // 返回完整的 Message 对象而不是纯字符串
});

// 第一次对话
await memory.saveContext(
  { input: "我叫小明" },
  { output: "你好小明！有什么可以帮你的？" }
);

// 第二次对话时，memory 会自动加载历史
const history = await memory.loadMemoryVariables({});
console.log(history.chat_history);
// [HumanMessage("我叫小明"), AIMessage("你好小明！有什么可以帮你的？")]
```

**Memory 类型对比：**

| 类型 | 策略 | 场景 |
|------|------|------|
| BufferMemory | 全量保留所有历史 | 短对话 |
| BufferWindowMemory | 只保留最近 K 轮 | 长对话，控制 token 消耗 |
| ConversationSummaryMemory | 把旧对话总结成一段摘要 | 超长对话，兼顾记忆和 token |
| VectorStoreRetrieverMemory | 把历史存入向量库，按相关性检索 | 需要精准回忆历史细节 |

---

### 4.10 Tool（工具）—— 外部能力

**是什么：** 给 LLM 一个可以调用的函数。LLM 会输出调用参数，LangChain 帮你执行，结果返回给 LLM。

```typescript
import { tool } from "@langchain/core/tools";
import { z } from "zod";  // 用 zod 定义参数 schema

// 定义一个工具：查询天气
const weatherTool = tool(
  async ({ city }: { city: string }) => {
    // 真实场景调用天气 API
    return `${city}今天晴天，25°C`;
  },
  {
    name: "get_weather",
    description: "查询指定城市的天气。输入城市名称。",
    schema: z.object({
      city: z.string().describe("城市名称，如 '北京'"),
    }),
  }
);

// LLM 看到这个工具的描述，会自主决定：
// "用户问天气了，我应该调用 get_weather 工具，参数 city='杭州'"
```

**这就是 Agent 的基础——** LLM 有了手，可以干活了。

---

### 4.11 Agent（智能体）—— 自动决策者

**是什么：** Agent 不是一个新的模型，它是一种**编排逻辑**：

```
用户提问 → LLM 思考 → 需要工具？→ 调用工具 → 拿到结果 → LLM 再思考 → 回答用户
              ↑______________________________________________________________|
                              （循环，直到 LLM 觉得可以回答了）
```

**和普通 Chain 的区别：**

| | Chain（链） | Agent（智能体） |
|------|-----------|--------------|
| 执行路径 | 固定的，预设好的 | 动态的，LLM 自己决定 |
| 工具调用 | 不支持 | 支持，自动选择 |
| 适用场景 | 翻译、摘要等确定性任务 | 需要推理、多步操作的任务 |
| 类比 | 传送带 | 一个会使用工具的助手 |

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { HumanMessage } from "@langchain/core/messages";

// 准备好模型和工具
const model = new ChatOpenAI({ model: "gpt-4o" });
const tools = [weatherTool, calculatorTool, searchTool];

// 创建 Agent（LangGraph 是目前推荐的 Agent 框架）
const agent = createReactAgent({
  llm: model,
  tools,
  prompt: "你是一个乐于助人的助手。遇到不确定的信息请使用工具查询。",
});

// 调用 Agent
const result = await agent.invoke({
  messages: [new HumanMessage("杭州今天天气怎么样？适合出游吗？")],
});

console.log(result.messages[result.messages.length - 1].content);
```

**LangGraph vs 旧版 AgentExecutor：** LangChain 现在推荐用 LangGraph 创建 Agent，它把 Agent 的决策循环建模成「节点 + 边」的有向图，比旧版 `AgentExecutor` 更灵活可控。

---

## 5. RAG 全景流程

RAG = Retrieval-Augmented Generation = **检索增强生成**

把前面学的模块串起来，就是一个完整的 RAG 系统：

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  文档加载    │ →  │  文本分割    │ →  │  向量嵌入    │
│  (Loader)   │    │  (Splitter)  │    │ (Embeddings) │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                                │
          ┌─────────────────────────────────────┘
          ↓
┌──────────────────┐     ┌──────────────────┐
│   向量数据库      │ ←→  │    检索器        │
│  (Vector Store)  │     │   (Retriever)    │
└──────────────────┘     └────────┬─────────┘
                                  │
          ┌───────────────────────┘
          ↓
┌──────────────────────────────────────────────┐
│               RAG Chain                      │
│                                              │
│  用户提问 → 检索相关文档 → 拼入 Prompt → LLM 回答  │
│                                              │
│  "根据以下参考资料回答问题：                  │
│   {检索到的文档}                              │
│   用户问题：{用户输入}"                        │
└──────────────────────────────────────────────┘
```

**完整 TypeScript 示例：**

```typescript
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { TextLoader } from "langchain/document_loaders/fs/text";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { RunnableSequence, RunnablePassthrough } from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers";

// ============ 第一步：准备知识库 ============

// 1. 加载文档
const loader = new TextLoader("./docs/company-policy.txt");
const docs = await loader.load();

// 2. 分割文档
const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,
  chunkOverlap: 50,
});
const chunks = await splitter.splitDocuments(docs);

// 3. 创建向量存储
const embeddings = new OpenAIEmbeddings();
const vectorStore = await MemoryVectorStore.fromDocuments(chunks, embeddings);
const retriever = vectorStore.asRetriever({ k: 3 });

// ============ 第二步：构建 RAG Chain ============

const model = new ChatOpenAI({ model: "gpt-4o", temperature: 0 });

// Prompt 模板：告诉模型用参考资料回答
const prompt = ChatPromptTemplate.fromTemplate(`
你是一个专业的企业知识问答助手。请根据以下参考资料回答用户问题。
如果参考资料中没有相关信息，请如实说"我不确定"。

参考资料：
{context}

用户问题：{question}

回答：
`);

// 把检索结果格式化成纯文本
const formatDocs = (docs: Document[]) =>
  docs.map((doc) => doc.pageContent).join("\n\n");

// 构建 Chain
const ragChain = RunnableSequence.from([
  {
    context: retriever.pipe(formatDocs),  // 检索 + 格式化
    question: new RunnablePassthrough(),   // 原样传递用户问题
  },
  prompt,
  model,
  new StringOutputParser(),
]);

// ============ 第三步：使用 ============

const answer = await ragChain.invoke("公司年假政策是什么？");
console.log(answer);
```

---

## 6. 从 Chain 到 Agent 的进化

理解两者的关系很重要：

```
Chain（链）              Agent（智能体）
─────────────            ──────────────────
A → B → C               LLM 自主决策：
确定性流程               - 要不要查资料？
- 翻译                   - 要不要调 API？
- 摘要                   - 要不要计算？
- 格式化输出             - 分几步完成？
                         - 每个步骤怎么做？

        ←──── 复杂度递增 ────→
        ←──── 灵活性递增 ────→
```

**RAG Agent 示例（结合检索 + 工具）：**

```typescript
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { createRetrieverTool } from "@langchain/core/tools";

// 把检索器包装成 Tool
const retrieverTool = createRetrieverTool(retriever, {
  name: "search_knowledge_base",
  description: "在公司知识库中搜索相关政策、流程、制度信息。对于任何公司内部问题，请先使用此工具。",
});

// 其他工具
const tools = [retrieverTool, weatherTool, calculatorTool];

// 创建 RAG Agent
const agent = createReactAgent({
  llm: model,
  tools,
  prompt: `你是公司内部助手。
- 涉及公司制度的，用 search_knowledge_base 查询
- 涉及实时信息的（天气等），用对应工具查询
- 遇到计算问题，用 calculator
- 不要在不确定时编造信息`,
});

// 使用
const result = await agent.invoke({
  messages: [new HumanMessage("我想请年假，公司规定最少提前几天申请？")],
});
```

---

## 7. 实际项目结构建议

```
src/
├── agents/              # Agent 定义
│   └── company-assistant.ts
├── chains/              # Chain 定义（简单链）
│   └── translation-chain.ts
├── tools/               # 自定义 Tool
│   ├── weather.tool.ts
│   └── calculator.tool.ts
├── knowledge/           # 知识库相关
│   ├── loader.ts        # 文档加载
│   ├── splitter.ts      # 文本分割
│   └── vector-store.ts  # 向量存储初始化
├── prompts/             # Prompt 模板
│   └── rag-prompt.ts
├── config/              # 配置
│   └── model.config.ts  # 模型统一配置
└── index.ts             # 入口
```

---

## 8. 常见坑与最佳实践

### 8.1 Token 消耗

- **问题：** 检索了太多文档块，导致 prompt 超长，花钱如流水
- **解决：** `retriever.asRetriever({ k: 3 })` 控制检索数量；必要时对检索结果做重排序（rerank）

### 8.2 检索不精准

- **问题：** 用户问「年假」，结果返回了「病假」「事假」「婚假」全来了
- **解决：** 优化 chunk 大小、使用更好的 Embedding 模型、加入关键词过滤

### 8.3 Agent 无限循环

- **问题：** Agent 不停调用工具，永远不给出最终答案
- **解决：** 设置 `maxIterations`（默认通常为 10）、在 prompt 中明确要求「最终必须给出答案」

### 8.4 记忆膨胀

- **问题：** 长时间对话，历史消息占满上下文窗口
- **解决：** 使用 `ConversationSummaryMemory` 自动压缩旧对话

### 8.5 本地开发环境变量

```bash
# .env
OPENAI_API_KEY=sk-xxxxx
LANGCHAIN_TRACING_V2=true        # 开启 LangSmith 调试追踪
LANGCHAIN_API_KEY=ls_xxxxx       # LangSmith API Key
```

```typescript
import "dotenv/config";  // 确保最先加载
```

---

## 总结

**LangChain 学习口诀：**

> Model 是大脑，Prompt 是话术，Chain 是流水线。  
> Loader 读文档，Splitter 切小块，Embeddings 转坐标。  
> Vector Store 存向量，Retriever 查相似。  
> Memory 记历史，Tool 给能力，Agent 自主决策。  
> RAG 就是：检索 + 拼接 + 生成。

**下一步学习建议：**
1. 先用简单 Chain 跑通一个翻译 / 摘要功能
2. 再搭建一个基础的 RAG（加载你自己的文档问答）
3. 然后给 RAG 加上 Memory
4. 最后引入 Tool + Agent，做一个能自主查询的智能助手

---

> 📦 本文配套 npm 包：  
> `@langchain/core` `@langchain/openai` `@langchain/community` `@langchain/langgraph` `langchain` `zod` `dotenv`
