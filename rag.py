from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from file_history_store import get_history
from vector_stores import VectorStoreService
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import os
def print_prompt(prompt):
    print("="*20)
    print(prompt.to_string())
    print("="*20)

    return prompt


class RagService(object):
    def __init__(self):
        # 1. 先创建所有需要的组件
        self.vector_service = VectorStoreService(
            embedding=config.emb
        )

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以我提供的已知参考资料为主，"
                 "简洁和专业并且不要迎合用户，回答用户问题。参考资料:{context}。"),
                ("system", "用户的对话历史记录，如下："),
                MessagesPlaceholder("history"),
                ("user", "请回答用户提问：{input}")
            ]
        )

        self.chat_model=ChatOpenAI(
            model="deepseek-v4-pro",                     # DeepSeek 模型名
            api_key=os.environ["DEEPSEEK_API_KEY"],      # 或通过环境变量获取（可以自己设，用什么模型都可以）
            base_url="https://api.deepseek.com",    # 关键：指向 DeepSeek 服务
            temperature=0.8,
         )
        self.chain = self.__get_chain(filter_dict=None)



    def __get_chain(self, filter_dict=None):
        """获取最终的执行链"""
        retriever = self.vector_service.get_retriever(filter_dict=filter_dict)   # 传入过滤条件

        def format_document(docs: list[Document]):
            if not docs:
                return "无相关参考资料"

            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"

            return formatted_str
        # 因为 retriever要求的输入是str，但原先输入是dict（"input": "针织毛衣如何保养？"）
        def format_for_retriever(value: dict) -> str:
            return value["input"]

        def format_for_prompt_template(value):
            # {input, context, history}这是self.prompt_template期望输入的
            new_value = {}
            new_value["input"] = value["input"]["input"]
            new_value["context"] = value["context"]
            new_value["history"] = value["input"]["history"]
            return new_value

        chain = (
            {
                "input": RunnablePassthrough(),
                "context": RunnableLambda(format_for_retriever) | retriever | format_document
            } | RunnableLambda(format_for_prompt_template) | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        return conversation_chain
    def set_filter(self, filter_dict):
        """动态更新部门过滤并替换 chain"""
        self.chain = self.__get_chain(filter_dict=filter_dict)
#if __name__ == '__main__':
    # session id 配置
    # session_config = {
    #     "configurable": {
    #         "session_id": "user_001",
    #     }
    # }

    # res = RagService().chain.invoke({"input": "针织毛衣如何保养？"}, session_config)
    # print(res)

