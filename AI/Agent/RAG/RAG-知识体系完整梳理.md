# RAG 检索增强生成 — 知识体系完整梳理

> 适用读者：正在系统学习 Agent 开发的 Node.js/TypeScript 全栈工程师  
> 技术栈关联：LangChain.js · RAG · Agent · 向量数据库 · 宝塔面板部署

---

## 一、RAG 是什么

**RAG（Retrieval-Augmented Generation，检索增强生成）** 是一种将**信息检索**与**大语言模型（LLM）生成**相结合的技术架构。

### 1.1 一句话理解

> 在让 LLM 回答问题之前，**先从外部知识库中检索出最相关的文档片段**，把这些片段作为"参考资料"一起塞进 Prompt，让 LLM 基于这些资料来生成答案。

### 1.2 类比理解

| 场景 | 类比 |
|------|------|
| 闭卷考试 | 纯 LLM — 全靠训练时记住的知识，可能过时、可能幻觉 |
| 开卷考试 | RAG — 给你一堆参考书，先翻到相关章节，再结合内容作答 |

### 1.3 为什么要用 RAG？

| 痛点 | RAG 如何解决 |
|------|-------------|
| **知识截止日期** | LLM 训练数据有截止时间，RAG 可以检索最新文档 |
| **幻觉问题** | 检索到的真实文档作为"锚点"，大幅减少模型编造 |
| **私有知识** | 企业内部文档、产品手册等私有数据，LLM 没学过 |
| **可解释性** | 可以告诉用户"答案来自哪篇文档"，支持溯源 |
| **成本** | 不用对 LLM 全量微调（Fine-tuning），只需维护向量库 |

---

## 二、RAG 核心架构（三层拆解）

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG 完整流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  【离线阶段 — 索引构建】                                          │
│                                                                  │
│   原始文档 ──→ 文档分割(Chunking) ──→ Embedding 向量化            │
│                                          │                       │
│                                          ▼                       │
│                                    向量数据库存储                  │
│                                   (Chroma / Pinecone / Milvus)    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  【在线阶段 — 检索 + 生成】                                       │
│                                                                  │
│   用户问题 ──→ Embedding 向量化 ──→ 向量相似度检索 ──→ Top-K 文档  │
│                                                                  │
│   原始问题 + 检索到的文档片段 ──→ 拼接 Prompt ──→ LLM 生成答案     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 离线阶段：索引构建（Indexing）

这是 RAG 的**准备工作**，只需执行一次（或定期更新）。

**步骤：**

1. **文档加载（Document Loader）**  
   从 PDF、Markdown、数据库、网页等来源加载原始文本。

2. **文档分割（Chunking / Text Splitting）**  
   将长文档切分为小块（Chunk），因为：
   - Embedding 模型有最大 token 限制（通常 512~8192 tokens）
   - 小块更精准：检索时匹配到的片段更聚焦
   - **关键参数：chunk_size（块大小）和 chunk_overlap（重叠量）**

3. **向量化（Embedding）**  
   将每个 Chunk 通过 Embedding 模型（如 OpenAI text-embedding-3-small、BGE、Jina）转换为高维向量（如 1536 维）。

4. **向量入库（Vector Store）**  
   将向量 + 原始文本 + 元数据存入向量数据库。

### 2.2 在线阶段：检索 + 生成（Retrieval & Generation）

**步骤：**

1. **查询向量化**：将用户问题通过**同一个 Embedding 模型**转为向量
2. **相似度检索**：在向量数据库中执行 **ANN（近似最近邻）** 搜索，返回 Top-K 个最相似的 Chunk
3. **Prompt 拼接**：将检索到的文档片段 + 原始问题组装成 Prompt 模板
4. **LLM 生成**：LLM 基于提供的上下文生成答案

### 2.3 典型 Prompt 模板

```text
你是一个专业的AI助手。请仅基于以下提供的参考资料回答用户问题。
如果参考资料中没有相关信息，请如实说"未找到相关信息"，不要编造。

【参考资料】
{context}

【用户问题】
{question}

【回答】
```

---

## 三、核心知识点深度拆解

### 3.1 文档分割策略（高频考点 ⭐⭐⭐）

