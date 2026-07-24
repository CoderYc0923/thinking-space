# 多 Agent 编排模式全景

> 整理时间：2026年7月  
> 涵盖：主流架构模式、框架对比、设计原则、与 pi-agent-core 统一工作流模式的映射

---

## 一、多 Agent 编排的核心问题

单 Agent（ReAct Loop）能解决很多问题，但面对复杂场景时会遇到瓶颈：

| 瓶颈 | 说明 |
|------|------|
| **上下文窗口限制** | 单 Agent 的上下文有限，复杂任务信息量爆炸 |
| **能力边界** | 一个 Agent 无法同时精通代码、写作、数据分析 |
| **幻觉放大** | 单 Agent 错误无校验，多 Agent 可交叉验证 |
| **工具调用冲突** | 不同子任务需要不同的工具集和权限 |

多 Agent 编排的本质：**把复杂任务拆成多个子任务，分配给多个专业化 Agent，通过控制流协调它们协作完成。**

---

## 二、七大主流编排模式

### 2.1 Sequential（顺序编排）

```
[Agent A] → [Agent B] → [Agent C] → 结果
```

- **原理**：前一个 Agent 的输出作为后一个 Agent 的输入，流水线式处理
- **适用场景**：文档生成流水线（调研→撰写→润色→审校）、数据处理 ETL
- **代表框架**：LangChain LCEL 的 `.pipe()` 链式调用
- **优点**：简单可控，调试方便
- **缺点**：缺乏并行能力，前置错误会级联放大

### 2.2 Parallel（并行编排）

```
         ┌─ [Agent A] ─┐
[输入] ──┼─ [Agent B] ─┼── [聚合] → 结果
         └─ [Agent C] ─┘
```

- **原理**：同一输入分发给多个 Agent 并行处理，结果汇总合并
- **适用场景**：多维度分析（同一篇新闻→情感分析+实体提取+摘要生成）、投票/多数表决
- **代表框架**：LangGraph 的 `Send` API、CrewAI 的并行 Task
- **优点**：速度快，多视角交叉验证
- **缺点**：资源消耗大，结果聚合逻辑复杂

### 2.3 Router（路由编排）

```
              ┌→ [Agent A: 技术问题]
[用户输入] → [Router] ─┼→ [Agent B: 售后问题]
              └→ [Agent C: 投诉升级]
```

- **原理**：根据输入内容动态判断交给哪个 Agent 处理
- **适用场景**：智能客服分流、多领域问答系统
- **代表框架**：LangGraph 的条件边（conditional edge）、AutoGen 的 SelectorGroupChat
- **优点**：专业化处理，避免"万能 Agent"的平庸
- **缺点**：路由判断本身可能出错，需要兜底机制

### 2.4 Debate / 辩论模式

```
[Agent A: 正方] ⇄ [Agent B: 反方] ⇄ [裁判 Agent] → 结论
```

- **原理**：多个 Agent 对同一问题持不同立场进行辩论，由裁判或共识机制得出最终结论
- **适用场景**：事实核查、代码审查、安全审计、决策辅助
- **代表框架**：AutoGen 的 GroupChat、ChatEval
- **核心价值**：**通过对抗降低幻觉**——一个 Agent 的胡说会被另一个 Agent 质疑
- **关键机制**：多轮辩论直到收敛，或达到最大轮数由裁判裁决

### 2.5 Hierarchical / 层级委派

```
              [Manager Agent]
              /      |      \
     [Worker A]  [Worker B]  [Worker C]
```

- **原理**：Manager 负责拆解任务、分配子任务、汇总结果；Worker 专注于执行
- **适用场景**：复杂项目管理、软件工程全流程（需求→设计→编码→测试）
- **代表框架**：CrewAI（原生支持 Role-Based 层级）、AutoGen 的 GroupChatManager
- **优点**：任务分解清晰，职责分明
- **缺点**：Manager 本身可能成为瓶颈，调度策略设计复杂

### 2.6 Swarm / 群体协作

```
[Agent A] ←→ [Agent B]
    ↕          ↕
[Agent C] ←→ [Agent D]  （去中心化，无固定拓扑）
```

- **原理**：大量轻量 Agent 通过消息传递自发协作，无中央协调者
- **适用场景**：大规模模拟（社会仿真、市场模拟）、分布式搜索
- **代表框架**：OpenAI Swarm（实验性）、Google Agent-to-Agent Protocol
- **关键特征**：去中心化、自组织、涌现行为
- **挑战**：可控性差，结果不可预测

### 2.7 Plan-Execute / 规划执行

```
[Planner Agent] → 生成执行计划
       ↓
[Executor Agent] → 逐步执行
       ↓
[Reviewer Agent] → 检查结果 → 通过/返工
```

- **原理**：规划与执行分离，Plan→Execute→Review 循环
- **适用场景**：长周期任务、代码生成+测试+修复
- **代表框架**：LangGraph 的 Plan-Execute 模式、CrewAI 的 Process 机制
- **优点**：长任务可追踪，中间结果可审查
- **缺点**：规划可能不准确，需要动态重规划能力

---

## 三、主流框架对比

### 3.1 框架概览

