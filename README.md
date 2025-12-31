# 🏛️ Tunisia Archaeological Chatbot

<div align="center">

**An intelligent conversational AI system for exploring Tunisia's archaeological heritage**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

---

</div>

## 📖 Overview

Tunisia Archaeological Chatbot is a production-grade Retrieval-Augmented Generation (RAG) system designed to make Tunisia's rich archaeological heritage accessible through natural language conversations. The system combines state-of-the-art embedding models, vector databases, and large language models to provide accurate, contextual responses with full source attribution.

**Key Capabilities:**
- Semantic search across archaeological site documentation
- Context-aware multi-turn conversations
- Automatic source citation and relevance scoring
- Persistent conversation history with SQLite backend
- Real-time response generation with local LLM deployment

**Use Cases:**
- Educational research and academic study
- Tourism planning and cultural exploration
- Archaeological documentation and knowledge management
- Heritage preservation and public engagement

---

## ✨ Features

### Core Functionality

- **🔍 Advanced RAG Pipeline**
  - Vector embeddings using Sentence Transformers (`all-MiniLM-L6-v2`)
  - Semantic similarity search with ChromaDB
  - Configurable top-k retrieval with relevance filtering
  - Document chunking with intelligent overlap strategy

- **💬 Conversational Intelligence**
  - Multi-turn dialogue with conversation history tracking
  - Context-aware response generation via Llama3
  - Automatic conversation summarization
  - Support for French language queries (Arabic-ready architecture)

- **📚 Source Attribution**
  - Automatic citation of source documents
  - Relevance scoring for retrieved information
  - Metadata display (site name, location, historical period, UNESCO status)
  - Transparent information provenance

- **💾 Data Persistence**
  - SQLite-backed chat history storage
  - Session management and conversation threading
  - Search functionality across historical conversations
  - Usage analytics and token tracking

### User Experience

- **🎨 Modern Web Interface**
  - Clean, responsive Streamlit UI
  - Sidebar navigation with search
  - Real-time streaming responses
  - Mobile-friendly design

- **⚙️ Configuration & Control**
  - Adjustable source display preferences
  - System status monitoring
  - Conversation management (create, load, delete)
  - Database statistics dashboard

- **🔒 Privacy-First Design**
  - Local deployment - no external API calls
  - User data stays on-premise
  - No telemetry or tracking
  - Open-source and auditable

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│                        (Streamlit - app.py)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
┌───────────────▼──────────────┐  ┌──────▼─────────────────────┐
│   RAG Engine (rag.py)        │  │  Database (database.py)     │
│  • Query Processing          │  │  • Chat History             │
│  • Context Retrieval         │  │  • Session Management       │
│  • Response Generation       │  │  • Analytics                │
└────┬─────────────┬───────────┘  └─────────────────────────────┘
     │             │
     │    ┌────────▼────────────┐
     │    │   ChromaDB          │
     │    │   Vector Store      │
     │    │   • Embeddings      │
     │    │   • Similarity      │
     │    └─────────────────────┘
     │
┌────▼─────────────────────┐
│   Ollama (Llama3)        │
│   Local LLM Instance     │
│   • Text Generation      │
│   • Context Integration  │
└──────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | Streamlit 1.31+ | Interactive UI and session management |
| **Vector Database** | ChromaDB 0.4.22 | Embedding storage and similarity search |
| **Embedding Model** | Sentence Transformers | Text-to-vector conversion |
| **LLM Runtime** | Ollama | Local language model serving |
| **Language Model** | Llama3 | Response generation and reasoning |
| **Persistence** | SQLite3 | Relational data storage |
| **HTTP Client** | Requests | Ollama API communication |

### Data Flow

1. **Ingestion Phase** (`ingest.py`)
   ```
   corpus.jsonl → Text Processing → Chunking → Embedding → ChromaDB
   ```

2. **Query Phase** (`rag.py`)
   ```
   User Query → Sanitization → Embedding → Vector Search → Context Assembly
                                                                ↓
   Response ← Text Generation ← Prompt Construction ← Conversation History
   ```

3. **Persistence Phase** (`database.py`)
   ```
   Chat Session → Messages → Metadata → SQLite → Analytics
   ```

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:

