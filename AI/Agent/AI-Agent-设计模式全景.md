# AI Agent 设计模式全景（2025-2026）

> 整理日期：2026年7月 | 覆盖国内外主流Agent架构设计

---

## 一、总览：Agent 设计模式分类

当前（2025-2026）Agent 设计模式已从单一 ReAct 演进为**多层次、多范式**的生态。按核心逻辑可划分为以下几大类：

| 分类 | 代表模式 | 核心思想 | 适用场景 |
|------|---------|---------|---------|
| **推理循环型** | ReAct、Reasoner-Actor | 思考-行动-观察循环 | 通用任务、工具调用 |
| **规划先行型** | Plan-and-Execute、Plan-Then-Execute | 先制定完整计划再逐步执行 | 复杂多步任务 |
| **自我完善型** | Reflexion、Self-Refine、CRITIC | 执行后自我反思并修正 | 代码生成、写作、数学推理 |
| **多智能体型** | Multi-Agent、Swarm、Supervisor | 多个专业Agent协作分工 | 复杂系统、多领域协作 |
| **路由分发型** | Router/Routing、MoE-Agent | 根据任务类型分发到不同处理分支 | 多功能助手、客服系统 |
| **树/图搜索型** | Tree-of-Thought、Graph-of-Thought、A* Search | 搜索式探索多条路径选最优 | 数学证明、策略规划 |

---

## 二、ReAct（Reasoning + Acting）— 当前最主流

### 提出者
Google Research & Princeton University，2022年论文《ReAct: Synergizing Reasoning and Acting in Language Models》

### 核心原理

```
┌──────────────────────────────────────────┐
│                ReAct 循环                 │
│                                          │
│  ┌──────────┐     ┌──────────────┐       │
│  │ Thought  │────▶│   Action     │       │
│  │ (思考)   │     │ (执行工具)    │       │
│  └──────────┘     └──────┬───────┘       │
│        ▲                 │               │
│        │          ┌──────▼───────┐       │
│        └──────────│ Observation  │       │
│                   │ (观察结果)    │       │
│                   └──────────────┘       │
└──────────────────────────────────────────┘
```

- **Thought（思考）**：LLM 分析当前状态，决定下一步做什么
- **Action（行动）**：调用工具、API或执行具体操作
- **Observation（观察）**：获取工具返回结果，作为下一轮思考的输入
- **循环终止**：LLM 判断任务完成，输出 Final Answer

### 伪代码流程

```
1. 用户输入问题
2. Thought: "我需要先搜索相关资料"
3. Action: search("2025年AI发展趋势")
4. Observation: [搜索结果摘要]
5. Thought: "根据结果，我还需要查询具体数据"
6. Action: calculate("AI市场规模增长率")
7. Observation: 计算结果
8. Thought: "信息已足够，可以给出答案"
9. Final Answer: 整理后的完整回答
```

### 代表实现
- **LangChain AgentExecutor**（Python/TypeScript）- 最广泛使用的 ReAct 实现
- **OpenAI Function Calling / Tools API** - 本质是简化版 ReAct
- **Anthropic Tool Use** - Claude 的原生 ReAct 能力
- **Cohere Coral** - 企业级 ReAct Agent

### 优缺点

| 优点 | 缺点 |
|------|------|
| ✅ 灵活，可动态调整策略 | ❌ Token 消耗大（每步都要完整上下文）|
| ✅ 可观察性强（思维链可见）| ❌ 容易陷入循环或死胡同 |
| ✅ 与工具生态深度绑定 | ❌ 复杂任务可能规划不足 |
| ✅ 社区成熟，资料丰富 | ❌ 依赖工具描述的准确性 |

---

## 三、Plan-and-Execute（规划-执行）

### 核心原理

```
┌──────────────┐     ┌──────────────────────┐
│   Planner    │────▶│    Executor          │
│  制定完整计划  │     │   逐步执行计划         │
│              │     │   （可调用ReAct子循环）  │
└──────────────┘     └──────────────────────┘
```

与 ReAct 的关键区别：**先有全局计划，再有步骤执行**，而非走一步看一步。

### 变体

1. **Plan-Then-Execute**：计划一次性生成，不可中途修改
2. **Plan-and-Execute with Replanning**：执行过程中可根据反馈重新规划
3. **Hierarchical Planning**：多层计划（高层目标 → 子目标 → 具体动作）

### 代表实现
- **LangChain PlanAndExecuteAgentExecutor**
- **AutoGPT**（部分采用）
- **BabyAGI** - 经典的任务驱动型计划执行
- **Microsoft TaskWeaver** - 代码优先的计划执行

