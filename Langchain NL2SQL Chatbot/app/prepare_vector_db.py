import os
from pyprojroot import here
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

class PrepareVectorDB:
    def __init__(self,
                 doc_dir: str,
                 chunk_size: int,
                 chunk_overlap: int,
                 embedding_model: str,
                 vectordb_dir: str,
                 collection_name: str
                 ) -> None:
        self.doc_dir = doc_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        self.vectordb_dir = vectordb_dir
        self.collection_name = collection_name

    def path_maker(self, file_name: str, doc_dir: str):
        return os.path.join(here(doc_dir), file_name)

    def run(self):
        vectordb_path = here(self.vectordb_dir)

        # Process all documents in the doc_dir
        file_list = os.listdir(here(self.doc_dir))
        docs = []
        for fn in file_list:
            # Choose the appropriate loader based on the file extension
            if fn.endswith(".pdf"):
                loader = PyPDFLoader(self.path_maker(fn, self.doc_dir))
            elif fn.endswith(".txt"):
                from langchain.document_loaders import TextLoader
                loader = TextLoader(self.path_maker(fn, self.doc_dir))
            else:
                print(f"Unsupported file type: {fn}")
                continue
            docs.extend(loader.load_and_split())

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )
        doc_splits = text_splitter.split_documents(docs)

        if os.path.exists(vectordb_path):
            # Load the existing vector DB and add new documents
            print(f"Loading existing vector DB from '{self.vectordb_dir}'...")
            vectordb = Chroma(
                persist_directory=str(vectordb_path),
                collection_name=self.collection_name,
                embedding_function=OpenAIEmbeddings(model=self.embedding_model)
            )
            vectordb.add_documents(doc_splits)
            print("Existing vector DB updated with new documents.")
            print("Number of vectors in vectordb:", vectordb._collection.count(), "\n")
        else:
            # Create the directory and new vector DB
            os.makedirs(vectordb_path)
            print(f"Directory '{self.vectordb_dir}' was created.")
            vectordb = Chroma.from_documents(
                documents=doc_splits,
                collection_name=self.collection_name,
                embedding=OpenAIEmbeddings(model=self.embedding_model),
                persist_directory=str(vectordb_path)
            )
            print("Vector DB created and saved.")
            print("Number of vectors in vectordb:", vectordb._collection.count(), "\n")