| 策略 | 原理 | 适用场景 | 优缺点 |
|------|------|---------|--------|
| **固定长度分割** | 按字符数/token数切分 | 通用场景 | 简单，但可能切断语义 |
| **基于分隔符** | 按 `\n`、`。`、段落等切分 | 结构化文档 | 语义更完整 |
| **递归分割** | 按优先级分隔符递归切分 | LangChain 默认 | 兼顾长度和语义 |
| **语义分割** | 用模型判断语义边界 | 高质量要求 | 效果好但慢且贵 |
| **父子文档** | 小Chunk检索 + 大Chunk生成 | 需要上下文 | 检索精准+生成有上下文 |

**核心概念：Chunk Size 与 Chunk Overlap**

```
Chunk Size = 500 tokens, Overlap = 50 tokens

文档: [A B C D E F G H I J K L M N O P Q R S T]

Chunk1: [A B C D E F G H I J]           ← 500 tokens
Chunk2:       [H I J K L M N O P Q R S]  ← 重叠 H I J（50 tokens）
Chunk3:             [P Q R S T ...]
```

**Overlap 的作用**：防止关键信息正好落在 Chunk 边界上被切断。

---

### 3.2 Embedding 模型选型（考点 ⭐⭐⭐）

| 模型 | 维度 | 特点 | 中文支持 |
|------|------|------|---------|
| OpenAI text-embedding-3-small | 512/1536 | 性价比高，可调维度 | ✅ |
| OpenAI text-embedding-3-large | 256/1024/3072 | 效果最好 | ✅ |
| BGE-M3 (BAAI) | 1024 | 开源，多语言，可本地部署 | ✅✅ |
| Jina Embeddings v3 | 1024 | 多语言，支持任务特定 | ✅✅ |
| Cohere Embed v3 | 1024 | 多语言，分类/检索模式 | ✅ |
| text2vec-large-chinese | 1024 | 中文专用，开源 | ✅✅✅ |

**选型原则：**
- 预算充足 + 快速上线 → OpenAI
- 数据隐私 + 本地部署 → BGE / Jina / text2vec
- 中文为主 → BGE-M3 或 text2vec-large-chinese

---

### 3.3 向量数据库对比（考点 ⭐⭐）

| 数据库 | 类型 | 部署难度 | 适用规模 | 特点 |
|--------|------|---------|---------|------|
| **Chroma** | 嵌入式 | ⭐ 极简 | 小/原型 | LangChain 原生支持，本地文件存储 |
| **FAISS** | 库 | ⭐⭐ | 中 | Meta 出品，纯向量检索，速度快 |
| **Milvus** | 分布式 | ⭐⭐⭐⭐ | 大/超大 | 云原生，支持混合查询 |
| **Pinecone** | 云服务 | ⭐ | 中/大 | 全托管，免运维，收费 |
| **Weaviate** | 独立服务 | ⭐⭐⭐ | 中/大 | GraphQL 接口，混合检索 |
| **Qdrant** | 独立服务 | ⭐⭐ | 中 | Rust 实现，性能优秀 |
| **pgvector** | PostgreSQL扩展 | ⭐⭐ | 中 | 和业务库共存，SQL 查询 |

**推荐路径：** 原型用 Chroma → 生产小规模用 Qdrant/pgvector → 大规模用 Milvus/Pinecone

---

### 3.4 相似度度量（考点 ⭐⭐）

| 度量方式 | 公式/原理 | 适用场景 |
|---------|----------|---------|
| **余弦相似度** | cos(θ) = A·B / (\|A\|·\|B\|) | 最常用，关注方向不关注长度 |
| **欧氏距离** | √Σ(Ai - Bi)² | 关注绝对距离 |
| **点积** | A·B | 向量已归一化时等价余弦 |

> 实际使用：Embedding 模型通常输出归一化向量，此时**点积 = 余弦相似度**，计算最快。

---

### 3.5 检索策略进阶（高级考点 ⭐⭐⭐）

#### 3.5.1 基础检索
- **稀疏检索（关键词）**：BM25、TF-IDF，基于词频，精确匹配
- **稠密检索（语义）**：Embedding 向量，语义匹配

#### 3.5.2 混合检索（Hybrid Search）
结合稀疏检索 + 稠密检索，取两者之长：
- 关键词匹配（BM25）→ 精确命中
- 语义匹配（Embedding）→ 同义改写也能找到
- 用 RRF（Reciprocal Rank Fusion）融合排序

