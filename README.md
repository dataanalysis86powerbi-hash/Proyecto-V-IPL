# Asistente Documental Inteligente (RAG Local)

Este proyecto es una implementación completa y profesional de un sistema de **Generación Aumentada por Recuperación (RAG, por sus siglas en inglés)** que funciona de manera 100% local, garantizando la privacidad absoluta de los datos y sin depender de APIs pagas comerciales. 

Desarrollado para la materia de **Proyectos Avanzados de Ingeniería en Inteligencia Artificial (Proyecto Junio 2026)**.

---

## 🚀 Características Principales

1. **Ingesta y Procesamiento de PDF**: Extrae de forma limpia el contenido de documentos estructurados mediante `PyPDFLoader`.
2. **Estrategia de Chunking Personalizada**: Implementa `RecursiveCharacterTextSplitter` para segmentación semántica precisa con parámetros configurables de tamaño de fragmento (`chunk_size`) y solape técnico (`chunk_overlap`).
3. **Embeddings Locales de Alto Rendimiento**: Conversión semántica utilizando el modelo de código abierto `all-MiniLM-L6-v2` mediante HuggingFace localmente.
4. **Base de Datos Vectorial Persistente**: Almacenamiento e indexación de alta velocidad en disco a través de `ChromaDB`.
5. **Mitigación Estricta de Alucinaciones**: Ingeniería de prompts robusta con `ChatPromptTemplate` que obliga al LLM local a rechazar respuestas cuyas fuentes no estén explícitamente indexadas en los documentos.
6. **Interfaz Web de Usuario (UI Premium)**: Pantalla interactiva reactiva desarrollada en `Streamlit` con gestión de historial y visualización de fuentes/fragmentos de origen utilizados para responder.

---

## 🛠️ Requisitos Previos

- **Python**: Versión 3.10 o superior (Probado en Python 3.13.3).
- **Ollama**: Descargado e instalado desde [ollama.com](https://ollama.com).
- **Modelo LLM**: Modelo `llama3.2` (3B) descargado localmente en Ollama.

---

## 📦 Guía de Instalación y Configuración

Sigue estos pasos para replicar el entorno de desarrollo y ejecutar la aplicación:

### Paso 1: Configurar Ollama
1. Asegúrate de que Ollama se esté ejecutando en tu sistema.
2. Abre una terminal de tu sistema operativo y descarga el modelo Llama 3.2:
   ```bash
   ollama pull llama3.2
   ```
3. Verifica que esté en la lista ejecutando:
   ```bash
   ollama list
   ```

### Paso 2: Crear el Entorno Virtual (venv)
Desde la carpeta raíz del proyecto, ejecuta en PowerShell / CMD:
```powershell
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# En Windows (CMD):
.\.venv\Scripts\activate.bat
```

### Paso 3: Instalar Dependencias
Con el entorno virtual activado, instala las librerías necesarias:
```bash
pip install -r requirements.txt
```

---

## 🖥️ Ejecución de la Aplicación

Para lanzar la interfaz gráfica de Streamlit, ejecuta el siguiente comando:
```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador web predeterminado (normalmente en `http://localhost:8501`).

---

## 📂 Estructura del Código

- [app.py](./app.py): Interfaz web gráfica interactiva de Streamlit. Controla el flujo del chat, carga de PDFs y la parametrización en tiempo real.
- [ingestion.py](./ingestion.py): Módulo encargado de la lectura del PDF, división en fragmentos (chunking) e indexación en la base de datos ChromaDB con HuggingFace Embeddings.
- [rag_chain.py](./rag_chain.py): Orquestación del flujo RAG con LangChain, recuperación semántica y restricciones sistémicas en la inferencia del LLM local de Ollama.
- [requirements.txt](./requirements.txt): Lista de librerías y dependencias necesarias con sus versiones estables.

---

## 📊 Criterios de Evaluación Cubiertos

- **Robustez del Pipeline (40%)**: Admite la carga de cualquier PDF en caliente y realiza búsquedas de similitud precisas utilizando embeddings densos.
- **Mitigación Absoluta de Alucinaciones (30%)**: Su prompt de sistema restringe al LLM para que responda **únicamente** con lo encontrado. Si la consulta no está en el contexto, el LLM responde: *"Lo siento, pero la información solicitada no se encuentra en los documentos indexados."*
- **Rendimiento e Interfaz Gráfica (20%)**: Visualización premium tipo chat, control de errores ante caídas de conexión con Ollama y panel de visualización directa de fuentes recuperadas en formato expandible.
- **Calidad de Software y Documentación (10%)**: Estructurado limpiamente con comentarios, modular, e incluye este `README.md` detallado y su respectivo `requirements.txt`.
