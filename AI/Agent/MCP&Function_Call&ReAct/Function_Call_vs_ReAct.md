# Function Call 与 ReAct 对比详解

> AI Agent 开发中的两种核心范式：从原理、区别到应用场景的完整对比。

---

## 一、核心概念与原理

### 1. Function Call（函数调用）

**本质**：模型直接输出结构化的函数调用指令，由外部系统执行后返回结果。

**原理流程**：

```
用户输入 → LLM 判断需要调用哪个函数 + 生成参数 JSON
         → 外部系统执行函数，拿到真实结果
         → 把结果喂回 LLM，生成最终回复
```

**关键特征**：

- LLM 本身**不执行**函数，它只负责"决定调用什么、传什么参数"
- 函数执行是**确定性**的（调用天气 API 就一定返回天气数据）
- 这是一次"**工具增强**"——把 LLM 的推理能力与外部确定性能力结合
- 模型在训练时就被微调过，能识别何时该输出 function_call 而非普通文本

**示例（OpenAI Function Call 格式）**：

```typescript
// 1. 定义工具
const tools = [{
  type: "function",
  function: {
    name: "get_weather",
    description: "获取指定城市的天气",
    parameters: {
      type: "object",
      properties: {
        city: { type: "string", description: "城市名" }
      },
      required: ["city"]
    }
  }
}];

// 2. LLM 返回的不是文本，而是 function_call
// response.choices[0].message.tool_calls = [{
//   function: { name: "get_weather", arguments: '{"city": "北京"}' }
// }]

// 3. 你的代码执行真正的函数
const weather = await fetchWeather("北京");

// 4. 把结果喂回 LLM 生成自然语言回复
```

---

### 2. ReAct（Reasoning + Acting）

**本质**：让 LLM 在**思维链推理**和**执行动作**之间交替循环，通过观察反馈动态调整下一步。

**原理流程**：

```
用户输入 → Thought（思考：我需要先查什么？）
         → Action（行动：调用工具X，参数Y）
         → Observation（观察：工具返回了结果Z）
         → Thought（思考：Z 还不够，还需要查什么？）
         → Action（行动：调用工具W）
         → Observation（观察：得到最终数据）
         → Thought（思考：现在可以回答了）
         → Final Answer（最终回复）
```

**关键特征**：

- **多步推理**：不是一次性决定调用什么，而是一步一步推
- **观察驱动**：每一步的决策都基于上一步的**观察结果**
- **动态路由**：根据中间结果可以改变后续计划
- **错误恢复**：工具调用失败可以换策略重试

**示例（ReAct 提示词模式）**：

```
Question: 北京今天天气适合户外运动吗？

Thought: 我需要先查询北京今天的天气情况。
Action: get_weather[{"city": "北京"}]
Observation: 北京今天多云，气温 15-22°C，风力 3 级，空气质量良

Thought: 多云、温度适中、风力不大、空气质量良，这些条件都适合户外运动。
Final Answer: 适合！北京今天多云，15-22°C，风力不大，空气质量也不错，非常适合户外运动。
```

---

## 二、核心区别对比

| 维度 | Function Call | ReAct |
|------|--------------|-------|
| **本质** | 工具调用协议/机制 | 推理+行动的**认知框架** |
| **层级** | 底层能力（模型级别的输出格式） | 上层策略（提示词工程/编排逻辑） |
| **调用方式** | 单步：一次决定调用哪个工具 | 多步：思考-行动-观察循环 |
| **推理过程** | 隐式（黑盒，用户看不到推理） | 显式（Thought 步骤可见可审查） |
| **工具数量** | 通常一次调用 1 个工具 | 可串联调用多个工具 |
| **动态决策** | 弱：如果结果不对，需要用户再次提问 | 强：根据 Observation 自动调整下一步 |
| **错误处理** | 依赖外部代码处理异常 | 可以在 Thought 中自我纠错 |
| **模型要求** | 需要模型支持 tool_calls 输出格式 | 只需要模型能遵循提示词模板 |
| **延迟** | 低（通常 2 次 API 调用） | 高（每轮循环都有 API 调用） |
| **可控性** | 高（函数定义即约束） | 中（依赖提示词约束，可能跑偏） |

---

## 三、层级关系：它们是不同层级的东西

一个常见的误解是把 Function Call 和 ReAct 当作互斥的选择。实际上它们是**互补关系**：