### 适用场景
- 需要多步骤完成的复杂任务（如"帮我做一个完整的市场调研报告"）
- 任务步骤之间依赖关系明确
- 需要执行前预览和确认的场景

---

## 四、Reflexion（反思模式）

### 提出者
Noah Shinn 等，2023年论文《Reflexion: Language Agents with Verbal Reinforcement Learning》

### 核心原理

```
┌──────────────────────────────────────────────┐
│              Reflexion 循环                    │
│                                               │
│  ┌────────┐    ┌────────┐    ┌────────────┐  │
│  │ Actor  │───▶│Evaluator│───▶│ Self-Reflect│  │
│  │ 执行任务 │    │ 评估结果 │    │ 自我反思     │  │
│  └────────┘    └────────┘    └─────┬──────┘  │
│       ▲                            │         │
│       └──────── 修正后重试 ◀────────┘         │
└──────────────────────────────────────────────┘
```

- Actor：使用 ReAct 或其他方式执行任务
- Evaluator：评估执行结果（成功/失败/质量打分）
- Self-Reflection：**用语言形式**总结失败原因和经验教训
- 将反思结果存入长期记忆，影响后续执行

### 核心创新
用**自然语言**而非数值梯度来做"强化学习"，反思结果直接作为后续 prompt 的上下文。

### 代表实现
- **LangChain Reflexion**（langchain-experimental）
- **Self-Refine**（CMU & Allen AI）
- **CRITIC**（自我验证+修正）
- **MetaGPT 的自我反思机制**

### 适用场景
- 代码生成与 Debug
- 写作优化（"写一篇文章 → 自我评价 → 修改"）
- 数学推理验证

---

## 五、Multi-Agent（多智能体协作）

### 核心思想
多个专业化 Agent 像公司团队一样分工协作。

### 架构模式

#### 5.1 Supervisor 模式（主管-工人）

```
         ┌──────────────┐
         │  Supervisor   │ (调度/决策)
         └───┬───┬───┬──┘
     ┌───────┘   │   └──────┐
┌────▼───┐ ┌────▼───┐ ┌────▼───┐
│Researcher│ │ Coder  │ │ Writer  │
│  研究员  │ │ 程序员  │ │  写手   │
└────────┘ └────────┘ └────────┘
```

- 一个 Supervisor Agent 负责任务分解和分配
- 各专业 Agent 执行自己的任务
- Supervisor 汇总结果、判断是否完成

**代表实现**：LangGraph SupervisorAgent、AutoGen GroupChat

#### 5.2 顺序流水线模式

```
[需求分析] → [方案设计] → [代码实现] → [测试审查] → [文档输出]
   Agent1       Agent2       Agent3       Agent4        Agent5
```

**代表实现**：MetaGPT（模拟软件公司SOP流水线）

#### 5.3 辩论/协作模式

```
┌──────────┐      ┌──────────┐
│ Agent A  │◀────▶│ Agent B  │  (相互辩论/补充)
│ 正方观点  │      │ 反方观点  │
└──────────┘      └──────────┘
        │              │
        └──────┬───────┘
         ┌─────▼─────┐
         │  综合判断   │
         └───────────┘
```

- 多个 Agent 针对同一问题给出不同视角
- 通过辩论或投票达成共识

**代表实现**：ChatDev、DuetGPT

### 主流多智能体框架

| 框架 | 特点 | 语言 |
|------|------|------|
| **Microsoft AutoGen** | 对话式多Agent，灵活编排 | Python |
| **LangGraph** | 图状态机，精确控制流程 | Python/JS |
| **CrewAI** | 角色化Agent团队 | Python |
| **MetaGPT** | 模拟软件公司SOP | Python |
| **OpenAI Swarm** | 轻量级Agent切换 | Python |
| **字节跳动 Coze/扣子** | 可视化多Agent编排 | 低代码 |
| **Dify** | 工作流+Agent编排 | 低代码 |

---

## 六、其他重要设计模式

### 6.1 Router / Routing（路由分发）

```
用户输入 → [Router 分类器] → 分发到对应专业模块
                │
      ┌────────┼────────┬────────┐
   ┌──▼──┐  ┌──▼──┐  ┌──▼──┐  ┌──▼──┐
   │翻译 │  │代码 │  │写作 │  │闲聊 │
   └────┘  └────┘  └────┘  └────┘
```

