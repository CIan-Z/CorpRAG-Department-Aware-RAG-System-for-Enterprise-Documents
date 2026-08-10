"""
pip install streamlit
Streamlit：当WEB页面元素发生变化，则代码重新执行一遍 如果此时有全局数据的话，会丢失（丢失状态）
session_state用于解决丢失状态
企业知识库管理 - 文档上传服务 (Streamlit)
"""
import time
import streamlit as st
from knowledge_base import KnowledgeBaseService
from file_parser import parse_uploaded_file
# 添加网页标题
st.set_page_config(page_title="知识库管理", page_icon="📚", layout="wide")
# ---------- 自定义样式 ----------
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1f77b4; margin-bottom: 0; }
    .sub-header { font-size: 1.2rem; color: #555; margin-top: 0; }
    .upload-card { background-color: #f8f9fa; border-radius: 10px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
    .doc-preview { border-left: 4px solid #1f77b4; padding-left: 15px; margin-top: 15px; background-color: #f0f5fa; border-radius: 5px; padding: 10px; }
    .meta-badge { display: inline-block; background-color: #e3f2fd; color: #0d47a1; border-radius: 12px; padding: 3px 12px; margin-right: 8px; font-size: 0.9rem; }
    .footer { text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)
# ---------- 页头 ----------
st.markdown('<div class="main-header">📚 企业知识库管理</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">上传、分类、索引 </div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">文件均为编造，本人能力有限，仅供学习RAG</div>', unsafe_allow_html=True)
st.divider()
# ---------- 服务初始化 ----------
if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()
# ---------- 部门与分类设置 ----------
col1, col2 = st.columns([1, 2])
with col1:
    department = st.selectbox(
        "📌 选择所属部门",
        options=["通用", "技术部", "人事部", "财务部", "市场部", "运营部"],
        index=0,
        help="该部门标签将应用到本次上传的所有文档片段"
    )
    st.session_state["dept"] = department
# ---------- 上传卡片 ----------
with st.container():
    st.markdown("### 📤 上传文档")
    st.markdown("支持格式：**TXT, PDF, DOCX, Markdown** —— 拖拽或点击选择文件")
    uploaded_file = st.file_uploader(
        "",
        type=['txt', 'pdf', 'docx', 'md'],
        accept_multiple_files=False,
        label_visibility="collapsed"
    )
if uploaded_file is not None:
    # 提取文件的信息
    file_name = uploaded_file.name
    file_type = uploaded_file.type
    file_size = uploaded_file.size / 1024    # KB

    st.subheader(f"文件名：{file_name}")
    st.write(f"格式：{file_type} | 大小：{file_size:.2f} KB")
    with st.spinner("🔄 正在解析文件内容..."):
        text = parse_uploaded_file(uploaded_file)
        time.sleep(1)  # 模拟解析耗时
    if text is None:
        st.error("❌ 不支持的文件格式或文件解析失败！请检查文件是否损坏。")
    else:
        # 文件基本信息卡片
        st.markdown("<div class='upload-card'>", unsafe_allow_html=True)
        st.markdown("#### 📄 文件详情")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            st.metric("文件名", file_name)
        with col_f2:
            st.metric("文件大小", f"{file_size:.2f} KB")
        with col_f3:
            st.metric("自动分类", "制度文件" if file_name.endswith(".pdf") else "其他")
        st.markdown("</div>", unsafe_allow_html=True)
        # 内容预览（截取前200字）
        with st.expander("🔍 点击预览文本内容"):
            st.text(text[:500] + ("..." if len(text) > 500 else ""))
        # 上传至知识库
        with st.spinner("⏳ 正在添加至知识库中..."):
            result = st.session_state["service"].upload_by_str(
                text,
                filename=file_name,
                # 尝试从会话状态中读取键为 "dept" 的值作为部门信息；如果不存在则默认为 "通用"。
                department=st.session_state.get("dept", "通用"),
                # 根据文件名扩展名自动推断文档类别：PDF 文件归类为“制度文件”，其余为“其他”。
                category="制度文件" if file_name.endswith(".pdf") else "其他"
            )
            time.sleep(0.5)
        # 结果反馈
        if "成功" in result:
            st.success(f"✅ {result}")
            # 显示元数据标签
            st.markdown(
                f"<div style='margin-top:10px;'>"
                f"<span class='meta-badge'>📁 {st.session_state.get('dept', '通用')}</span>"
                f"<span class='meta-badge'>📌 {'制度文件' if file_name.endswith('.pdf') else '其他'}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.info(result)  # 如果是跳过等情况用info
    st.divider()
# ---------- 已上传文件列表 ----------
st.divider()
st.subheader("📋 知识库已有文档")
if st.button("刷新列表"):
    st.rerun()
# 从向量数据库中查询所有文档元数据（仅需一次）
try:
    # 获取所有文档的元数据（Chroma get返回前10000条，足够一般测试）
    all_data = st.session_state["service"].chroma.get(limit=10000)
    sources = set()
    if all_data and "metadatas" in all_data:
        for meta in all_data["metadatas"]:
            if "source" in meta:
                sources.add(meta["source"])
    if sources:
        for s in sorted(sources):
            st.write(f"📄 {s}")
    else:
        st.write("暂无文档")
except Exception as e:
    st.warning(f"无法加载文档列表：{e}")
# ---------- 页脚 ----------
st.markdown("<div class='footer'>© 2026 企业知识库 · 安全可靠</div>", unsafe_allow_html=True)