#### 3.5.3 多阶段检索（Re-ranking）
```
初检（快速，Top-100）→ 重排序（精准，Top-5）→ 送入 LLM
```
- 初检：向量检索快速召回候选
- 重排序：用 Cross-Encoder 模型（如 Cohere Rerank、BGE-Reranker）精细打分

#### 3.5.4 查询增强
- **Multi-Query**：把一个用户问题改写为多个不同角度的查询，分别检索后合并
- **Query Decomposition**：把复杂问题拆成子问题，逐个检索和回答
- **HyDE**：先让 LLM 生成假设性答案，再拿这个答案去做向量检索

#### 3.5.5 自查询检索（Self-Querying）
在语义检索的同时，LLM 自动提取元数据过滤条件。
> 例：用户问"2024年发布的关于React的文档"  
> → LLM 提取：year=2024, topic="React" → 向量检索 + 元数据过滤

---

## 四、RAG 评测指标（考点 ⭐⭐）

| 指标 | 含义 | 说明 |
|------|------|------|
| **Hit Rate（命中率）** | Top-K 结果中是否包含正确答案 | 宽松指标 |
| **MRR（Mean Reciprocal Rank）** | 第一个正确答案的平均排名倒数 | MRR=1/rank，越靠前越好 |
| **NDCG** | 考虑排序位置加权的归一化指标 | 排序质量 |
| **Faithfulness（忠实度）** | 答案是否完全基于检索到的上下文 | 不编造 |
| **Answer Relevance** | 答案与问题的相关程度 | 不跑题 |
| **Context Precision** | 检索到的上下文中，真正有用的占比 | 检索精度 |
| **Context Recall** | 答案需要的上下文是否被检索到 | 检索召回 |

---

## 五、TypeScript 实战 — LangChain.js 完整 RAG 代码

> 结合你的技术栈偏好，以下使用 TypeScript + LangChain.js

### 5.1 安装依赖

```bash
npm install @langchain/core @langchain/openai @langchain/community
npm install langchain chromadb
```

### 5.2 文档加载与分割

```typescript
import { TextLoader } from "langchain/document_loaders/fs/text";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

// 1. 加载文档
const loader = new TextLoader("./docs/product-manual.txt");
const docs = await loader.load();
console.log(`加载了 ${docs.length} 篇文档`);

// 2. 文档分割
const textSplitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,        // 每块 500 字符
  chunkOverlap: 50,      // 重叠 50 字符
  separators: ["\n\n", "\n", "。", "，", " ", ""]  // 递归分割优先级
});

const splitDocs = await textSplitter.splitDocuments(docs);
console.log(`分割为 ${splitDocs.length} 个 Chunk`);
```

### 5.3 向量化并存入 Chroma

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";
import { Chroma } from "@langchain/community/vectorstores/chroma";

// 3. 初始化 Embedding 模型
const embeddings = new OpenAIEmbeddings({
  modelName: "text-embedding-3-small",
  dimensions: 512,  // 可选，降低维度以节省空间
});

// 4. 向量化并存入 Chroma
const vectorStore = await Chroma.fromDocuments(
  splitDocs,
  embeddings,
  {
    collectionName: "product-docs",
    url: "http://localhost:8000",  // Chroma 服务地址
  }
);

console.log("向量索引构建完成！");
```

### 5.4 检索链（RetrievalQA Chain）

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { createRetrievalChain } from "langchain/chains/retrieval";
import { createStuffDocumentsChain } from "langchain/chains/combine_documents";
import { ChatPromptTemplate } from "@langchain/core/prompts";

// 5. 初始化 LLM
const llm = new ChatOpenAI({
  modelName: "gpt-4o",
  temperature: 0.3,  // RAG 场景建议低温，减少幻觉
});

// 6. 定义 Prompt 模板
const prompt = ChatPromptTemplate.fromTemplate(`
你是一个专业的产品知识助手。请**仅基于**以下参考资料回答用户问题。
如果参考资料中没有相关信息，请明确说"根据现有资料，暂未找到相关信息"。

【参考资料】
{context}

【用户问题】
{input}