```
                    ┌──────────────────────────────┐
                    │         ReAct 框架            │
                    │  Thought → Action → Observe   │
                    │     ↑_________↓_______________│
                    │        循环迭代               │
                    └──────────┬───────────────────┘
                               │
                    在 Action 步骤中，
                    可以用 Function Call 来触发工具
                               │
                    ┌──────────▼───────────────────┐
                    │     Function Call 机制        │
                    │  模型输出 tool_calls JSON     │
                    │  外部执行 → 返回结果          │
                    └──────────────────────────────┘
```

- **Function Call** 是 OpenAI/各大模型厂商提供的**模型能力**——模型能输出结构化的函数调用
- **ReAct** 是一种**提示词工程/编排策略**——让模型按 Thought→Action→Observation 循环推理
- **它们可以组合使用**：ReAct 的 Action 步骤，可以借助 Function Call 来精确触发工具

---

## 四、应用场景

### Function Call 适用场景

| 场景 | 说明 |
|------|------|
| **简单工具增强** | 用户问天气 → 调天气 API → 返回。一次性调用，不需要多步推理 |
| **确定性操作** | "帮我把这个会议加到日历" → 直接调 create_event 函数 |
| **低延迟要求** | 客服机器人、实时助手等场景，每多一轮循环都增加用户等待时间 |
| **安全性敏感场景** | 银行转账、权限修改——函数定义的 parameters 有严格 schema 约束 |
| **多模态/富客户端操作** | "把图片调亮一点" → `image_adjust(brightness: +20)` |

### ReAct 适用场景

| 场景 | 说明 |
|------|------|
| **复杂多步推理** | "分析这家公司过去三年的财务数据，判断是否值得投资" |
| **信息检索 + 综合** | "DeepSeek 和 GPT-4 在代码能力上谁更强？" → 搜索 → 对比 → 分析 |
| **结果依赖的动态调整** | "帮我订明天去上海的机票，要最便宜的" → 查航班 → 调整条件 → 确认 |
| **需要可解释性** | 医疗诊断辅助、法律分析——Thought 步骤让用户看到推理依据 |
| **工具链串联** | 查数据库 → 结果异常 → 查日志 → 定位 bug → 给修复建议 |

---

## 五、现代实践：两者结合

在实际的 Agent 开发中（如 LangChain 的 AgentExecutor），最常见的模式是：

```
┌────────────────────────────────────────────┐
│              AgentExecutor                  │
│  实现 ReAct 循环：                          │
│                                             │
│  while (not finished) {                    │
│    thought = llm.reason(history);           │
│    action = llm.decide_tool(thought);       │ ← 这一步用 Function Call
│    observation = execute_tool(action);      │
│    history.push(thought, action, observation)│
│  }                                          │
│  return llm.generate_final_answer(history); │
└────────────────────────────────────────────┘
```

**LangChain 中的体现**：
- `AgentExecutor` 实现了 ReAct 循环逻辑
- 内部的 `tool_calling` 机制就是借助模型的 Function Call 能力
- `createReactAgent` 等封装把两者整合在一起

---

## 六、选择决策树

```
需要调用外部工具吗？
├── 否 → 直接用普通 LLM 对话
└── 是 → 任务需要多少步？
    ├── 1 步（查天气、设闹钟、翻译）
    │   └── 用纯 Function Call，低延迟、高可靠
    └── 多步且结果相互依赖
        ├── 步骤固定 → 用 Chain/Workflow 编排
        └── 步骤不固定 → 用 ReAct + Function Call 组合
            └── Agent 自主规划路径
```

---

## 七、直观类比

| | Function Call | ReAct |
|---|---|---|
| **类比** | 遥控器上的**单个按钮** | 一个会**先想再按**的人 |
| 按"音量+" | 直接执行，音量 +1 | 先想"现在太吵了，降一点"，再按 |
| **优势** | 快、准 | 灵活、能处理复杂情况 |
| **代价** | 不会自己判断该不该调 | 每次都要想一下，慢了 |

---

## 八、总结

> **Function Call 解决的是"模型怎么精确调用工具"的问题，ReAct 解决的是"模型怎么规划多步行动来解决复杂问题"的问题。它们是互补关系，不是替代关系。**

在实际开发中：
- 简单场景直接用 Function Call，追求低延迟和高可靠
- 复杂场景用 ReAct + Function Call 组合，让 Agent 自主规划和执行
- 两者在现代 Agent 框架（如 LangChain）中已经深度整合
