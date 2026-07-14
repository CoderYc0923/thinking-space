# Top-K 完整知识梳理

> 关联文档：RAG 知识体系完整梳理 · Agent 开发学习路径  
> 技术栈：Node.js / TypeScript / LangChain.js

---

## 一、Top-K 是什么

**Top-K** 是信息检索和机器学习中最基础的操作之一：

> 从一个排序后的候选集中，**选取得分最高（或距离最近）的前 K 个结果**，丢弃其余。

### 1.1 为什么需要 Top-K？

| 原因 | 说明 |
|------|------|
| **效率** | 不需要全部候选，K 个足够 |
| **质量** | 低分候选通常是噪声，丢弃可提升信噪比 |
| **成本** | 传递给下游（LLM、用户）的数据越少，处理成本越低 |
| **上下文限制** | LLM 有最大 token 数，必须截断 |

### 1.2 Top-K 的普适性

Top-K 不只是 RAG 的概念，它在以下领域都是核心操作：

```
信息检索     → 返回最相关的 K 篇文档
推荐系统     → 推荐评分最高的 K 个商品
LLM 生成     → 从概率最高的 K 个 token 中采样
分类任务     → 输出概率最高的 K 个类别
向量搜索     → 返回距离最近的 K 个向量
数据库查询   → SELECT ... LIMIT K（本质也是 Top-K）
```

---

## 二、Top-K 在 RAG 检索中的完整解析

### 2.1 检索流程中的位置

```
                         向量数据库
                             │
用户问题 → Embedding → 相似度计算 → 全部候选（按得分降序）
                             │
                    ┌────────┘
                    ▼
              Top-K 截断（只取前 K 个）
                    │
                    ▼
              拼接 Prompt → LLM 生成答案
```

### 2.2 相似度得分与排序

检索时，向量数据库对每个候选 Chunk 计算相似度：

```
候选 Chunk A → 相似度 0.95  ← 第1名 ✓ 入选
候选 Chunk B → 相似度 0.87  ← 第2名 ✓ 入选
候选 Chunk C → 相似度 0.72  ← 第3名 ✓ 入选 (K=3)
候选 Chunk D → 相似度 0.68  ← 第4名 ✗ 丢弃
候选 Chunk E → 相似度 0.31  ← 第5名 ✗ 丢弃
...
```

### 2.3 K 值的艺术：选多大？

**K 值的选择直接影响 RAG 系统质量**，这是工程中的核心调参点。

| K 值 | 总 Token 估算 | 效果特征 | 典型场景 |
|------|-------------|---------|---------|
| **1** | ~500 tokens | 极聚焦，但极易遗漏关键信息 | 简单事实查询 |
| **2~3** | ~1K tokens | 平衡点，覆盖主要信息面 | 产品参数、政策条款 |
| **4~5** | ~2K tokens | **最常用**，覆盖面与噪声比均衡 | 通用 RAG 问答 |
| **6~10** | ~3~5K tokens | 覆盖面广，噪声风险上升 | 复杂多文档推理 |
| **10~20** | ~5K+ tokens | 初检阶段，需配合 Re-ranking | 多阶段检索模式 |

### 2.4 K 值与 Chunk Size 的联动关系

> **核心公式**：`总上下文长度 ≈ Chunk Size × Top-K`

```
场景 A：Chunk Size = 256 tokens,  Top-K = 8  → 总上下文 ≈ 2048 tokens
场景 B：Chunk Size = 1024 tokens, Top-K = 3  → 总上下文 ≈ 3072 tokens
场景 C：Chunk Size = 512 tokens,  Top-K = 5  → 总上下文 ≈ 2560 tokens  ← 推荐
```

**调参原则**：
- Chunk 小 → K 可以大（小块语义碎片化，需要更多块拼出完整信息）
- Chunk 大 → K 应该小（大块本身信息完整，太多块会超 token 限制）
- 目标：总上下文控制在 **2K~4K tokens**，不要超过 LLM 的有效关注范围

