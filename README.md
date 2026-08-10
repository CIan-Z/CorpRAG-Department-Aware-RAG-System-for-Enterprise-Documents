# 📚 企业知识库 RAG 系统

**CorpRAG：Department-Aware RAG System for Enterprise Documents**

基于 **LangChain + Streamlit + Chroma + DeepSeek** 构建的轻量级 RAG（检索增强生成）项目，支持文档上传、向量化存储、多轮对话问答，并可按部门筛选知识范围。

> ⚠️ 本项目仅用于学习 RAG 架构，所有上传文档均为示例内容，请勿用于生产环境。

---

## 功能一览

- **📤 知识库管理**
  - 支持 TXT、PDF、DOCX、Markdown 文件上传
  - 内容自动分段（可配置分段大小与重叠）
  - MD5 去重，避免重复入库
  - 按 **部门**（通用 / 技术部 / 人事部 / 财务部 / 市场部 / 运营部）标记文档
  - 已上传文档列表查看
- **🤖 智能问答**
  - 基于 Retrieval-Augmented Generation，结合知识库回答
  - **部门知识库过滤**：可选择只检索某一部门的文档
  - 多轮对话支持，历史记录持久化（文件存储）
  - 流式输出，体验更流畅
  - 清空对话历史功能
  - ![](C:\Users\Cian_Z\Desktop\Typora-image\屏幕截图 2026-08-10 095802.png)
  - ![](C:\Users\Cian_Z\Desktop\Typora-image\屏幕截图 2026-08-10 112729.png)

---

## 项目结构

```
RAG/
├── app_file_uploader.py      # Streamlit 知识库上传界面
├── app_qa.py                 # Streamlit 智能问答界面
├── config_data.py            # 全局配置参数（分段、向量库路径、API 等）
├── knowledge_base.py         # 知识库服务：文本分割、向量化、MD5 去重
├── vector_stores.py          # Chroma 向量存储与检索器封装（支持元数据过滤）
├── rag.py                    # RAG 核心链构建（检索->上下文拼接->生成）
├── file_history_store.py     # 对话历史文件存储（基于 session_id）
├── file_parser.py            # 文件解析工具（PDF、DOCX、TXT、MD）
├── md5.text                  # MD5 记录文件（自动生成）
├── chroma_db/                # Chroma 向量数据库持久化目录（自动生成）
└── chat_history/             # 对话历史文件目录（自动生成）
```

---

## 环境准备

- Python 3.8+
- 建议新建虚拟环境

**安装依赖**

```bash
pip install streamlit langchain langchain-chroma langchain-openai langchain-community pymupdf python-docx
```

> 注意：`chromadb` 由 `langchain-chroma` 自动安装，无需单独安装。

**配置 API Key**

系统使用了两个外部模型，需要设置环境变量：

- **智谱 Embedding**（文本向量化）
  在系统环境变量中添加 `ZHIPU_KEY`，值为你的智谱 API Key。
  或运行时临时设置：`set ZHIPU_KEY=your_key`（Windows）/ `export ZHIPU_KEY=your_key`（Mac/Linux）

