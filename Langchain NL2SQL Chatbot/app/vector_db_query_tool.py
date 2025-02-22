
class VectorDBQueryTool:
    def __init__(self, vector_db):
        self.vector_db = vector_db

    def invoke(self, query: str) -> str:
        docs = self.vector_db.similarity_search(query)
        results = "\n\n".join([doc.page_content for doc in docs])
        return results
