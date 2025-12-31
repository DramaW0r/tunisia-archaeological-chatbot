"""
RAG (Retrieval-Augmented Generation) Chatbot Module.
Handles document retrieval and LLM-based response generation.
"""

import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json
import time
import re
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass

# ==================== CONFIGURATION ====================

CHROMA_PERSIST_DIR = "data/chroma_db"
COLLECTION_NAME = "sites_archeologiques_tunisie"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Ollama configuration
LLM_MODEL = "llama3"
OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_TIMEOUT = 120

# RAG parameters
DEFAULT_TOP_K = 5
MAX_HISTORY_MESSAGES = 6
MAX_INPUT_LENGTH = 500


@dataclass
class RAGResponse:
    """Structured response from the RAG system."""
    answer: str
    sources: List[Dict]
    tokens_used: int = 0
    response_time_ms: int = 0
    error: Optional[str] = None


class RAGChatbot:
    """RAG-based chatbot for Tunisian archaeological sites."""
    
    def __init__(self):
        self._init_chroma()
        self._init_embedder()
        self.conversation_history: List[Dict] = []
    
    def _init_chroma(self):
        """Initialize ChromaDB connection."""
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            collections = [c.name for c in self.client.list_collections()]
            
            if COLLECTION_NAME in collections:
                self.collection = self.client.get_collection(name=COLLECTION_NAME)
            else:
                self.collection = self.client.create_collection(name=COLLECTION_NAME)
                print(f"Created new collection: {COLLECTION_NAME}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB: {e}")
    
    def _init_embedder(self):
        """Initialize the embedding model."""
        try:
            self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}")
    
    # ==================== INPUT PROCESSING ====================
    
    def sanitize_input(self, query: str) -> str:
        """Clean and validate user input."""
        if not query or not isinstance(query, str):
            return ""
        
        query = query.strip()[:MAX_INPUT_LENGTH]
        query = re.sub(r'\x00', '', query)
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    def detect_language(self, text: str) -> str:
        """Detect if text is primarily French or Arabic."""
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        if arabic_pattern.search(text):
            return "ar"
        return "fr"
    
    # ==================== RETRIEVAL ====================
    
    def retrieve_documents(self, query: str, top_k: int = DEFAULT_TOP_K) -> Tuple[str, List[Dict]]:
        """Retrieve relevant documents from ChromaDB."""
        query_embedding = self.embedder.encode([query], convert_to_numpy=True)[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        context_parts = []
        sources = []
        seen_sites = set()
        
        if not results['documents'] or not results['documents'][0]:
            return "", []
        
        for i, (doc_text, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            context_parts.append(doc_text.strip())
            
            site_name = meta.get("site", "Sans titre")
            if site_name not in seen_sites:
                seen_sites.add(site_name)
                distance = results['distances'][0][i] if results.get('distances') else None
                sources.append({
                    "site": site_name,
                    "source": meta.get("source", "inconnu"),
                    "ville": meta.get("ville", ""),
                    "periode": meta.get("period", ""),
                    "coordonnees": meta.get("coordonnees", ""),
                    "relevance": round(1 - distance, 3) if distance else None
                })
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    # ==================== GENERATION ====================
    
    def build_messages(self, query: str, context: str) -> List[Dict]:
        """Build the message list for Ollama API."""
        system_prompt = """Tu es un assistant expert spécialisé sur les sites archéologiques de Tunisie.

RÈGLES IMPORTANTES:
1. Réponds UNIQUEMENT avec les informations du CONTEXTE fourni
2. Si l'information n'est pas dans le contexte, dis clairement: "Je n'ai pas cette information dans ma base de données."
3. Ne jamais inventer ou supposer des informations
4. Réponds en français de manière claire et professionnelle
5. Structure tes réponses avec des paragraphes si nécessaire
6. Mentionne les sources (sites) quand tu donnes des informations
7. Si on te demande des coordonnées ou localisations, fournis-les si disponibles"""

        user_prompt = f"""CONTEXTE (Base de données des sites archéologiques tunisiens):
{context}

QUESTION: {query}

Réponds de manière précise et informative en te basant uniquement sur le contexte ci-dessus."""

        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in self.conversation_history[-MAX_HISTORY_MESSAGES:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    def generate_response(self, messages: List[Dict]) -> Tuple[str, int]:
        """Generate response using Ollama API."""
        start_time = time.time()
        
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500,
                        "top_p": 0.9
                    }
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                answer = result['message']['content']
                tokens = result.get('eval_count', 0)
                return answer, tokens, response_time
            elif response.status_code == 404:
                return f"❌ Modèle '{LLM_MODEL}' non trouvé. Exécutez: ollama pull {LLM_MODEL}", 0, response_time
            else:
                return f"❌ Erreur API (code {response.status_code})", 0, response_time
                
        except requests.exceptions.Timeout:
            return "⏱️ Délai d'attente dépassé. Le modèle prend trop de temps.", 0, 0
        except requests.exceptions.ConnectionError:
            return "❌ Impossible de se connecter à Ollama. Vérifiez qu'il est lancé avec: ollama serve", 0, 0
        except Exception as e:
            return f"❌ Erreur: {str(e)}", 0, 0
    
    # ==================== MAIN INTERFACE ====================
    
    def answer(self, query: str, top_k: int = DEFAULT_TOP_K) -> Tuple[str, List[Dict], int, int]:
        """
        Main method to answer a query.
        Returns: (answer, sources, tokens_used, response_time_ms)
        """
        query = self.sanitize_input(query)
        if not query:
            return "❌ Veuillez entrer une question valide.", [], 0, 0
        
        context, sources = self.retrieve_documents(query, top_k)
        
        if not context:
            return "❌ Aucun document trouvé dans la base de données. Exécutez d'abord: python ingest.py", [], 0, 0
        
        messages = self.build_messages(query, context)
        answer, tokens, response_time = self.generate_response(messages)
        
        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": answer})
        
        if len(self.conversation_history) > MAX_HISTORY_MESSAGES * 2:
            self.conversation_history = self.conversation_history[-MAX_HISTORY_MESSAGES * 2:]
        
        return answer, sources, tokens, response_time
    
    def load_history_from_messages(self, messages: List[Dict]):
        """Load conversation history from database messages."""
        self.conversation_history = []
        for msg in messages[-MAX_HISTORY_MESSAGES:]:
            self.conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the document collection."""
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": COLLECTION_NAME,
                "embedding_model": EMBEDDING_MODEL_NAME
            }
        except Exception:
            return {"document_count": 0}


# ==================== HEALTH CHECK ====================

def check_ollama_status() -> Dict:
    """Check if Ollama is running and model is available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            return {
                "status": "online",
                "models": model_names,
                "current_model": LLM_MODEL,
                "model_available": any(LLM_MODEL in m for m in model_names)
            }
        return {"status": "error", "message": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "message": "Ollama n'est pas en cours d'exécution"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
