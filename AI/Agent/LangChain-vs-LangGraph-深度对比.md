# LangChain vs LangGraph 全面对比分析

> 本文从设计模式、底层原理、应用场景、优缺点等角度，系统梳理 LangChain 和 LangGraph 的区别与联系。

---

## 一、核心定位

| 维度 | LangChain | LangGraph |
|------|-----------|-----------|
| **本质** | LLM 应用开发**框架** | 有状态、多角色**编排引擎** |
| **目标** | 快速构建 LLM 应用原型 | 构建复杂、生产级 Agent 系统 |
| **作者** | Harrison Chase (LangChain Inc.) | 同一团队，LangChain 生态子项目 |
| **首次发布** | 2022年10月 | 2023年8月 |

**一句话概括关系：LangChain 提供"零件"，LangGraph 提供"装配流水线"。**

- LangChain 帮你快速集成各种 LLM、工具、向量数据库
- LangGraph 帮你精确控制 Agent 的执行流程、状态和分支

---

## 二、设计模式

### 2.1 LangChain：链式调用（Chain Pattern）

经典设计是**责任链模式 + 管道模式**。把多个步骤串成线性流水线，数据从上一步流入下一步。

```
用户输入 → Prompt模板 → LLM调用 → 输出解析 → 返回结果
```

**核心抽象：**

| 抽象 | 说明 |
|------|------|
| `Chain` | 可组合的执行单元 |
| `LCEL`（LangChain Expression Language） | 用 `\|` 管道符串联组件 |
| `Runnable` 接口 | 统一的 `invoke`/`batch`/`stream` 调用规范 |