- **Python 3.8 or higher** ([Download](https://www.python.org/downloads/))
- **Ollama** ([Installation Guide](https://ollama.ai))
- **Git** (for cloning the repository)
- **4GB RAM minimum** (8GB recommended)
- **2GB free disk space** (for models and data)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/DramaW0r/tunisia-archaeological-chatbot.git
cd tunisia-archaeological-chatbot
```

#### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Ollama

```bash
# Pull the Llama3 model (one-time operation, ~4GB download)
ollama pull llama3

# Start Ollama server (keep this terminal open)
ollama serve
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

#### 5. Prepare Archaeological Data

Create your corpus file at `data/processed/corpus.jsonl`:

```json
{"id": 1, "site": "Carthage", "ville": "Tunis", "description": "Ancient Phoenician city founded in 814 BCE, later capital of the Carthaginian Empire...", "periode": "Punique/Romaine", "statut": "UNESCO", "coordonnees": "36.8525°N, 10.3233°E"}
{"id": 2, "site": "Amphithéâtre d'El Jem", "ville": "El Jem", "description": "One of the best-preserved Roman amphitheaters in the world...", "periode": "Romaine", "statut": "UNESCO", "coordonnees": "35.2964°N, 10.7068°E"}
```

**Data Schema:**
- `id` (int): Unique document identifier
- `site` (str): Archaeological site name
- `ville` (str): City/location
- `description` (str): Detailed site description
- `periode` (str): Historical period
- `statut` (str): Status (UNESCO, National, etc.)
- `coordonnees` (str): GPS coordinates
- `keywords` (list, optional): Search keywords
- `monuments` (list, optional): Notable structures

#### 6. Index the Data

```bash
python ingest.py
```

**Expected Output:**
```
🏛️ Ingestion des données - Patrimoine Archéologique Tunisien
============================================================
📦 Chargement du modèle: sentence-transformers/all-MiniLM-L6-v2
✓ Modèle chargé avec succès
📄 Lecture du corpus: data/processed/corpus.jsonl
   ✓ 45 documents chargés
🗄️ Initialisation ChromaDB: data/chroma_db
   ✓ Collection 'sites_archeologiques_tunisie' créée
📄 Traitement des documents...
Indexation: 100%|██████████| 45/45 [00:15<00:00,  2.89docs/s]
📥 Insertion de 287 chunks...
Insertion: 100%|██████████| 1/1 [00:02<00:00,  2.34s/batch]

============================================================
✅ INGESTION TERMINÉE
============================================================
   📄 Documents traités: 45
   📦 Chunks créés: 287
   🗄️ Base de données: data/chroma_db
   📚 Collection: sites_archeologiques_tunisie

💡 Lancez l'application avec: streamlit run app.py
```

#### 7. Launch the Application

```bash
streamlit run app.py
```

The application will automatically open in your browser at `http://localhost:8501`

---

## 📚 Documentation

### Usage Guide

#### Starting a New Conversation

1. Click **"➕ Nouvelle conversation"** in the sidebar
2. The chatbot will greet you and await your query
3. Type your question in the input field at the bottom
4. Press Enter or click the send button

#### Example Queries

**General Information:**
```
"Quels sont les sites archéologiques classés UNESCO en Tunisie?"
"Donne-moi une liste des sites romains accessibles au public"
```

**Specific Site Inquiries:**
```
"Parle-moi de l'histoire de Carthage"
"Où se trouve l'amphithéâtre d'El Jem et comment puis-je le visiter?"
"Quels monuments puis-je voir à Dougga?"
```

**Comparative Analysis:**
```
"Quelle est la différence entre les sites puniques et romains?"
"Compare l'amphithéâtre d'El Jem avec celui de Carthage"
```

**Practical Information:**
```
"Quels sont les horaires d'ouverture des sites de Carthage?"
"Combien coûte l'entrée au musée du Bardo?"
```

#### Managing Conversations

- **Switch Conversations:** Click any conversation title in the sidebar
- **Search History:** Use the search bar to filter conversations by keywords
- **Delete Conversations:** Click the 🗑️ icon next to any conversation
- **View Statistics:** Check the sidebar for total conversations and messages

#### Customization Options

Access settings in the sidebar:

- **Show/Hide Sources:** Toggle source citations display
- **System Status:** Monitor Ollama and database connectivity
- **Conversation Export:** (Coming soon) Export chats as PDF/Markdown

### Configuration

#### RAG Parameters

Edit `rag.py` to adjust retrieval settings:

```python
# Number of documents to retrieve per query
DEFAULT_TOP_K = 5

# Maximum conversation history to maintain
MAX_HISTORY_MESSAGES = 6

# Maximum input length (characters)
MAX_INPUT_LENGTH = 500
```

#### Chunking Strategy

Edit `ingest.py` to modify text processing:

```python
# Target words per chunk
CHUNK_WORD_TARGET = 200

# Overlapping words between chunks
CHUNK_OVERLAP_WORDS = 30

# Minimum chunk size threshold
MIN_CHUNK_WORDS = 15
```

#### LLM Configuration

Edit `rag.py` to change model settings:

```python
# Model selection
LLM_MODEL = "llama3"  # Options: llama3, mistral, codellama

# Generation parameters
"temperature": 0.7,    # Creativity (0.0-1.0)
"num_predict": 500,    # Max tokens to generate
"top_p": 0.9          # Nucleus sampling
```

### Project Structure

```
tunisia-archaeological-chatbot/
│
├── app.py                      # Streamlit web application
│   ├── UI components and layout
│   ├── Session state management
│   └── Chat interface logic
│
├── rag.py                      # RAG engine implementation
│   ├── RAGChatbot class
│   ├── Document retrieval logic
│   ├── LLM integration
│   └── Response generation
│
├── database.py                 # Database management layer
│   ├── ChatDatabase class
│   ├── CRUD operations
│   ├── Schema migration
│   └── Analytics queries
│
├── ingest.py                   # Data indexing pipeline
│   ├── Corpus loading
│   ├── Text chunking
│   ├── Embedding generation
│   └── ChromaDB indexing
│
├── requirements.txt            # Python dependencies
│
├── data/
│   ├── processed/
│   │   ├── .gitkeep           # Directory placeholder
│   │   └── corpus.jsonl       # Source data (user-provided)
│   │
│   ├── chroma_db/             # Vector database (auto-generated)
│   │   ├── *.bin              # HNSW index files
│   │   └── chroma.sqlite3     # Metadata storage
│   │
│   └── chat_history.db        # SQLite conversation history
│
├── .gitignore                  # Git exclusion rules
├── LICENSE                     # MIT License
├── README.md                   # This file
├── CONTRIBUTING.md             # Contribution guidelines
├── SECURITY.md                 # Security policy
└── CODE_OF_CONDUCT.md         # Community guidelines
```

---

## 🔧 Advanced Usage

### Custom Embedding Models

Replace the default embedding model in `ingest.py` and `rag.py`:

```python
# Options: all-MiniLM-L6-v2 (default), all-mpnet-base-v2, multilingual-e5-large
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
```

**Note:** Changing models requires re-indexing your data.

### Alternative LLM Models

Install and use different Ollama models:

```bash
# List available models
ollama list

# Pull alternative models
ollama pull mistral      # Faster, smaller
ollama pull llama3.1     # Latest version
ollama pull codellama    # Code-focused
```

Update `LLM_MODEL` in `rag.py` accordingly.

### Database Maintenance

```python
# Verify collection integrity
python ingest.py --verify

# View database statistics
python -c "from database import get_stats; print(get_stats())"

# Clean up old conversations
python -c "from database import db; db.delete_all_chats()"
```

### API Integration (Coming Soon)

Future versions will include a REST API:

```python
# Example endpoint usage
POST /api/v1/query
{
  "query": "Tell me about Carthage",
  "conversation_id": "abc123",
  "top_k": 5
}
```

---

## 📊 Performance Benchmarks

**Hardware Reference:** Intel i7-9700K, 16GB RAM, SSD

| Operation | Time | Notes |
|-----------|------|-------|
| **First Query** | 3-5s | Includes model loading |
| **Subsequent Queries** | 1-3s | Cached embeddings |
| **Document Ingestion** | ~2-3 docs/s | Depends on text length |
| **Vector Search** | <100ms | For 1000 documents |
| **LLM Generation** | 1-2s | ~500 tokens output |

**Resource Usage:**
- **Memory:** 500MB-1GB (models + data)
- **Disk:** 2-5GB (models + embeddings + history)
- **CPU:** Moderate during inference

**Scalability:**
- Tested with up to 1000 documents
- Supports millions of vectors (ChromaDB capacity)
- SQLite handles thousands of conversations efficiently

---

## 🗺️ Roadmap

### Version 1.1 (Q1 2025)
- [ ] Arabic language interface and responses
- [ ] Advanced filtering (by period, location, UNESCO status)
- [ ] Conversation export (PDF, Markdown, JSON)
- [ ] Image integration for archaeological sites

### Version 1.2 (Q2 2025)
- [ ] Interactive map with site coordinates
- [ ] Voice input/output capabilities
- [ ] Multi-user support with authentication
- [ ] RESTful API endpoints

### Version 2.0 (Q3 2025)
- [ ] Mobile application (iOS/Android)
- [ ] Real-time collaboration features
- [ ] Integration with external knowledge bases
- [ ] Advanced analytics dashboard

### Community Requests
- [ ] Docker containerization
- [ ] Cloud deployment guides (AWS, Azure, GCP)
- [ ] Jupyter notebook tutorials
- [ ] Video demonstration series

---

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'feat: add AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Contribution Guidelines

- Follow [PEP 8](https://pep8.org/) style guidelines
- Write clear, descriptive commit messages (see [Conventional Commits](https://www.conventionalcommits.org/))
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

### Development Setup

```bash
# Install development dependencies
pip install black flake8 pytest mypy

# Format code
black *.py

# Lint code
flake8 . --max-line-length=88

# Type checking
mypy *.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 🔒 Security

### Reporting Vulnerabilities

We take security seriously. If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email details to: [your-security-email@example.com]
3. Include steps to reproduce and potential impact

See [SECURITY.md](SECURITY.md) for our security policy.

### Security Best Practices

- This application runs **locally** - no data leaves your machine
- Chat history stored in **local SQLite** database
- Ollama serves models on **localhost only** (default)
- Regular dependency updates recommended

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**Summary:**
- ✅ Commercial use permitted
- ✅ Modification permitted
- ✅ Distribution permitted
- ✅ Private use permitted
- ⚠️ Liability and warranty disclaimers apply

---

## 🙏 Acknowledgments

This project builds upon excellent open-source technologies:

- **[Ollama](https://ollama.ai)** - Local LLM runtime
- **[ChromaDB](https://www.trychroma.com/)** - Vector database
- **[Sentence Transformers](https://www.sbert.net/)** - Embedding models
- **[Streamlit](https://streamlit.io/)** - Web application framework
- **[Meta's Llama](https://ai.meta.com/llama/)** - Large language model

**Data Sources:**
- Tunisia Ministry of Culture
- UNESCO World Heritage Centre
- OpenStreetMap contributors

**Inspiration:**
- LangChain RAG tutorials
- ChromaDB documentation
- Streamlit community examples

---

## 📞 Support & Contact

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/yourusername/tunisia-archaeological-chatbot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/tunisia-archaeological-chatbot/discussions)
- **Documentation:** [Wiki](https://github.com/yourusername/tunisia-archaeological-chatbot/wiki)

### Community

- **Discord:** [Coming Soon]
- **Twitter:** [@YourHandle](https://twitter.com/yourhandle)
- **Email:** [project-email@example.com]

---

## 📈 Project Status

![GitHub stars](https://img.shields.io/github/stars/yourusername/tunisia-archaeological-chatbot?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/tunisia-archaeological-chatbot?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/tunisia-archaeological-chatbot)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/tunisia-archaeological-chatbot)

**Current Version:** 1.0.0  
**Status:** Active Development  
**Last Updated:** January 2025

---

## 📚 Citation

If you use this project in your research or work, please cite:

```bibtex
@software{tunisia_archaeological_chatbot,
  author = {Your Name},
  title = {Tunisia Archaeological Chatbot: A RAG-Based System for Heritage Exploration},
  year = {2025},
  url = {https://github.com/yourusername/tunisia-archaeological-chatbot}
}
```

---

<div align="center">

**Built with ❤️ for Tunisia's Cultural Heritage**

[⬆ Back to Top](#️-tunisia-archaeological-chatbot)

</div>