### 2.5 K 值过大的问题

| 问题 | 机制 |
|------|------|
| **上下文超限** | 超过 LLM 最大 token 数，必须截断或报错 |
| **Lost in the Middle** | LLM 对长上下文中间部分关注度显著下降 |
| **噪声干扰** | 低相关性文档分散模型注意力，答案质量下降 |
| **成本飙升** | 更多 input token → 更高的 API 费用 |
| **延迟增加** | 更多上下文 → LLM 推理时间线性增长 |

### 2.6 K 值过小的问题

| 问题 | 机制 |
|------|------|
| **信息遗漏** | 关键答案在第 K+1 个文档，被截断了 |
| **答案不完整** | 多文档拼接才能回答的问题，缺少必要片段 |
| **无法交叉验证** | 只有一个来源，无法判断信息可信度 |

### 2.7 最佳实践：两阶段 Top-K

生产环境中最推荐的模式：

```
第一阶段：粗检 Top-K₁（大 K，快速召回）
    ↓
第二阶段：精排 Top-K₂（小 K，精准筛选）
    ↓
送入 LLM
```

**典型参数**：
- K₁ = 20（初检，用向量相似度快速召回）
- Re-ranking（用 Cross-Encoder 模型对 20 个候选重打分）
- K₂ = 3~5（取重排序后的前几名送入 LLM）

---

## 三、TypeScript / LangChain.js 实战代码

### 3.1 基础：设置 Top-K

```typescript
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings({
  modelName: "text-embedding-3-small",
});

const vectorStore = await Chroma.fromExistingCollection(embeddings, {
  collectionName: "knowledge-base",
});

// ═══ 方法1：asRetriever 直接设 k ═══
const retriever = vectorStore.asRetriever({
  k: 4,                        // ← Top-K
  searchType: "similarity",    // "similarity" | "mmr"
});

const docs = await retriever.invoke("什么是 RAG？");
console.log(`检索到 ${docs.length} 个文档`);  // 4
```

### 3.2 使用 MMR 模式（兼顾多样性）

```typescript
// MMR (最大边际相关性)：在 Top-K 基础上增加多样性约束
const mmrRetriever = vectorStore.asRetriever({
  k: 5,
  searchType: "mmr",
  searchKwargs: {
    fetchK: 20,     // 先从库中取 20 个候选
    lambda: 0.5,    // 0=最大多样性, 1=最大相关性
  },
});

// MMR 工作流：
// 1. 检索 20 个候选 (fetchK)
// 2. 贪心选择 5 个 (k)：每次选与问题最相关、且与已选文档最不相似的
```

### 3.3 带相似度分数的检索

```typescript
// 查看每个文档的相似度得分
const retriever = vectorStore.asRetriever({ k: 4 });
const docs = await retriever.invoke("产品定价策略");

docs.forEach((doc, i) => {
  console.log(`[Top-${i + 1}] 相似度: ${doc.metadata.score?.toFixed(4)}`);
  console.log(`内容: ${doc.pageContent.substring(0, 100)}...\n`);
});
```

### 3.4 动态调整 Top-K

```typescript
class AdaptiveRetriever {
  constructor(private vectorStore: VectorStore) {}

  async retrieve(question: string): Promise<Document[]> {
    // 根据问题长度动态调整 K
    const questionLength = question.length;
    let k: number;

    if (questionLength < 20) {
      k = 3;  // 短问题 → 可能简单，少检索
    } else if (questionLength < 100) {
      k = 5;  // 中等问题 → 标准 K
    } else {
      k = 8;  // 长问题 → 可能复杂，多检索
    }

    const retriever = this.vectorStore.asRetriever({ k });
    return retriever.invoke(question);
  }
}
```

### 3.5 两阶段检索（Top-K + Re-ranking）完整实现

