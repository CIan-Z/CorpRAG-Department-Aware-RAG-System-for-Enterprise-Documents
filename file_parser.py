import os
from typing import Optional
import pymupdf
from docx import Document  # pip install python-docx
from io import BytesIO
def parse_uploaded_file(uploaded_file) -> Optional[str]:
    """
    根据文件类型将上传的文件对象内容转为纯文本。
    支持: txt, pdf, docx, md
    返回: 提取的文本内容，若解析失败返回 None
    """
    filename = uploaded_file.name
    _, ext = os.path.splitext(filename) #os.path.splitext(filename)将文件名拆分为 (主文件名， 扩展名) 的元组，例如 "报告.PDF" → ("报告", ".PDF")
    #_表示我们不关心前面的主文件名，只取扩展名部分赋给变量 ext。
    ext = ext.lower()                   #ext.lower()将扩展名字符串全部转为小写，例如 ".PDF" → ".pdf"。
    try:
        if ext == '.txt':
            return uploaded_file.getvalue().decode('utf-8')
        elif ext == '.md':
            return uploaded_file.getvalue().decode('utf-8')
        elif ext == '.pdf':
            return _parse_pdf(uploaded_file.read())
        elif ext == '.docx':
            return _parse_docx(uploaded_file.read())
        else:
            return None
    except Exception as e:
        # 可在此记录日志
        print(f"文件解析失败: {filename} - {e}")
        return None
#将 PDF 文件的二进制内容提取为纯文本字符串。
def _parse_pdf(file_bytes: bytes) -> str:
    text = ""
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        #逐页迭代 PDF 的每一页对象。
        for page in doc:
            text += page.get_text()
    return text
def _parse_docx(file_bytes: bytes) -> str:
    #将内存中的字节数据包装成一个类文件对象，让 python-docx 库能够像打开硬盘文件一样读取它，避免创建临时文件。用 python-docx 库解析该 Word 文档，得到一个包含所有段落、表格等内容的 Document 对象。
    doc = Document(BytesIO(file_bytes))
    #遍历文档中的所有段落对象，提取每个段落的纯文本内容，生成一个字符串列表。
    paragraphs = [para.text for para in doc.paragraphs]
    #将段落文本用换行符连接成一个完整的文本字符串，保持段落之间的自然分隔，便于后续的分割处理。
    return "\n".join(paragraphs)