【回答】
`);

// 7. 创建组合链
const combineDocsChain = await createStuffDocumentsChain({
  llm,
  prompt,
});

const retrievalChain = await createRetrievalChain({
  retriever: vectorStore.asRetriever({ k: 4 }),  // 每次检索 Top-4
  combineDocsChain,
});

// 8. 提问
const result = await retrievalChain.invoke({
  input: "产品A的保修期是多久？",
});

console.log("答案:", result.answer);
console.log("来源文档:", result.context);
```

### 5.5 带来源引用的完整服务

```typescript
interface RAGResponse {
  answer: string;
  sources: Array<{
    content: string;
    page?: number;
    score: number;
  }>;
}

async function askWithSources(question: string): Promise<RAGResponse> {
  // 检索带相似度分数
  const retriever = vectorStore.asRetriever({
    k: 4,
    searchType: "similarity",  // 或 "mmr" (最大边际相关性，增加多样性)
  });

  const relevantDocs = await retriever.invoke(question);
  
  const context = relevantDocs.map(doc => doc.pageContent).join("\n\n---\n\n");

  const response = await llm.invoke([
    ["system", `你是一个专业助手。仅基于提供的资料回答。如果不知道就说不知道。`],
    ["human", `参考资料:\n${context}\n\n问题: ${question}\n\n回答:`]
  ]);

  return {
    answer: response.content as string,
    sources: relevantDocs.map((doc, i) => ({
      content: doc.pageContent.substring(0, 200) + "...",
      page: doc.metadata.loc?.pageNumber,
      score: doc.metadata.score || 0,
    })),
  };
}
```

---

## 六、RAG 常见问题与优化（面试高频 ⭐⭐⭐）

### 6.1 检索质量差

| 问题现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 搜到无关内容 | Embedding 模型不匹配 | 换领域适配模型 / Fine-tune Embedding |
| 关键信息搜不到 | Chunk 太大或太小 | 调整 Chunk Size，尝试 256/512/1024 |
| 精确词匹配失败 | 纯语义检索的局限 | 加入 BM25 做混合检索 |
| 多跳推理问题 | 单个 Chunk 信息不足 | 知识图谱增强 / 迭代检索 |

### 6.2 答案质量问题

| 问题现象 | 解决方案 |
|---------|---------|
| **幻觉** | 强化 Prompt 约束（"不知道就说不知道"）、降低 temperature、增加参考资料权重 |
| **答案不完整** | 增加 Top-K、使用 Map-Reduce 或 Refine 链处理多文档 |
| **上下文超长** | 使用 Re-ranking 精简、Summarization 压缩中间上下文 |
| **引用错误** | 要求 LLM 逐句标注来源、使用 Citation 专用 Prompt |

### 6.3 Lost in the Middle（中间丢失）

> LLM 对长上下文的**开头和结尾**关注更多，**中间部分容易被忽略**。

**解决方案：**
- Re-ranking 后把最相关的 Chunk 放在开头和结尾
- 控制上下文总长度，不要塞太多 Chunk

### 6.4 多模态 RAG

支持图片、表格等非文本内容的 RAG：
- 用多模态 Embedding（如 CLIP）将图片向量化
- 检索时文本和图片一起召回
- 用多模态 LLM（如 GPT-4V）生成答案

---

## 七、RAG vs 微调（Fine-tuning）对比（考点 ⭐⭐）

| 维度 | RAG | 微调 |
|------|-----|------|
| **知识更新** | 更新向量库即可，实时生效 | 需要重新训练，周期长 |
| **数据需求** | 无需训练数据，只需文档 | 需要高质量 Q&A 数据集 |
| **成本** | 向量库存储 + Embedding API | GPU 训练成本高 |
| **可解释性** | 可以溯源到具体文档 | 黑盒，难以溯源 |
| **幻觉控制** | 有文档锚点，幻觉较少 | 仍可能产生幻觉 |
| **私有知识** | ✅ 天然适合 | ✅ 但成本高 |
| **风格/角色定制** | 通过 Prompt 控制 | ✅ 更深度的风格学习 |
| **推理速度** | 多一次检索延迟 | 纯生成，更快 |

> **最佳实践：RAG + 微调组合使用** — RAG 负责知识更新，微调负责风格和指令跟随。

---

## 八、生产部署考虑（结合你的宝塔面板环境）

### 8.1 推荐架构