```typescript
interface RetrievalResult {
  content: string;
  score: number;
  rerankScore?: number;
}

async function twoStageRetrieval(
  question: string,
  vectorStore: VectorStore
): Promise<RetrievalResult[]> {

  // ═══ 阶段1：粗检 Top-20 ═══
  const retriever = vectorStore.asRetriever({ k: 20 });
  const candidates = await retriever.invoke(question);

  console.log(`初检: ${candidates.length} 个候选`);

  // ═══ 阶段2：重排序 Top-5（使用 Cohere Rerank API 示例） ═══
  // 实际使用时需要安装 @cohere-ai/cohere
  // const cohere = new CohereClient({ token: process.env.COHERE_API_KEY });
  // const rerankResult = await cohere.rerank({
  //   query: question,
  //   documents: candidates.map(d => d.pageContent),
  //   topN: 5,              // ← 最终的 Top-K₂
  //   model: "rerank-v3.5",
  // });

  // 简化示意（实际需替换为真实 Rerank API）
  const reranked = candidates
    .map((doc, i) => ({
      content: doc.pageContent,
      score: (doc as any).metadata?.score || 0,
      rerankScore: 1 - i * 0.03,  // 模拟重排序得分
    }))
    .sort((a, b) => b.rerankScore! - a.rerankScore!)
    .slice(0, 5);  // ← 最终取 Top-5

  console.log(`重排序后: ${reranked.length} 个文档送入 LLM`);

  return reranked;
}
```

### 3.6 在 RetrievalQA Chain 中使用

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { createRetrievalChain } from "langchain/chains/retrieval";
import { createStuffDocumentsChain } from "langchain/chains/combine_documents";
import { ChatPromptTemplate } from "@langchain/core/prompts";

const llm = new ChatOpenAI({ modelName: "gpt-4o", temperature: 0.3 });

const prompt = ChatPromptTemplate.fromTemplate(`
基于以下参考资料回答问题。如果无法回答，请明确说明。

参考资料：
{context}

问题：{input}
`);

const combineDocsChain = await createStuffDocumentsChain({ llm, prompt });

const chain = await createRetrievalChain({
  retriever: vectorStore.asRetriever({ k: 4 }),  // ← Top-K = 4
  combineDocsChain,
});

const result = await chain.invoke({ input: "公司年假政策是什么？" });
console.log(result.answer);
```

---

## 四、Top-K 在其他 AI 场景的含义

### 4.1 LLM 文本生成中的 Top-K 采样

在 LLM 逐个生成 token 时，Top-K 是一种**解码策略**，控制生成的随机性和质量。

```
LLM 输出 logits → Softmax → 概率分布（50000 个 token 各有一个概率）
                                   │
                            排序，取 Top-K 个
                                   │
                            重新归一化 → 从中随机采样
