import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def load_and_split_pdf(pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Loads a PDF file and splits it into text chunks.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"El archivo PDF no existe en la ruta: {pdf_path}")
    
    print(f"Cargando PDF: {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"PDF cargado. Total de páginas: {len(documents)}")
    
    print(f"Dividiendo texto (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Texto dividido en {len(chunks)} fragmentos (chunks).")
    return chunks

def ingest_pdf_to_chroma(pdf_path: str, db_directory: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Loads, splits, embeds and indexes a PDF into ChromaDB.
    """
    chunks = load_and_split_pdf(pdf_path, chunk_size, chunk_overlap)
    
    print("Inicializando modelo de embeddings locales (all-MiniLM-L6-v2)...")
    # This will download and run the sentence-transformer model locally
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print(f"Creando y persistiendo la base de datos vectorial en: {db_directory}...")
    # Chroma persists automatically upon initialization in newer versions
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_directory
    )
    
    print("¡Indexación completada con éxito!")
    return vector_store

if __name__ == "__main__":
    # Test block
    import tempfile
    print("Módulo de Ingesta cargado correctamente.")