| 维度 | LangGraph | CrewAI | AutoGen | OpenAI Agents SDK |
|------|-----------|--------|---------|-------------------|
| **开发者** | LangChain | CrewAI Inc. | Microsoft | OpenAI |
| **语言** | Python / JS | Python | Python | Python |
| **核心理念** | 图状态机 | 角色扮演团队 | 对话驱动 | 极简 Agent |
| **编排模型** | 有向图 + 条件边 | 顺序/层级 Process | GroupChat | Handoff 交接 |
| **状态管理** | 显式 State 对象 | 隐式 | 对话历史 | 隐式 |
| **人机协同** | `interrupt` 断点 | `human_input` | `UserProxyAgent` | 内置 |
| **可观测性** | LangSmith | 有限 | 有限 | OpenAI Dashboard |
| **生产就绪** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **学习曲线** | 陡峭 | 平缓 | 中等 | 平缓 |

### 3.2 选型建议

```
你的场景 → 框架推荐

简单链式调用          → LangChain LCEL（不需要图）
复杂分支+条件逻辑     → LangGraph（图状态机最强）
角色扮演团队协作      → CrewAI（开箱即用）
多 Agent 对话辩论     → AutoGen（对话原生）
快速原型+简单交接     → OpenAI Agents SDK
TypeScript 优先       → LangGraph.js / LangChain.js
```

---

## 四、设计原则与反模式

### 4.1 核心原则

1. **单一职责**：每个 Agent 只做一件事，做好一件事
2. **控制流反转**：Agent 不感知自己处于何种编排中（与 pi-agent-core 理念一致）
3. **优雅降级**：单个 Agent 失败不应导致整个编排崩溃
4. **可观测性优先**：每个 Agent 的输入/输出/耗时必须可追踪
5. **最小权限**：Agent 只拥有完成其任务所需的最小工具集

### 4.2 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **万能 Agent** | 一个 Agent 承担所有任务，上下文爆炸 | 按职责拆分为多个专业 Agent |
| **过度编排** | 简单任务也用复杂多 Agent | 能用单 Agent 就不用多 Agent |
| **无兜底路由** | Router 没有默认分支 | 始终保留 fallback Agent |
| **循环无上限** | Agent 间无限循环调用 | 设置 `max_turns` 或 `recursion_limit` |
| **无状态追踪** | 执行到哪一步无法知道 | 显式管理 State，支持断点续跑 |

---

## 五、与 pi-agent-core 统一工作流模式的映射

你之前学过的 pi-agent-core 三层抽象可以直接覆盖上述所有模式：

| 编排模式 | ControlFlow 映射 | 说明 |
|----------|-----------------|------|
| Sequential | `Sequential` | 线性串联 WorkflowUnit |
| Parallel | `Parallel` | 多单元并发，结果聚合 |
| Router | `Router` + Steering | 条件判断选择下游单元 |
| Debate | `Loop` + 多单元 | 循环直到收敛 |
| Hierarchical | `Delegation` | Manager 委派给 Worker |
| Swarm | 多单元 + MessageBus | 去中心化消息传递 |
| Plan-Execute | `Sequential` + `Loop` | Planner→Executor→Reviewer 循环 |

核心公式再次验证：

```
Agent 工作流 = AgentLoop ⊗ (Steering/FollowUp) ⊗ ControlFlow
```

所有"花里胡哨"的多 Agent 模式，本质上是 **WorkflowUnit + ControlFlow 的组合**，WorkflowUnit 永远不感知自己处于何种编排中（控制流反转），这保证了任意混合模式的逻辑自洽。

---

## 六、TypeScript 生态现状

你偏好 TypeScript，目前各框架的 JS/TS 支持情况：

| 框架 | TypeScript 支持 | 推荐度 |
|------|----------------|--------|
| **LangGraph.js** | ✅ 官方支持，API 与 Python 版一致 | ⭐⭐⭐⭐⭐ |
| **LangChain.js** | ✅ 官方支持，生态成熟 | ⭐⭐⭐⭐⭐ |
| **CrewAI** | ❌ 仅 Python | — |
| **AutoGen** | ❌ 仅 Python（社区有非官方 JS 端口） | — |
| **OpenAI Agents SDK** | ❌ 仅 Python | — |
| **Mastra** | ✅ TypeScript 原生 | ⭐⭐⭐⭐ |
| **Vercel AI SDK** | ✅ TypeScript 原生，轻量 | ⭐⭐⭐⭐ |

**结论**：在 TypeScript 生态中，**LangGraph.js** 是多 Agent 编排的最佳选择，配合 **LangChain.js** 作为工具/模型抽象层。

---

## 七、参考资料

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangGraph.js 快速入门](https://langchain-ai.github.io/langgraphjs/)
- [CrewAI 官方文档](https://docs.crewai.com/)
- [AutoGen 官方文档](https://microsoft.github.io/autogen/)
- [OpenAI Agents SDK](https://platform.openai.com/docs/guides/agents)
- [Anthropic 多 Agent 最佳实践](https://docs.anthropic.com/en/docs/build-with-claude/multi-agent)
- [pi-agent-core 统一工作流模式设计](./Agent统一工作流模式设计.md)