```

#### 4.1.1 Top-K 生成示例

假设 LLM 在生成下一个 token，候选词概率为：

| Token | 概率 | K=3 时 | K=6 时 |
|-------|------|--------|--------|
| "学习" | 0.40 | ✅ 入选 | ✅ 入选 |
| "研究" | 0.25 | ✅ 入选 | ✅ 入选 |
| "了解" | 0.15 | ✅ 入选 | ✅ 入选 |
| "分析" | 0.08 | ✗ 丢弃 | ✅ 入选 |
| "掌握" | 0.06 | ✗ 丢弃 | ✅ 入选 |
| "阅读" | 0.04 | ✗ 丢弃 | ✅ 入选 |
| ... | ... | ✗ | ✗ |

- K=3：只从 {学习, 研究, 了解} 中采样 → 输出更可控、确定性更高
- K=6：从 6 个候选中采样 → 更多样化，但也可能输出不合适的词

#### 4.1.2 Top-K vs Top-P vs Temperature

| 参数 | 原理 | 效果 |
|------|------|------|
| **Top-K** | 固定取概率最高的 K 个 | K 大 → 多样；K 小 → 保守 |
| **Top-P** (Nucleus) | 动态取累计概率 ≥ P 的最小集合 | P=0.9 可能取 5 个也可能取 50 个 |
| **Temperature** | 在 Softmax 前缩放 logits | T<1 → 更确定；T>1 → 更随机 |

**实际使用**：OpenAI API 默认使用 Top-P（未暴露 Top-K）；开源模型（Llama、Qwen 等）常 Top-K + Top-P 组合使用。

#### 4.1.3 LangChain.js 中设置生成参数

```typescript
const llm = new ChatOpenAI({
  modelName: "gpt-4o",
  temperature: 0.7,
  // OpenAI API 不支持直接设 Top-K，但本地模型可以：
  // modelKwargs: {
  //   top_k: 50,
  //   top_p: 0.9,
  // }
});
```

### 4.2 推荐系统中的 Top-K

```
用户画像 + 商品库 → 召回（数千候选） → 粗排（数百） → 精排 → Top-K（K=10~100） → 展示
```

推荐系统的 Top-K 直接影响用户体验：
- K 太小 → 用户看不到足够选择
- K 太大 → 信息过载，用户决策困难

### 4.3 分类任务中的 Top-K Accuracy

评估指标：只要正确答案在模型预测的 Top-K 个类别中，就算对。

```
真实标签：猫
模型预测 Top-5：[狗, 猫, 老虎, 豹, 狼]
→ Top-1 Accuracy：✗（第一名是狗）
→ Top-5 Accuracy：✓（猫在前5名中）

ImageNet 常用 Top-5 Accuracy 作为指标，因为有些类别非常相似（如犬种）。
```

---

## 五、Top-K 的变体与进阶

### 5.1 MMR（最大边际相关性）

> MMR = Top-K 的多样性增强版

标准 Top-K 问题：选出的 K 个文档可能内容高度重复。

MMR 解决方式：贪心选择，每轮选一个既相关又与已选文档不相似的。

```
MMR 公式：
MMR = argmax[ λ × Sim(D, Q) - (1-λ) × max(Sim(D, Dj)) ]
                        ↑                        ↑
                   与问题的相关性          与已选文档的最大相似度
```

| λ 值 | 效果 |
|------|------|
| λ=1.0 | 退化为标准 Top-K（只关心相关性） |
| λ=0.7 | 推荐值，偏向相关性但保留一定多样性 |
| λ=0.0 | 完全多样性优先（不推荐） |

### 5.2 Top-K 与分页

在大规模检索中，需要分页获取结果：

```typescript
// 获取第 3 页，每页 10 条
const page = 3;
const pageSize = 10;

// 实际需要检索 (page × pageSize) 条，然后客户端分页
const retriever = vectorStore.asRetriever({ k: page * pageSize });
const allDocs = await retriever.invoke(question);

// 客户端切片
const pageDocs = allDocs.slice((page - 1) * pageSize, page * pageSize);
```

> ⚠️ 向量数据库通常不支持原生 offset 分页，需应用层实现。

### 5.3 多查询融合 Top-K

```typescript
// Multi-Query：把一个问题改写为多个版本，分别检索后合并 Top-K
async function multiQueryRetrieval(
  question: string,
  vectorStore: VectorStore,
  k: number = 3
): Promise<Document[]> {

  // 1. 用 LLM 生成多个查询变体
  const queryVariations = await generateQueryVariations(question, llm);
  // ["什么是RAG？", "RAG技术原理", "检索增强生成如何工作"]

  // 2. 每个变体检索 Top-K
  const allDocs: Document[] = [];
  for (const q of queryVariations) {
    const retriever = vectorStore.asRetriever({ k });
    const docs = await retriever.invoke(q);
    allDocs.push(...docs);
  }

  // 3. 去重 + 按最高分排序 + 最终 Top-K
  const unique = deduplicateByContent(allDocs);
  return unique.slice(0, k);
}
```

---

## 六、Top-K 常见问题与调优

### 6.1 如何确定最佳 K 值？

**方法：A/B 测试 + 指标评估**

```typescript
// 评估脚本示例
const kValues = [1, 2, 3, 5, 8, 10];
const testQuestions = loadTestSet();  // 标注好的测试问题集

