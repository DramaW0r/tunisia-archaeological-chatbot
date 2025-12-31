# Tunisia Archaeological Chatbot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)

An intelligent RAG-based chatbot for exploring Tunisia's archaeological heritage through natural language conversations.

## Overview

This system combines semantic search, vector databases, and large language models to provide accurate responses about Tunisian archaeological sites with full source attribution.

**Key Features:**
- Semantic search using ChromaDB and Sentence Transformers
- Context-aware conversations with Llama3
- Automatic source citation with relevance scoring
- Persistent chat history with SQLite
- Local-first deployment (no external APIs)

## Features

### Core Functionality

- **RAG Pipeline**: Vector embeddings with Sentence Transformers and semantic search via ChromaDB
- **Conversational AI**: Multi-turn dialogues with context awareness using Llama3
- **Source Attribution**: Automatic citations with relevance scores and metadata
- **Persistence**: SQLite-backed chat history with search and analytics

### User Interface

- Clean Streamlit web interface
- Real-time response streaming
- Conversation management (create, load, delete, search)
- System status monitoring
- Privacy-first local deployment

## Architecture

### System Components

```
User Interface (Streamlit)
         ↓
    RAG Engine
    ↓         ↓
ChromaDB   Ollama/Llama3
         ↓
   SQLite Database
```

### Technology Stack

- **Web Framework**: Streamlit
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: Llama3 via Ollama
- **Database**: SQLite3
- **Language**: Python 3.8+

## Quick Start

### Prerequisites

- Python 3.8+
- Ollama ([Installation](https://ollama.ai))
- 4GB RAM minimum

### Installation

**1. Clone and setup environment**
```bash
git clone https://github.com/yourusername/tunisia-archaeological-chatbot.git
cd tunisia-archaeological-chatbot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure Ollama**
```bash
ollama pull llama3
ollama serve  # Keep running in separate terminal
```

**3. Prepare data**

Create `data/processed/corpus.jsonl`:
```json
{"id": 1, "site": "Carthage", "ville": "Tunis", "description": "Ancient Phoenician city...", "periode": "Punique/Romaine", "statut": "UNESCO"}
```

**4. Index data**
```bash
python ingest.py
```

**5. Launch application**
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Usage

### Example Queries

```
"Quels sont les sites UNESCO en Tunisie?"
"Parle-moi de l'histoire de Carthage"
"Où se trouve l'amphithéâtre d'El Jem?"
```

### Managing Conversations

- **New chat**: Click "Nouvelle conversation" in sidebar
- **Switch chats**: Click any conversation title
- **Search**: Use search bar to filter conversations
- **Delete**: Click 🗑️ icon next to conversation

### Configuration

Edit settings in the source files:

**RAG Parameters** (`rag.py`):
```python
DEFAULT_TOP_K = 5              # Documents per query
MAX_HISTORY_MESSAGES = 6       # Conversation context
```

**Chunking** (`ingest.py`):
```python
CHUNK_WORD_TARGET = 200        # Words per chunk
CHUNK_OVERLAP_WORDS = 30       # Overlap between chunks
```

## Project Structure

```
tunisia-archaeological-chatbot/
├── app.py                    # Streamlit UI
├── rag.py                    # RAG engine
├── database.py               # SQLite management
├── ingest.py                 # Data indexing
├── requirements.txt
└── data/
    ├── processed/
    │   └── corpus.jsonl      # User-provided
    ├── chroma_db/            # Auto-generated
    └── chat_history.db       # Auto-generated
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Built with:
- [Ollama](https://ollama.ai) - LLM runtime
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Sentence Transformers](https://www.sbert.net/) - Embeddings
- [Streamlit](https://streamlit.io/) - Web framework

## Contact

- Issues: [GitHub Issues](https://github.com/yourusername/tunisia-archaeological-chatbot/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/tunisia-archaeological-chatbot/discussions)
