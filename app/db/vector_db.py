import os
import chromadb
from chromadb.utils import embedding_functions

class VectorDBManager:
    def __init__(self):
        print("🧠 初始化向量大脑 (ChromaDB)...")
        # 1. 设置向量数据库持久化存储路径 (存在项目根目录下的 chroma_data 文件夹)
        self.persist_directory = os.path.join(os.getcwd(), "chroma_data")
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # 2. 初始化嵌入模型 (Embedding Model)
        # 这里使用 Chroma 自带的轻量级默认模型 (all-MiniLM-L6-v2)
        # 第一次运行时它会自动从 HuggingFace 下载约 90MB 的模型权重，请保持网络畅通！
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # 3. 获取或创建“新闻集合” (Collection)
        # 类似于关系型数据库里的 Table (表)
        self.collection = self.client.get_or_create_collection(
            name="daily_news_collection",
            embedding_function=self.embedding_fn
        )
        print("✅ 向量大脑加载完毕！")

    def add_news_to_vector_db(self, news_items: list):
        """
        将清洗好的新闻存入向量数据库
        news_items: 包含字典的列表，例如 [{"id": "url1", "text": "新闻内容", "metadata": {"source": "xxx"}}]
        """
        if not news_items:
            return
            
        ids = []
        documents = []
        metadatas = []
        
        for item in news_items:
            # 以新闻链接作为唯一 ID，防止重复存入向量库
            ids.append(item['id'])
            # 这里的 text 是用来算数学向量的核心文本
            documents.append(item['text'])
            # metadata 用来存附加信息，方便以后过滤
            metadatas.append(item.get('metadata', {}))
            
        # 批量存入 ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"📥 成功将 {len(news_items)} 条新闻的『记忆向量』刻入大脑。")

    def search_related_news(self, query_text: str, n_results: int = 3) -> list:
        """
        根据输入的问题，去向量空间里寻找最相似的历史新闻
        """
        print(f"🔍 正在记忆深海中检索与『{query_text}』相关的历史情报...")
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # ChromaDB 返回的是一个复杂的字典结构，我们把它提取成简单的列表
        if results['documents'] and len(results['documents'][0]) > 0:
            return results['documents'][0]
        return []