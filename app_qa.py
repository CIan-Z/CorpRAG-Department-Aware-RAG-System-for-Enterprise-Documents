import time
from rag import RagService
import streamlit as st
import config_data as config
st.write("Script loaded successfully")
# 标题
st.set_page_config(page_title="企业智能客服", page_icon="🤖", layout="wide")
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1f77b4; }
    .sub-header { font-size: 1.1rem; color: #555; margin-bottom: 0.5rem; }
    .section { background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)
# 保证 RagService 在整个用户会话中只被创建一次，后续所有操作都使用这个实例。
if "rag" not in st.session_state:
    st.session_state["rag"] = RagService()
# session_state 是 Streamlit 提供的会话级状态管理机制，用于在多次用户交互（比如点击按钮、输入框提交等）导致脚本重新运行时，保持变量值不丢失。
if "message" not in st.session_state:
    st.session_state["message"] = [{"role": "assistant", "content": "你好！我是企业知识助手，可以选择部门后提问哦 👋"}]
# 如果 st.session_state 中还没有键 "rag"，就创建一个 RagService 实例并存入 st.session_state["rag"]。
# ==================== 侧边栏：部门过滤与工具 ====================
with st.sidebar:
    st.markdown("## ⚙️ 对话设置")
    # 部门选择
    dept_options = ["全部", "通用", "技术部", "人事部", "财务部", "市场部", "运营部"]
    selected_dept = st.selectbox(
        "📌 选择知识库部门",
        dept_options,
        index=0,
        help="选择后仅查询该部门的文档，选择“全部”则搜索所有"
    )
    filter_dict = None if selected_dept == "全部" else {"department": selected_dept}
    # 动态更新过滤条件（仅在变化时重建链，避免重复开销）
    if "last_filter" not in st.session_state or st.session_state["last_filter"] != filter_dict:
        st.session_state["rag"].set_filter(filter_dict)
        st.session_state["last_filter"] = filter_dict
        st.success(f"✅ 已切换至 {selected_dept} 知识库")
    st.divider()
    # 清空对话按钮
    if st.button("🗑️ 清空对话历史"):
        st.session_state["message"] = [{"role": "assistant", "content": "历史已清空，请继续提问。"}]
        # 可选：同时清空持久化历史文件（若需要）
        # from file_history_store import FileChatMessageHistory
        # FileChatMessageHistory(st.session_state["session_config"]["configurable"]["session_id"], "./chat_history").clear()
        st.rerun()
# ==================== 主界面 ====================
st.markdown('<div class="main-header">🤖 企业智能客服</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">当前查询部门：<b>{selected_dept}</b></div>', unsafe_allow_html=True)
st.divider()
for message in st.session_state["message"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])
# 在页面最下方提供用户输入栏
prompt = st.chat_input()

if prompt:

    # 在页面输出用户的提问
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    ai_res_list = []
    with st.spinner("🤔 AI思考中..."):
        res_stream = st.session_state["rag"].chain.stream({"input": prompt}, config.session_config)
        # yield
        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                yield chunk

        st.chat_message("assistant").write_stream(capture(res_stream, ai_res_list))
        st.session_state["message"].append({"role": "assistant", "content": "".join(ai_res_list)})

# ["a", "b", "c"]   "".join(list)    -> abc
# ["a", "b", "c"]   ",".join(list)    -> a,b,c

# 为什么st.session_state["message"].append({"role": "assistant", "content":res_stream})不行?
# stream() 返回的是生成器，不是字符串
# 当 write_stream 执行完毕后，生成器已走到末尾，不可再迭代。此时 res_stream 已经是一个“空壳”，把它直接存入消息列表毫无意义。
# 这个 capture 函数是一个生成器包装器（generator wrapper），它同时完成两个任务：
# 转发数据：yield chunk 将原始的每个流式 chunk 原样传递给下游消费者（比如 write_stream），让界面能实时显示每个片段。
# 副本收集：cache_list.append(chunk) 在转发的同时把每个 chunk 存入列表 cache_list，这样当生成器被完全消费后，cache_list 中就累积了完整的响应内容（所有 chunk 的集合）。
