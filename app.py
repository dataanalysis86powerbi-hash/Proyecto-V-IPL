import streamlit as st
import os
import json
import urllib.request
import shutil
from ingestion import ingest_pdf_to_chroma
from rag_chain import load_vector_store, create_rag_chain

# Directives for directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "chroma_db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_docs")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Page Configuration
st.set_page_config(
    page_title="RAG Local - Asistente Documental Inteligente",
    page_icon="🧠",
    layout="wide"
)

# Custom Styling (Premium Glassmorphism & Gradient Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stSidebarCollapse"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #09090b);
        color: #f4f4f5;
    }
    
    h1, h2, h3, .main-title {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
        text-align: left;
    }
    
    .subtitle {
        color: #a1a1aa;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Custom cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 1rem;
    }
    
    .status-badge-ok {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-badge-err {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Sources style */
    .source-container {
        background: rgba(255, 255, 255, 0.02);
        border-left: 3px solid #818cf8;
        padding: 0.75rem;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.85rem;
        color: #d4d4d8;
    }
    
    /* Streamlit overrides */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Checking Ollama connectivity
def is_ollama_running():
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.5) as response:
            return response.status == 200
    except Exception:
        return False

def get_installed_models():
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=1.5) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = [model['name'] for model in data.get('models', [])]
            # Clean names (remove :latest tag or keep format)
            return models
    except Exception:
        return []

# App Main UI
st.markdown('<div class="main-title">Asistente RAG Local Inteligente</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Pregunta a tus documentos privados localmente y con privacidad garantizada.</div>', unsafe_allow_html=True)

# Initialization of session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "active_doc" not in st.session_state:
    st.session_state.active_doc = None