```
用户 → Nginx (宝塔) → Node.js API (Express/Fastify)
                           ├──→ LLM API (OpenAI / 本地 vLLM)
                           ├──→ Embedding 服务
                           └──→ 向量数据库 (Qdrant Docker)
```

### 8.2 Docker Compose 部署向量数据库

```yaml
# docker-compose.yml (在宝塔面板的 Docker 管理中部署)
version: "3.8"
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"    # HTTP API
      - "6334:6334"    # gRPC
    volumes:
      - ./qdrant_data:/qdrant/storage
    restart: always

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - ./chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
    restart: always
```

### 8.3 宝塔面板部署检查清单

- [ ] Docker 已安装（宝塔软件商店 → Docker 管理器）
- [ ] 向量数据库容器正常运行
- [ ] Node.js 项目通过 PM2 管理器运行
- [ ] Nginx 反向代理配置（API 路由 + WebSocket 支持）
- [ ] SSL 证书（宝塔一键申请 Let's Encrypt）
- [ ] 环境变量管理（API Key 等敏感信息）
- [ ] 日志监控（宝塔日志管理 + PM2 日志）

---

## 九、考点总结（面试/认证速查）

### 9.1 名词解释题

| 术语 | 一句话解释 |
|------|----------|
| **RAG** | 检索 + 生成，给 LLM 外挂知识库 |
| **Embedding** | 将文本映射为高维向量，语义相近的文本向量距离近 |
| **Chunk** | 文档分割后的小块，检索的基本单位 |
| **Vector Store** | 存储和检索向量的专用数据库 |
| **Re-ranking** | 对初检结果用更精准的模型重新排序 |
| **Hybrid Search** | 关键词检索 + 语义检索的融合 |
| **Hallucination** | 模型生成的内容与事实不符（幻觉） |
| **MMR** | 最大边际相关性，平衡检索结果的相关性和多样性 |

### 9.2 简答题高频考点

1. **RAG 的基本流程是什么？**  
   文档加载 → 分割 → Embedding → 向量入库 → 查询向量化 → 相似度检索 → Prompt 拼接 → LLM 生成

2. **Chunk Size 太大或太小有什么影响？**  
   太大：检索粒度粗，无关信息多，可能超 token 限制  
   太小：语义不完整，关键信息被切断

3. **如何处理 RAG 中的幻觉问题？**  
   - Prompt 约束（明确"不知道就说不知道"）
   - 降低 temperature
   - Re-ranking 确保上下文质量
   - 要求模型逐句标注引用来源

4. **RAG 和微调的区别是什么？**  
   见上文第七章对比表

### 9.3 场景设计题

> **题目：为一个企业内部的 10000+ 份 PDF 技术文档构建 RAG 问答系统，请设计方案。**

**答题框架：**

1. **文档处理**：PDF 解析（PyMuPDF/unstructured） → 按章节分割（保留层级结构）→ Chunk Size 512~1024，Overlap 100
2. **向量化**：选 BGE-M3（开源、中文好、可本地部署），1024 维
3. **向量库**：Milvus（支持 10 万+文档规模，分布式）或 Pinecone（免运维）
4. **检索策略**：混合检索（BM25 + Embedding）+ Re-ranking（BGE-Reranker）
5. **LLM**：GPT-4o 或本地 Qwen 模型
6. **更新机制**：新增/修改文档 → 增量 Embedding → 更新向量库
7. **监控**：记录检索命中率、答案质量评分、用户反馈

---

## 十、进阶方向

掌握了基础 RAG 后，可以进一步学习：

- **Agentic RAG**：Agent 自主判断是否需要检索、检索什么、如何检索（结合你正在学的 Agent 开发）
- **Graph RAG**：用知识图谱增强 RAG，处理多跳推理
- **Self-RAG**：LLM 自我反思，判断检索结果是否足够，不够则再次检索
- **Corrective RAG**：检索后评估文档相关性，不相关则自动改写查询重新检索
- **多模态 RAG**：同时处理文本 + 图片 + 表格

---

> 📅 文档生成时间：2026年7月  
> 🔧 技术栈：Node.js / TypeScript / LangChain.js / Chroma / Qdrant / 宝塔面板  
> 📚 关联学习：Agent 开发标准流程 · LangChain 框架 · 向量数据库
