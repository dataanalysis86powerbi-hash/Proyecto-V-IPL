import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def load_vector_store(db_directory: str):
    """
    Loads the persistent Chroma vector store.
    """
    if not os.path.exists(db_directory) or not os.listdir(db_directory):
        raise FileNotFoundError(f"La base de datos vectorial no existe en: {db_directory}. Por favor, ingiere un documento PDF primero.")
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma(
        persist_directory=db_directory,
        embedding_function=embeddings
    )
    return vector_store

def create_rag_chain(vector_store, model_name: str = "llama3.2", temperature: float = 0.0, retriever_k: int = 4):
    """
    Creates a retrieval-augmented generation (RAG) chain with strict prompt constraints.
    """
    # 1. Initialize local LLM via Ollama with strict temperature (0.0 for deterministic answers)
    llm = ChatOllama(
        model=model_name,
        temperature=temperature,
        num_predict=512,  # Limit length to prevent infinite loops
    )
    
    # 2. Configure Retriever
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": retriever_k}
    )
    
    # 3. Define the strict Prompt Template (mitigation of hallucinations)
    # The prompt forces the LLM to refuse to answer if the context does not contain the answer.
    system_prompt = (
        "Eres un Asistente Documental Inteligente. Tu tarea es responder a las preguntas del usuario "
        "basándote ESTRICTAMENTE y ÚNICAMENTE en el contexto proporcionado a continuación.\n\n"
        "REGLAS CRÍTICAS DE COMPORTAMIENTO:\n"
        "1. Si la respuesta a la pregunta del usuario no está contenida de forma explícita y directa "
        "en el contexto proporcionado, responde exactamente: 'Lo siento, pero la información solicitada "
        "no se encuentra en los documentos indexados.' No intentes deducir, asumir o utilizar conocimientos "
        "externos al contexto bajo ninguna circunstancia.\n"
        "2. Si la respuesta está en el contexto, sé preciso, estructurado y responde de forma profesional. "
        "Intenta mencionar el origen (ej. 'pág. X') si la fuente lo indica.\n"
        "3. No inventes datos ni menciones hechos no contenidos en el texto provisto.\n\n"
        "CONTEXTO:\n"
        "{context}\n\n"
        "Pregunta del usuario: {question}\n\n"
        "Respuesta:"
    )
    
    prompt = ChatPromptTemplate.from_template(system_prompt)
    
    # 4. Helper function to format retrieved documents
    def format_docs(docs):
        formatted = []
        for i, doc in enumerate(docs):
            page = doc.metadata.get('page', 'Desconocido')
            # Handle page index starting from 0
            if isinstance(page, int):
                page += 1
            formatted.append(f"[Fragmento {i+1} - Página {page}]: {doc.page_content}")
        return "\n\n".join(formatted)
    
    # 5. Define the pipeline
    # We pass the question directly and recover both response and retrieved source documents
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain, retriever

if __name__ == "__main__":
    print("Módulo de Cadena RAG cargado correctamente.")