**TypeScript 示例：**

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { PromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const model = new ChatOpenAI({ modelName: "gpt-4" });
const prompt = PromptTemplate.fromTemplate(
  "将以下文本翻译为{target_lang}：{text}"
);
const parser = new StringOutputParser();

// 管道式串联
const chain = prompt.pipe(model).pipe(parser);

const result = await chain.invoke({
  target_lang: "英文",
  text: "今天天气真好",
});
// 输出：The weather is really nice today.
```

> 这种链式模式**本质上是一个 DAG（有向无环图）**，数据单向流动，没有循环和复杂分支。

### 2.2 LangGraph：图状态机（Graph State Machine）

设计灵感来自 **Actor 模型**和**有限状态机**，把应用建模为一个**有向图（允许循环）**。

- 图中的**节点**代表计算步骤
- **边**代表控制流

**核心抽象：**

| 抽象 | 说明 |
|------|------|
| `StateGraph` | 定义整个应用的状态和流转 |
| `Node` | 处理状态并返回更新的函数 |
| `Edge` | 连接节点的有向边（普通边 / 条件边） |
| `State` | 贯穿整个图的共享状态对象 |
| `Checkpointer` | 状态持久化机制（支持暂停、恢复、回溯） |

**TypeScript 示例：**

```typescript
import { StateGraph, Annotation, END, START } from "@langchain/langgraph";

// 1. 定义状态结构
const AgentState = Annotation.Root({
  messages: Annotation<string[]>({
    reducer: (prev, next) => prev.concat(next),
    default: () => [],
  }),
});

// 2. 定义节点函数
const callModel = async (state: typeof AgentState.State) => {
  const model = new ChatOpenAI({ modelName: "gpt-4" });
  const response = await model.invoke(state.messages);
  return { messages: [response] };
};

const shouldContinue = (state: typeof AgentState.State) => {
  const lastMessage = state.messages[state.messages.length - 1];
  if (lastMessage.tool_calls?.length) {
    return "tools";
  }
  return END;
};

// 3. 构建图
const workflow = new StateGraph(AgentState)
  .addNode("agent", callModel)
  .addNode("tools", toolNode)
  .addEdge(START, "agent")
  .addConditionalEdges("agent", shouldContinue)
  .addEdge("tools", "agent"); // ← 允许循环！agent → tools → agent

const app = workflow.compile();
await app.invoke({ messages: ["帮我查一下今天的天气"] });
```

---

## 三、底层原理

### 3.1 LangChain 原理

1. **Runnable 接口**：所有组件实现统一的 `invoke`（单次调用）、`stream`（流式）、`batch`（批量）方法，这是可组合性的基础。
2. **LCEL 管道**：`a | b | c` 被解析成 `RunnableSequence` 对象，内部维护一个步骤数组，依次执行。
3. **回调系统**：通过 `Callbacks` 机制在生命周期节点（`on_llm_start`、`on_chain_end` 等）插入钩子，用于日志、监控、token 计数。
4. **输出解析器**：将 LLM 的原始字符串输出强制转换成结构化数据（JSON、函数调用等）。

### 3.2 LangGraph 原理

1. **状态图编译**：`StateGraph.compile()` 将定义的节点/边编译成一个可执行的 `CompiledGraph` 对象。
2. **Pregel 执行模型**（借鉴 Google 的大规模图处理框架）：
   - 每个"超级步"（Superstep）中，所有可执行的节点并行运行。
   - 节点通过**通道**（Channel）读取和更新状态。
   - 状态合并采用用户自定义的 `reducer` 函数（如 `append`、`replace`）。
3. **条件边**：根据当前状态动态决定下一步执行哪个节点，实现智能路由。
4. **检查点机制（Checkpointer）**：
   - 每个节点执行后自动保存状态快照。
   - 支持 `thread_id` 隔离多用户会话。
   - 支持**时间旅行**：可回到任意历史状态重新执行（适用于错误恢复、A/B 测试）。

---

## 四、应用场景

| 场景 | LangChain 适用 | LangGraph 适用 |
|------|:---:|:---:|
| 简单 RAG 问答（检索→增强→生成） | ✅ 最佳 | ⚠️ 过于复杂 |
| 提示词模板 + LLM 调用 | ✅ 最佳 | ⚠️ 杀鸡用牛刀 |
| 文档摘要/翻译 | ✅ 最佳 | ⚠️ 无必要 |
| 多步骤推理 Agent（ReAct/Plan-Execute） | ⚠️ 较局限 | ✅ 最佳 |
| 多 Agent 协作（分工、辩论、层级） | ❌ 困难 | ✅ 最佳 |
| 人在回路（Human-in-the-loop） | ❌ 难以实现 | ✅ 原生支持 |
| 长时间运行的工作流（数小时/天） | ❌ 不支持 | ✅ 检查点暂停恢复 |
| 动态路由和循环（if/else/while） | ⚠️ 勉强实现 | ✅ 天然适配 |

---

## 五、关键区别总览

| 对比维度 | LangChain | LangGraph |
|----------|-----------|-----------|
| **控制流** | 链式（线性/单向） | 图（循环/双向/任意跳转） |
| **状态管理** | 无内置状态，通过参数传递 | 全局 `State` + Checkpointer 持久化 |
| **循环支持** | 困难（需手动递归） | 原生支持，`addEdge("B", "A")` 即可 |
| **条件分支** | `RunnableBranch`（功能有限） | 条件边 + 路由函数（强大灵活） |
| **并行执行** | 有限（`RunnableParallel`） | Pregel 超级步天然并行 |
| **暂停/恢复** | ❌ 不支持 | ✅ 通过 Checkpointer 实现 |
| **人机交互** | 需要自己拼接 | `interrupt()` 一行代码暂停等输入 |
| **调试可视化** | LangSmith 链路追踪 | LangSmith + 图的 Mermaid/可视化 |
| **学习曲线** | 低→中 | 中→高 |

---

## 六、优缺点

### LangChain

**✅ 优点：**
- 快速上手，LCEL 管道符直观易懂
- 生态庞大：数百个集成（模型、向量库、工具）
- 适合 80% 的常规 LLM 应用场景
- TypeScript 和 Python 双语言一等公民

**❌ 缺点：**
- 过度抽象，黑盒感强，调试困难
- 复杂逻辑下链式模型捉襟见肘（"回调地狱"）
- 版本迭代激进，API 不稳定
- 对 Agent 循环、工具调用的控制力弱

### LangGraph

**✅ 优点：**
- 精细粒度的流程控制，开发者是第一公民
- 原生支持复杂 Agent 模式（ReAct、Plan-Execute、Multi-Agent）
- 内置状态持久化和错误恢复
- 图结构可序列化、可视化、自解释
- 与 LangChain 生态无缝集成（模型、工具复用）

**❌ 缺点：**
- 学习曲线陡峭：需要理解图、状态、reducer、检查点等概念
- 简单任务代码量偏多，显得"过度工程"
- 目前生态相对较新，第三方教程/案例不如 LangChain 多
- 调试复杂图流程仍有一定难度（虽然有可视化）

---

## 七、如何选择：决策树

```
开始
 │
 ├─ 任务是否包含循环/多步推理/多Agent？
 │   ├─ 是 → 用 LangGraph
 │   └─ 否 → 继续
 │
 ├─ 是否需要暂停/恢复/人在回路？
 │   ├─ 是 → 用 LangGraph
 │   └─ 否 → 继续
 │
 └─ 是否是线性流程（RAG/翻译/摘要）？
     └─ 是 → 用 LangChain（更简单快速）
```

---

## 八、学习路径建议

结合 Node.js + TypeScript + Agent 开发背景，推荐路径如下：

1. **第一阶段：LangChain 入门**
   - 用 LCEL 快速跑通一个 RAG 或简单 Agent
   - 理解 LLM 应用的基础抽象（Prompt、Model、Parser、Chain）
   
2. **第二阶段：LangGraph 进阶**
   - 当需要复杂的 Agent 推理循环、多 Agent 协作或人机交互时
   - 用 LangGraph 的图模型获得完全的控制自由度
   
3. **第三阶段：两者结合使用**
   - LangGraph 负责顶层编排
   - LangChain 的 Model、Tool、Prompt 组件作为图中的"原子节点"

---

## 九、参考资源

- [LangChain 官方文档](https://js.langchain.com/)
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraphjs/)
- [LCEL 指南](https://js.langchain.com/docs/concepts/lcel/)
- [LangGraph 教程](https://langchain-ai.github.io/langgraphjs/tutorials/)