- 先识别用户意图，再路由到对应的处理模块
- 降低单一 Agent 的复杂度
- 代表：OpenAI Assistants API Routing、LangChain RouterChain

### 6.2 Tree-of-Thought / Graph-of-Thought（思维树/图搜索）

- **ToT（Tree-of-Thought）**：同时探索多个推理路径，每步评估并剪枝
- **GoT（Graph-of-Thought）**：比树更灵活，允许路径合并
- **A* Search for LLM**：用启发式搜索找最优推理路径
- 适用：数学证明、逻辑推理、策略游戏

### 6.3 RAG + Agent 融合模式

```
用户问题 → Agent
              │
              ├─ 需要检索知识？ → RAG检索 → 注入上下文 → 继续推理
              ├─ 需要调用工具？ → 工具调用 → 获取结果 → 继续推理
              └─ 信息足够？   → 生成最终答案
```

- 现代 Agent 几乎都集成了 RAG 作为"知识检索工具"
- 代表：LangChain RAG + Agent、Coze 知识库+Agent、Dify 知识库+工作流

---

## 七、国内主流框架与设计模式

### 7.1 字节跳动 Coze / 扣子

- **模式**：可视化 Multi-Agent + Workflow 编排
- **特点**：低代码拖拽式，国内生态最完善
- **适用**：快速搭建 Bot、企业客服、营销助手

### 7.2 Dify（开源）

- **模式**：Workflow（ChatFlow / Workflow）
- **特点**：开源可私有部署，支持 RAG + Agent + 工具
- **编排方式**：节点式可视化编排，类似流程图

### 7.3 百度文心智能体平台

- **模式**：ReAct + 百度生态工具集成
- **特点**：深度绑定文心大模型和百度搜索/地图等

### 7.4 阿里百炼 / 通义千问 Agent

- **模式**：ReAct + Multi-Agent（百炼平台支持多Agent编排）
- **特点**：与阿里云服务深度集成，支持 Function Calling

### 7.5 智谱 AutoGLM / GLM Agent

- **模式**：ReAct + 反思 + 工具调用
- **特点**：手机端 Agent（AutoGLM可操控手机App）

### 7.6 FastGPT（开源）

- **模式**：Workflow + RAG + Agent 工具调用
- **特点**：开源、私有化部署友好、社区活跃

---

## 八、模式选择决策指南

```
你的任务是什么？
│
├─ 简单问答 / 单步工具调用
│  └─ 推荐：ReAct（OpenAI Function Calling 即可）
│
├─ 需要多步规划且步骤明确
│  └─ 推荐：Plan-and-Execute
│
├─ 需要高质量输出（代码/文章）
│  └─ 推荐：ReAct + Reflexion（自我反思修正）
│
├─ 复杂系统，多种专业能力
│  └─ 推荐：Multi-Agent（Supervisor模式或流水线）
│
├─ 多功能助手，需要意图分类
│  └─ 推荐：Router + 专业子Agent
│
├─ 需要搜索/知识库回答
│  └─ 推荐：RAG + Agent 融合模式
│
└─ 极复杂推理（数学/逻辑）
   └─ 推荐：Tree-of-Thought / Graph-of-Thought
```

---

## 九、总结：ReAct 仍是主流吗？

**是的，ReAct 仍然是 2025-2026 年最主流的基础范式**，但有几个重要趋势：

1. **ReAct 不是唯一选择**：它是最底层、最通用的循环模式，复杂系统通常在 ReAct 之上叠加其他模式
2. **Multi-Agent 快速崛起**：AutoGen、LangGraph、CrewAI 让多Agent协作成为新热点
3. **RAG + Agent 深度融合**：几乎所有生产级 Agent 都集成了 RAG
4. **反思/自修正成为标配**：Reflexion、Self-Refine 等机制大幅提升输出质量
5. **低代码 Agent 编排普及**：Coze、Dify 让非开发者也能搭建 Agent

**一句话总结**：ReAct 是地基，Multi-Agent + RAG + Reflexion 是上层建筑。

---

## 参考资料

- [ReAct Paper](https://arxiv.org/abs/2210.03629) - Google Research, 2022
- [Reflexion Paper](https://arxiv.org/abs/2303.11366) - Noah Shinn et al., 2023
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) - Princeton/Google DeepMind, 2023
- [LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) - Lilian Weng (OpenAI)
- [LangChain Agent Documentation](https://js.langchain.com/docs/concepts/agents)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraphjs/)
- [Microsoft AutoGen](https://github.com/microsoft/autogen)
- [CrewAI](https://github.com/crewAIInc/crewAI)
