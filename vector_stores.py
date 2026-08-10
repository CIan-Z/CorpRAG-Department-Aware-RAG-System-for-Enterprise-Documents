from langchain_chroma import Chroma
import config_data as config
from langchain_community.embeddings import ZhipuAIEmbeddings
import os
emb=ZhipuAIEmbeddings(
    model="embedding-3",
    api_key=os.environ["ZHIPU_KEY"]
)
class VectorStoreService(object):
    def __init__(self, embedding):
        """
        :param embedding: 嵌入模型的传入
        """
        self.embedding = embedding
        # 向量存储
        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory,
        )

    def get_retriever(self, filter_dict: dict = None):
        """返回向量检索器，方便加入chain"""
        """
               支持按元数据过滤，例如 {"department": "技术部"} 或 {"$and": [...]}
               若未提供过滤条件，则返回全部。
        """
        search_kwargs = {"k": config.similarity_threshold}
        if filter_dict:
            #filter 参数会被 Chroma 原生识别并执行元数据过滤。Chroma 的 as_retriever 方法会将 search_kwargs 透传给底层的 similarity_search 方法，而 Chroma 支持在查询时传入 filter 参数来按元数据筛选文档。
            search_kwargs["filter"] = filter_dict
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)


# if __name__ == '__main__':
#     retriever = VectorStoreService(emb).get_retriever()
#
#     res = retriever.invoke("我的体重180斤，尺码推荐")
#     print(res)
'''
在 retriever.invoke("我的体重180斤，尺码推荐") 中，查询字符串被传递给了 self.vector_store（Chroma 向量存储）内部的检索流程，具体流向如下：
传给 self.embedding（嵌入模型）
Chroma 收到查询文本后，会调用你传入的 self.embedding（这里是 ZhipuAIEmbeddings 对象），将查询文本转换为一个向量。
在 Chroma 中执行相似度检索
生成的查询向量与之前存入的所有文本片段的向量进行相似度计算（默认余弦相似度），找出距离最近的 k 个（由 search_kwargs={"k": config.similarity_threshold} 指定
返回最相关的 Document 列表
invoke 返回的 res 是一个 List[Document]，每个 Document 包含 page_content（原始文本片段）和 metadata。
'''
'''
retriever.invoke(query) 内部:
# 1. 向量化查询
query_vector = self.embedding.embed_query("我的体重180斤，尺码推荐")
# 2. 在 Chroma 中执行相似度搜索（返回 top-k 文档）
docs = self.vector_store.similarity_search_by_vector(
    query_vector, 
    k=config.similarity_threshold
)
# 3. 返回 List[Document]
return docs
'''