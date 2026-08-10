from langchain_community.embeddings import ZhipuAIEmbeddings
import os
emb=ZhipuAIEmbeddings(
    model="embedding-3",
    api_key=os.environ["ZHIPU_KEY"]
)
md5_path = "./md5.text"


# Chroma
collection_name = "rag"
persist_directory = "./chroma_db"


# spliter
chunk_size = 1000
chunk_overlap = 100
separators = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]
max_split_char_number = 1000        # 文本分割的阈值

#
similarity_threshold = 1            # 检索返回匹配的文档数量

embedding_model_name = "embedding-3"
chat_model_name = "deepseek-v4-pro"

session_config = {
        "configurable": {
            "session_id": "C1an_Z",
        }
    }
