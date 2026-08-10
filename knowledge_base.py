"""
知识库
"""
import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
emb=ZhipuAIEmbeddings(
    model="embedding-3",
    api_key=os.environ["ZHIPU_KEY"]
)

def check_md5(md5_str: str):
    """检查传入的md5字符串是否已经被处理过了
        return False(md5未处理过)  True(已经处理过，已有记录）
    """
    if not os.path.exists(config.md5_path):
        # if进入表示文件不存在，那肯定没有处理过这个md5了
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()     # 处理字符串前后的空格和回车
            if line == md5_str:
                return True         # 已处理过

        return False


def save_md5(md5_str: str):
    """将传入的md5字符串，记录到文件内保存"""
    with open(config.md5_path, 'a', encoding="utf-8") as f:
        f.write(md5_str + '\n')


def get_string_md5(input_str: str, encoding='utf-8'):
    """将传入的字符串转换为md5字符串
    hashlib.md5().hexdigest()
    返回的是一个32 字符的十六进制字符串（128 位哈希值，每 4 位用一个十六进制字符表示）。
    """

    # 将字符串转换为bytes字节数组 还原为二进制
    str_bytes = input_str.encode(encoding=encoding)

    # 创建md5对象
    md5_obj = hashlib.md5()     # 得到md5对象
    md5_obj.update(str_bytes)   # 更新内容（传入即将要转换的字节数组）
    md5_hex = md5_obj.hexdigest()       # 得到md5的十六进制字符串

    return md5_hex



class KnowledgeBaseService(object):
    def __init__(self):
        # 如果文件夹不存在则创建，如果存在则跳过
        os.makedirs(config.persist_directory, exist_ok=True)

        self.chroma = Chroma(
            collection_name=config.collection_name,     # 数据库的表名

            embedding_function=emb,
            persist_directory=config.persist_directory,     # 数据库本地存储文件夹
        )     # 向量存储的实例 Chroma向量库对象

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,       # 分割后的文本段最大长度
            chunk_overlap=config.chunk_overlap,     # 连续文本段之间的字符重叠数量
            separators=config.separators,       # 自然段落划分的符号
            length_function=len,                # 使用Python自带的len函数做长度统计的依据
        )     # 文本分割器的对象

    def upload_by_str(self, data: str, filename: str, **kwargs):
        """将传入的字符串，进行向量化，存入向量数据库中"""
        # 先得到传入字符串的md5值
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            return "[跳过]内容已经存在知识库中"
        # 检测一下是否超过阈值
        if len(data) > config.max_split_char_number:
            knowledge_chunks: list[str] = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]

        metadata_base = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "C1an_Z",
        }
        # 合并外部传入的元数据
        metadata_base.update(kwargs)
        metadatas = [metadata_base.copy() for _ in knowledge_chunks]
        # 目前创建的都是字符串，所以用add_texts
        # 入库
        self.chroma.add_texts(knowledge_chunks, metadatas=metadatas)
        save_md5(md5_hex)
        return "[成功]内容已经成功载入向量库"
        '''
        self.chroma.add_texts(knowledge_chunks, ...)这一步会：
        调用嵌入模型，为每一个文本片段生成向量（例如 2048 维浮点数数组）。
        将原始文本片段、生成的向量、元数据（metadata） 一起持久化到 config.persist_directory 目录下的 Chroma 数据库中。
        你后续检索时，返回的也是这些原始文本片段（page_content），不是 MD5。
        “向量化 + 存储” 发生在 Chroma 内部，对象是原始文本。
        MD5 记录 是一个独立的轻量级去重索引，避免相同内容重复向量化。
        '''


    '''
    从功能上讲，检查内容是否已存在确实可以直接拿原始字符串去数据库里查，但直接用 MD5 有工程上的几个实际好处：
    1.速度与成本
    向量数据库的强项是相似度搜索，而不是精确匹配。如果你想查“某段长文本是否已存在”，通常需要逐条比对 page_content，如果知识库很大，开销很高。
    MD5 将任意长度的文本映射成一个固定长度（32 字符）的哈希值，去重时只需 O(1) 的哈希表查询，极快且资源消耗极小。
    2.避免语义误判
    向量库的检索逻辑是“相似”，不是“相等”。直接查文本可能因为细微差异而漏判；而业务去重要求的是完全一致的内容不重复入库。用 MD5 做精确哈希，同一段文字生成相同 MD5，不会误判。
    用极小的计算代价换来了精确、高效、解耦的去重能力。直接查向量库反而会慢且不可靠（除非显式建精确索引）。
    '''
# if __name__ == '__main__':
#     service = KnowledgeBaseService()
#     r = service.upload_by_str("CESHI", "testfile")
#     print(r)