# Sidebar Content
with st.sidebar:
    st.markdown("### 🖥️ Estado del Sistema")
    
    ollama_ok = is_ollama_running()
    if ollama_ok:
        st.markdown('Servidor Ollama: <span class="status-badge-ok">En línea</span>', unsafe_allow_html=True)
        models = get_installed_models()
        if models:
            selected_model = st.selectbox("Seleccionar Modelo LLM", models, index=0)
        else:
            st.error("No se encontraron modelos. Ejecuta: `ollama pull llama3.2` en tu consola.")
            selected_model = None
    else:
        st.markdown('Servidor Ollama: <span class="status-badge-err">Desconectado</span>', unsafe_allow_html=True)
        st.error("Por favor, asegúrate de que Ollama esté ejecutándose localmente. Abre tu terminal y escribe `ollama serve`.")
        selected_model = None

    st.markdown("---")
    st.markdown("### 📂 Ingesta de Documentos")
    uploaded_file = st.file_uploader("Subir documento PDF", type=["pdf"])
    
    # Advanced Hyperparameters for chunking (Session 2 & 4 requirements)
    with st.expander("⚙️ Parámetros Avanzados"):
        chunk_size = st.slider("Tamaño de Chunk (caracteres)", min_value=200, max_value=2000, value=1000, step=100)
        chunk_overlap = st.slider("Solapamiento (overlap)", min_value=0, max_value=500, value=200, step=50)
        temperature = st.slider("Temperatura (Creatividad LLM)", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
        retriever_k = st.slider("Documentos a recuperar (k)", min_value=1, max_value=8, value=4, step=1)

    if uploaded_file is not None:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Archivo subido: {uploaded_file.name}")
        
        if st.button("Procesar e Indexar Documento"):
            with st.spinner("Procesando PDF, dividiendo textos e indexando en ChromaDB..."):
                try:
                    # Ingest PDF
                    ingest_pdf_to_chroma(
                        pdf_path=file_path,
                        db_directory=DB_DIR,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                    st.session_state.active_doc = uploaded_file.name
                    st.success("¡Documento indexado con éxito!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error durante la ingesta: {str(e)}")
                    
    # Show active document status
    if st.session_state.active_doc:
        st.info(f"📂 Documento Activo: {st.session_state.active_doc}")
    elif os.path.exists(DB_DIR) and len(os.listdir(DB_DIR)) > 0:
        st.session_state.active_doc = "Base de datos persistente cargada"
        st.info(f"📂 Base de datos cargada.")

    # Reset button
    if st.button("Limpiar Base de Datos y Chat"):
        if os.path.exists(DB_DIR):
            shutil.rmtree(DB_DIR)
        if os.path.exists(UPLOAD_DIR):
            shutil.rmtree(UPLOAD_DIR)
            os.makedirs(UPLOAD_DIR, exist_ok=True)
        st.session_state.chat_history = []
        st.session_state.active_doc = None
        st.success("Base de datos y chat eliminados.")
        st.rerun()

# Check database state for UI warnings
db_ready = os.path.exists(DB_DIR) and len(os.listdir(DB_DIR)) > 0

# Chat Layout
if not db_ready:
    st.warning("👈 Sube un documento PDF en el panel lateral para iniciar el Asistente Documental RAG.")
    
    # Showcase project description
    st.markdown("""
    <div class="glass-card">
        <h3>ℹ️ Sobre este Proyecto (Asistente RAG Local)</h3>
        <p>Este sistema implementa un flujo completo de <b>Generación Aumentada por Recuperación (RAG)</b> totalmente offline:</p>
        <ul>
            <li><b>Extracción:</b> Lectura de archivos estructurados (PDF).</li>
            <li><b>Chunking:</b> Fragmentación de párrafos semánticos con tamaño de ventana y solapamiento personalizable.</li>
            <li><b>Embeddings:</b> Modelo local <i>all-MiniLM-L6-v2</i> ejecutándose localmente.</li>
            <li><b>Indexación:</b> Base de datos vectorial persistente mediante <i>ChromaDB</i>.</li>
            <li><b>Orquestación RAG:</b> Respuestas contextuales estrictamente controladas mediante <i>LangChain</i> y <i>Ollama</i> para mitigar la alucinación.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

else:
    # Check Ollama before letting the user chat
    if not ollama_ok or not selected_model:
        st.warning("⚠️ El chat está inactivo porque el servidor de Ollama no está en línea o no tienes modelos cargados.")
    else:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                # Show retrieved sources if available
                if "sources" in message and message["sources"]:
                    with st.expander("🔍 Ver fragmentos de fuentes recuperadas"):
                        for i, doc in enumerate(message["sources"]):
                            page = doc.get("page", "Desconocido")
                            content = doc.get("content", "")
                            st.markdown(f"**Fragmento {i+1} (Página {page}):**")
                            st.markdown(f'<div class="source-container">{content}</div>', unsafe_allow_html=True)

        # Accept user input
        if prompt := st.chat_input("Realiza una pregunta sobre el documento indexado:"):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Buscando en la base de datos vectorial y generando respuesta..."):
                    try:
                        # 1. Load vector store
                        vector_store = load_vector_store(DB_DIR)
                        
                        # 2. Build chain
                        rag_chain, retriever = create_rag_chain(
                            vector_store=vector_store,
                            model_name=selected_model,
                            temperature=temperature,
                            retriever_k=retriever_k
                        )
                        
                        # 3. Retrieve documents for displaying sources
                        retrieved_docs = retriever.invoke(prompt)
                        sources = []
                        for doc in retrieved_docs:
                            # Page indices are 0-based in PyPDFLoader, make them 1-based for the user
                            page_num = doc.metadata.get('page', 0) + 1
                            sources.append({
                                "page": page_num,
                                "content": doc.page_content
                            })
                        
                        # 4. Generate answer
                        answer = rag_chain.invoke(prompt)
                        
                        # 5. Display answer
                        message_placeholder.markdown(answer)
                        
                        # Show sources in expander
                        if sources:
                            with st.expander("🔍 Ver fragmentos de fuentes recuperadas"):
                                for i, doc in enumerate(sources):
                                    st.markdown(f"**Fragmento {i+1} (Página {doc['page']}):**")
                                    st.markdown(f'<div class="source-container">{doc["content"]}</div>', unsafe_allow_html=True)
                        
                        # Save to session history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })
                        
                    except Exception as e:
                        error_msg = f"Ocurrió un error al procesar tu solicitud: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