- **DeepSeek 大模型**（对话生成）
  添加 `DEEPSEEK_API_KEY`，值为你的 DeepSeek API Key。
  可在 [DeepSeek 开放平台](https://platform.deepseek.com/usage)获取。

---

## 配置说明

所有可调参数集中在 `config_data.py`，可按需修改：

| 参数                    | 默认值                                       | 说明                                     |
| ----------------------- | -------------------------------------------- | ---------------------------------------- |
| `chunk_size`            | 1000                                         | 文本分段最大长度                         |
| `chunk_overlap`         | 100                                          | 相邻片段重叠长度                         |
| `max_split_char_number` | 1000                                         | 触发分段的内容长度阈值                   |
| `similarity_threshold`  | 1                                            | 检索返回的文档片段数量                   |
| `persist_directory`     | `./chroma_db`                                | 向量数据库保存路径                       |
| `collection_name`       | `rag`                                        | Chroma 集合名称                          |
| `md5_path`              | `./md5.text`                                 | MD5 去重记录文件                         |
| `session_config`        | `{"configurable": {"session_id": "C1an_Z"}}` | 对话历史标识，可改为动态值实现多用户隔离 |

---

## 如何运行

1. **上传知识库**

   ```bash
   streamlit run app_file_uploader.py
   ```

   在打开的网页中选择部门，上传文件（支持 TXT、PDF、DOCX、MD），系统会自动分段、向量化并存储。

2. **启动问答服务**
   打开另一个终端或停止上传服务后运行：

   ```bash
   streamlit run app_qa.py
   ```

   在页面侧边栏选择要查询的部门（或“全部”），输入问题即可获得基于已上传文档的回答。

> 💡 两个 App 需共享同一个 `chroma_db` 目录（默认配置即为同一目录），确保上传的文档能被问答服务检索。

---

## 常见问题

<details>
<summary><b>1. 上传文件后“知识库已有文档”列表不显示文件？</b></summary>


- 确保文件上传时未因 MD5 重复而被“跳过”。检查控制台输出，或查看 `md5.text` 文件是否记录了该文件的哈希。
- 尝试**刷新列表**按钮，或直接在页面底部查看自动显示的文档列表（每次刷新都会从 Chroma 读取）。
- 如果仍然不显示，请重启 Streamlit 服务，清除浏览器缓存（页面右上角 ☰ → Clear cache）。
  </details>

<details>
<summary><b>2. 选择部门后提问，回答似乎仍包含所有部门的内容？</b></summary>


- 确认 `rag.py` 中已添加 `set_filter` 方法，且 `VectorStoreService.get_retriever` 支持 `filter_dict` 参数。
- 检查上传文档时元数据中是否包含了 `department` 字段（在 `knowledge_base.py` 的 `upload_by_str` 中通过 `**kwargs` 传入并合并到了 `metadata`）。
- 如果问题依旧，可以在 `rag.py` 的 `__get_chain` 中临时打印 `filter_dict`，确认其在运行时非空。
  </details>

<details>
<summary><b>3. 报错 <code>'RagService' object has no attribute 'set_filter'</code></b></summary>


- 这是因为 Streamlit 会话缓存了旧的 `RagService` 实例（没有 `set_filter` 方法）。
- **解决方法**：在浏览器页面右上角 ☰ → Clear cache → Rerun，或重启 Streamlit 服务。
- 开发阶段可临时将 `app_qa.py` 中的 `if "rag" not in st.session_state: st.session_state["rag"] = RagService()` 改为直接赋值 `st.session_state["rag"] = RagService()`（每次重建实例）。
  </details>

<details>
<summary><b>4. PDF 或 Word 文件解析失败？</b></summary>


- 确保已安装 `pymupdf` 和 `python-docx`：`pip install pymupdf python-docx`。
- PDF 文件需为文字型，扫描版图片 PDF 无法提取文本（需 OCR）。
- 文件损坏或加密也可能导致解析返回 `None`，此时页面会提示“不支持的文件格式”。
  </details>

<details>
<summary><b>5. 如何切换大模型或 Embedding 模型？</b></summary>


- 修改 `rag.py` 中的 `ChatOpenAI` 参数（可换成其他兼容 OpenAI 接口的模型），只需提供正确的 `api_key` 和 `base_url`。
- 修改 `config_data.py` 或 `knowledge_base.py`、`vector_stores.py` 中的 `ZhipuAIEmbeddings`，可换成其他 LangChain 支持的嵌入模型。
  </details>

<details>
<summary><b>6. 对话历史保存在哪里？如何清除？</b></summary>


- 历史文件默认存储在 `./chat_history/` 目录下，以 `session_id` 命名（目前固定为 `C1an_Z`）。

- 可在界面侧边栏点击“清空对话历史”按钮，仅清除当前页面的显示，**不会删除文件**。如需物理删除文件，可手动删除对应文件或调用 `FileChatMessageHistory.clear()` 方法。
  </details>

  

## 致谢

本项目仅用于学习 RAG 系统的基本架构，所有示例文档为虚构内容。

感谢黑马教育传授知识，LangChain、Streamlit、Chroma 等开源项目提供的强大工具链。
