"""
Data Ingestion Module for RAG Chatbot.
Processes corpus.jsonl and indexes documents into ChromaDB.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import chromadb

# ==================== CONFIGURATION ====================

DATA_PROCESSED = Path("data/processed/corpus.jsonl")
CHROMA_PERSIST_DIR = "data/chroma_db"
COLLECTION_NAME = "sites_archeologiques_tunisie"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking parameters
CHUNK_WORD_TARGET = 200
CHUNK_OVERLAP_WORDS = 30
MIN_CHUNK_WORDS = 15

# ==================== UTILITIES ====================

_sentence_split_re = re.compile(r'(?<=[.!?।。!?])\s+')


def read_corpus(path: Path) -> List[Dict]:
    """Read JSONL corpus file."""
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                docs.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"⚠️ Ligne {line_num}: Erreur JSON - {e}")
    return docs


def text_to_chunks(
    text: str, 
    target_words: int = CHUNK_WORD_TARGET, 
    overlap: int = CHUNK_OVERLAP_WORDS
) -> List[str]:
    """Split text into overlapping chunks."""
    sentences = _sentence_split_re.split(text)
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        words = sentence.split()
        word_count = len(words)
        
        if current_word_count + word_count <= target_words or not current_chunk:
            current_chunk.append(sentence)
            current_word_count += word_count
        else:
            # Save current chunk
            chunk_text = " ".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
            
            # Start new chunk with overlap
            if overlap > 0:
                all_words = " ".join(current_chunk).split()
                overlap_words = all_words[-overlap:] if len(all_words) >= overlap else all_words
                current_chunk = [" ".join(overlap_words)]
                current_word_count = len(overlap_words)
            else:
                current_chunk = []
                current_word_count = 0
            
            current_chunk.append(sentence)
            current_word_count += word_count
    
    # Add remaining chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)
    
    # Filter out very short chunks
    chunks = [c for c in chunks if len(c.split()) >= MIN_CHUNK_WORDS]
    
    return chunks


def create_rich_text(doc: Dict) -> str:
    """Create enriched text from document for better embeddings."""
    parts = []
    
    # Site name (important for search)
    site = doc.get('site', '')
    if site:
        parts.append(f"Site archéologique: {site}.")
    
    # Location
    ville = doc.get('ville', '')
    if ville:
        parts.append(f"Situé à {ville}, Tunisie.")
    
    # Main description
    description = doc.get('description', '')
    if description:
        parts.append(description)
    
    # Historical period
    periode = doc.get('periode', '')
    if periode:
        parts.append(f"Période historique: {periode}.")
    
    # UNESCO status
    statut = doc.get('statut', '')
    if statut:
        if statut == "UNESCO":
            parts.append("Ce site est inscrit au patrimoine mondial de l'UNESCO.")
        else:
            parts.append(f"Statut: {statut}.")
    
    # Coordinates
    coordonnees = doc.get('coordonnees', '')
    if coordonnees:
        parts.append(f"Coordonnées GPS: {coordonnees}.")
    
    # Additional details
    details = doc.get('details', '')
    if details:
        parts.append(details)
    
    # Monuments/attractions
    monuments = doc.get('monuments', [])
    if monuments:
        parts.append(f"Principaux monuments: {', '.join(monuments)}.")
    
    # Practical info
    horaires = doc.get('horaires', '')
    if horaires:
        parts.append(f"Horaires: {horaires}.")
    
    tarif = doc.get('tarif', '')
    if tarif:
        parts.append(f"Tarif: {tarif}.")
    
    return " ".join(parts)


# ==================== MAIN INGESTION ====================

def main():
    """Main ingestion process."""
    print("=" * 60)
    print("🏛️ Ingestion des données - Patrimoine Archéologique Tunisien")
    print("=" * 60)
    
    # Check corpus file
    if not DATA_PROCESSED.exists():
        print(f"❌ Fichier non trouvé: {DATA_PROCESSED}")
        print("   Placez votre corpus.jsonl dans data/processed/")
        sys.exit(1)
    
    # Load embedding model
    print(f"\n📦 Chargement du modèle: {EMBEDDING_MODEL_NAME}")
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # Load corpus
    print(f"\n📄 Lecture du corpus: {DATA_PROCESSED}")
    docs = read_corpus(DATA_PROCESSED)
    print(f"   ✓ {len(docs)} documents chargés")
    
    # Initialize ChromaDB
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    print(f"\n🗄️ Initialisation ChromaDB: {CHROMA_PERSIST_DIR}")
    
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    
    # Delete existing collection if present
    collections = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in collections:
        print(f"   ⚠️ Collection existante '{COLLECTION_NAME}' supprimée")
        client.delete_collection(COLLECTION_NAME)
    
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Sites archéologiques de Tunisie"}
    )
    print(f"   ✓ Collection '{COLLECTION_NAME}' créée")
    
    # Prepare data for ingestion
    to_add_ids = []
    to_add_docs = []
    to_add_metadatas = []
    to_add_embeddings = []
    
    global_chunk_id = 0
    
    print(f"\n🔄 Traitement des documents...")
    
    for doc in tqdm(docs, desc="Indexation"):
        doc_id = doc.get("id", global_chunk_id)
        
        # Create rich text for embedding
        full_text = create_rich_text(doc)
        
        if not full_text.strip():
            continue
        
        # Chunk the text
        chunks = text_to_chunks(full_text)
        
        if not chunks:
            # If no chunks, use the full text as one chunk
            chunks = [full_text]
        
        # Compute embeddings
        embeddings = embedder.encode(chunks, show_progress_bar=False, convert_to_numpy=True)
        
        # Prepare for insertion
        for i, chunk_text in enumerate(chunks):
            chunk_uid = f"{doc_id}::chunk_{i}"
            
            metadata = {
                "source_id": str(doc_id),
                "site": str(doc.get("site", "")),
                "ville": str(doc.get("ville", "")),
                "period": str(doc.get("periode", "")),
                "statut": str(doc.get("statut", "")),
                "source": str(doc.get("source", "")),
                "coordonnees": str(doc.get("coordonnees", "")),
                "keywords": ", ".join(doc.get("keywords", [])),
            }
            
            to_add_ids.append(chunk_uid)
            to_add_docs.append(chunk_text)
            to_add_metadatas.append(metadata)
            to_add_embeddings.append(embeddings[i].tolist())
            global_chunk_id += 1
    
    # Batch insert
    print(f"\n📥 Insertion de {len(to_add_ids)} chunks...")
    
    BATCH_SIZE = 500
    for i in tqdm(range(0, len(to_add_ids), BATCH_SIZE), desc="Insertion"):
        j = min(i + BATCH_SIZE, len(to_add_ids))
        collection.add(
            ids=to_add_ids[i:j],
            documents=to_add_docs[i:j],
            metadatas=to_add_metadatas[i:j],
            embeddings=to_add_embeddings[i:j]
        )
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ INGESTION TERMINÉE")
    print("=" * 60)
    print(f"   📄 Documents traités: {len(docs)}")
    print(f"   📦 Chunks créés: {len(to_add_ids)}")
    print(f"   🗄️ Base de données: {CHROMA_PERSIST_DIR}")
    print(f"   📚 Collection: {COLLECTION_NAME}")
    print("\n💡 Lancez l'application avec: streamlit run app.py")


def verify_collection():
    """Verify the collection contents."""
    print("\n🔍 Vérification de la collection...")
    
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    
    try:
        collection = client.get_collection(COLLECTION_NAME)
        count = collection.count()
        print(f"   ✓ Collection '{COLLECTION_NAME}': {count} documents")
        
        # Sample query
        if count > 0:
            results = collection.query(
                query_texts=["Carthage"],
                n_results=3
            )
            print(f"\n   📋 Test de recherche 'Carthage':")
            for i, doc in enumerate(results['documents'][0][:3]):
                print(f"      {i+1}. {doc[:100]}...")
                
    except Exception as e:
        print(f"   ❌ Erreur: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_collection()
    else:
        main()
        verify_collection()