for (const k of kValues) {
  const results = await evaluateRAG(testQuestions, vectorStore, k);
  console.log(`K=${k}: HitRate=${results.hitRate}, MRR=${results.mrr}`);
}

// 输出示例：
// K=1:  HitRate=0.62, MRR=0.62
// K=3:  HitRate=0.85, MRR=0.73
// K=5:  HitRate=0.91, MRR=0.71  ← HitRate 最高但 MRR 略降
// K=8:  HitRate=0.92, MRR=0.65  ← 边际收益递减
// K=10: HitRate=0.92, MRR=0.58  ← 噪声增加，MRR 下降明显
```

> 通常在 K=3~5 时找到性价比最优点。

### 6.2 评估指标速查

| 指标 | 含义 | 与 Top-K 的关系 |
|------|------|----------------|
| **Hit@K** | 正确答案是否在 Top-K 中 | K 越大，命中率越高 |
| **MRR** | 第一个正确答案排名的倒数 | K 太大会降低 MRR（噪声排前面） |
| **NDCG@K** | 考虑排序位置的归一化指标 | K 的选择直接影响分数 |
| **Recall@K** | Top-K 中相关文档数 / 总相关文档数 | K 越大召回越高 |
| **Precision@K** | Top-K 中相关文档数 / K | K 越大精度越低 |

### 6.3 调优决策树

```
答案经常不完整？ → 增大 K
答案出现幻觉？  → 检查 Prompt + 考虑 Re-ranking
上下文超 token？ → 减小 K 或减小 Chunk Size
检索速度慢？    → 减小 K，或用更快的索引类型
用户反馈内容重复？→ 使用 MMR 替代标准 Top-K
多文档推理需求？→ 增大 K + 配合 Map-Reduce 链
```

---

## 七、与已有知识体系的关联

| 关联知识点 | 关系 |
|-----------|------|
| **Chunk Size & Overlap** | Top-K × Chunk Size = 总上下文长度，需要联动调参 |
| **向量数据库选型** | 不同数据库的 Top-K 查询性能不同（Qdrant/Milvus 优于 Chroma） |
| **Re-ranking** | Top-K 是初检截断，Re-ranking 是精排优化 |
| **混合检索** | BM25 + Embedding 融合后，仍需 Top-K 截断 |
| **Agent 中的 Tool 选择** | Agent 也需要 Top-K 来限制调用的工具数量 |
| **Prompt 模板设计** | K 决定了 `{context}` 的大小，影响 Prompt 设计 |

---

## 八、考点速记卡

| 考点 | 答案 |
|------|------|
| Top-K 是什么？ | 从排序候选集中取前 K 个结果 |
| RAG 中 K 的推荐值？ | 3~5（通用场景） |
| K 太大有什么问题？ | 上下文过长、成本增加、Lost in the Middle、噪声干扰 |
| K 太小有什么问题？ | 信息遗漏、答案不完整 |
| 和 Chunk Size 的关系？ | 负相关：总上下文 = Chunk Size × K |
| MMR 和 Top-K 的区别？ | MMR 在 Top-K 基础上增加多样性约束 |
| 两阶段检索是什么？ | 初检 Top-K₁（大）→ Re-ranking → 精排 Top-K₂（小） |
| LLM 生成中的 Top-K？ | 只从概率最高的 K 个 token 中采样，控制生成多样性 |
| Top-K vs Top-P？ | Top-K 固定数量，Top-P 动态数量（累计概率） |
| 如何评估 K 的选择？ | Hit@K、MRR、NDCG@K、Recall@K、Precision@K |

---

> 📅 文档生成时间：2026年7月  
> 🔧 技术栈：Node.js / TypeScript / LangChain.js / RAG  
> 📚 关联文档：RAG 知识体系完整梳理
