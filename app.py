"""
Professional RAG Chatbot for Tunisian Archaeological Sites.
Streamlit-based interface with chat history and database persistence.
"""

import streamlit as st
from rag import RAGChatbot, check_ollama_status
import database as db
from datetime import datetime

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="Patrimoine Tunisien - Chatbot",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .chat-container {
        border-radius: 10px;
        padding: 1rem;
    }
    .source-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        border-left: 4px solid #1E3A5F;
    }
    .stats-card {
        background: linear-gradient(135deg, #1E3A5F 0%, #2E5A8F 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #1E3A5F;
    }
    div[data-testid="stChatMessage"] {
        padding: 1rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================

def init_session_state():
    """Initialize session state variables."""
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = RAGChatbot()
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "show_sources" not in st.session_state:
        st.session_state.show_sources = True

init_session_state()

# ==================== HELPER FUNCTIONS ====================

def create_new_chat():
    """Create a new chat session."""
    chat_id = db.create_chat("Nouvelle conversation")
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = []
    st.session_state.chatbot.clear_history()
    return chat_id

def load_chat(chat_id: int):
    """Load an existing chat."""
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = db.get_chat_messages(chat_id)
    st.session_state.chatbot.load_history_from_messages(st.session_state.messages)

def format_time(timestamp_str: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m %H:%M")
    except:
        return ""

def truncate_title(title: str, max_len: int = 30) -> str:
    """Truncate title for sidebar display."""
    if len(title) > max_len:
        return title[:max_len-3] + "..."
    return title

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown('<p class="sidebar-title">🏛️ Patrimoine Tunisien</p>', unsafe_allow_html=True)
    
    # New chat button
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("➕ Nouvelle conversation", use_container_width=True, type="primary"):
            create_new_chat()
            st.rerun()
    with col2:
        if st.button("🔄", help="Rafraîchir"):
            st.rerun()
    
    st.divider()
    
    # Search in history
    search_query = st.text_input("🔍 Rechercher", placeholder="Rechercher dans l'historique...")
    
    # Chat list
    st.markdown("### 💬 Conversations")
    
    chats = db.get_all_chats()
    
    if chats:
        for chat in chats:
            is_current = chat['id'] == st.session_state.current_chat_id
            
            # Filter by search
            if search_query and search_query.lower() not in chat['title'].lower():
                continue
            
            col1, col2 = st.columns([5, 1])
            
            with col1:
                icon = "📌" if is_current else "💭"
                btn_type = "primary" if is_current else "secondary"
                title = truncate_title(chat['title'])
                msg_count = chat.get('message_count', 0)
                
                if st.button(
                    f"{icon} {title}", 
                    key=f"chat_{chat['id']}", 
                    use_container_width=True,
                    type=btn_type if is_current else "secondary"
                ):
                    load_chat(chat['id'])
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{chat['id']}", help="Supprimer"):
                    db.delete_chat(chat['id'])
                    if chat['id'] == st.session_state.current_chat_id:
                        st.session_state.current_chat_id = None
                        st.session_state.messages = []
                        st.session_state.chatbot.clear_history()
                    st.rerun()
    else:
        st.info("Aucune conversation. Créez-en une nouvelle!")
    
    st.divider()
    
    # Statistics
    st.markdown("### 📊 Statistiques")
    stats = db.get_stats()
    col_stats = st.columns(2)
    with col_stats[0]:
        st.metric("Conversations", stats.get('total_chats', 0))
    with col_stats[1]:
        st.metric("Messages", stats.get('total_messages', 0))
    
    # Collection info
    try:
        coll_stats = st.session_state.chatbot.get_collection_stats()
        st.metric("Documents indexés", coll_stats.get('document_count', 0))
    except:
        pass
    
    st.divider()
    
    # Settings
    st.markdown("### ⚙️ Paramètres")
    st.session_state.show_sources = st.toggle("Afficher les sources", value=True)
    
    # Ollama status
    st.markdown("### 🔌 État du système")
    ollama_status = check_ollama_status()
    
    if ollama_status['status'] == 'online':
        st.markdown('<span class="status-online">● Ollama en ligne</span>', unsafe_allow_html=True)
        if ollama_status.get('model_available'):
            st.success(f"Modèle: {ollama_status['current_model']}")
        else:
            st.warning(f"Modèle {ollama_status['current_model']} non installé")
    else:
        st.markdown('<span class="status-offline">● Ollama hors ligne</span>', unsafe_allow_html=True)
        st.error("Lancez: ollama serve")
    
    st.divider()
    
    # About
    with st.expander("ℹ️ À propos"):
        st.markdown("""
        **Chatbot RAG - Patrimoine Tunisien**
        
        Ce chatbot utilise:
        - 🔍 **RAG** (Retrieval-Augmented Generation)
        - 🗄️ **ChromaDB** pour la recherche vectorielle
        - 🤖 **Llama3** via Ollama
        - 💾 **SQLite** pour l'historique
        
        Développé pour explorer les sites archéologiques de Tunisie.
        """)

# ==================== MAIN CONTENT ====================

# Header
st.markdown('<p class="main-header">🏛️ Patrimoine Archéologique Tunisien</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Explorez les sites historiques de la Tunisie grâce à l\'intelligence artificielle</p>', unsafe_allow_html=True)

# Main chat area
if st.session_state.current_chat_id is None:
    # Welcome screen
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🏺 Sites UNESCO
        Découvrez les 8 sites tunisiens classés au patrimoine mondial.
        """)
        if st.button("Explorer les sites UNESCO", use_container_width=True):
            create_new_chat()
            st.rerun()
    
    with col2:
        st.markdown("""
        ### 🏛️ Époque Romaine
        Explorez les vestiges de l'Afrique romaine.
        """)
        if st.button("Découvrir l'époque romaine", use_container_width=True):
            create_new_chat()
            st.rerun()
    
    with col3:
        st.markdown("""
        ### 🕌 Patrimoine Islamique
        Mosquées, médinas et monuments islamiques.
        """)
        if st.button("Explorer le patrimoine islamique", use_container_width=True):
            create_new_chat()
            st.rerun()
    
    st.markdown("---")
    
    # Quick examples
    st.markdown("### 💡 Exemples de questions")
    example_questions = [
        "Quels sont les sites UNESCO en Tunisie?",
        "Parle-moi de Carthage et son histoire",
        "Quels sites romains puis-je visiter à Tunis?",
        "Où se trouve l'amphithéâtre d'El Jem?",
        "Quels sont les sites de l'époque punique?"
    ]
    
    cols = st.columns(2)
    for i, q in enumerate(example_questions):
        with cols[i % 2]:
            if st.button(f"💬 {q}", key=f"example_{i}", use_container_width=True):
                chat_id = create_new_chat()
                st.session_state.pending_question = q
                st.rerun()

else:
    # Active chat interface
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🏛️"):
            st.markdown(message["content"])
            
            # Display sources for assistant messages
            if message["role"] == "assistant" and message.get("sources") and st.session_state.show_sources:
                with st.expander("📚 Sources utilisées", expanded=False):
                    for source in message["sources"]:
                        st.markdown(f"""
                        <div class="source-card">
                            <strong>🏛️ {source.get('site', 'N/A')}</strong><br>
                            📍 {source.get('ville', 'N/A')} | 
                            📅 {source.get('periode', 'N/A')} |
                            📖 {source.get('source', 'N/A')}
                            {f"<br>🎯 Pertinence: {source['relevance']:.0%}" if source.get('relevance') else ""}
                        </div>
                        """, unsafe_allow_html=True)
    
    # Handle pending question from examples
    if hasattr(st.session_state, 'pending_question') and st.session_state.pending_question:
        query = st.session_state.pending_question
        st.session_state.pending_question = None
        
        # Process the question
        st.session_state.messages.append({"role": "user", "content": query})
        db.add_message(st.session_state.current_chat_id, "user", query)
        
        if len(st.session_state.messages) == 1:
            title = query[:50] + "..." if len(query) > 50 else query
            db.update_chat_title(st.session_state.current_chat_id, title)
        
        with st.chat_message("user", avatar="🧑"):
            st.markdown(query)
        
        with st.chat_message("assistant", avatar="🏛️"):
            with st.spinner("🔍 Recherche en cours..."):
                answer, sources, tokens, response_time = st.session_state.chatbot.answer(query)
            
            st.markdown(answer)
            
            if sources and st.session_state.show_sources:
                with st.expander("📚 Sources utilisées", expanded=False):
                    for source in sources:
                        st.markdown(f"""
                        <div class="source-card">
                            <strong>🏛️ {source.get('site', 'N/A')}</strong><br>
                            📍 {source.get('ville', 'N/A')} | 
                            📅 {source.get('periode', 'N/A')} |
                            📖 {source.get('source', 'N/A')}
                        </div>
                        """, unsafe_allow_html=True)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
        db.add_message(
            st.session_state.current_chat_id, 
            "assistant", 
            answer, 
            sources,
            tokens_used=tokens,
            response_time_ms=response_time
        )
        st.rerun()
    
    # Chat input
    if query := st.chat_input("Posez votre question sur le patrimoine tunisien..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        db.add_message(st.session_state.current_chat_id, "user", query)
        
        # Update title with first message
        if len(st.session_state.messages) == 1:
            title = query[:50] + "..." if len(query) > 50 else query
            db.update_chat_title(st.session_state.current_chat_id, title)
        
        # Display user message
        with st.chat_message("user", avatar="🧑"):
            st.markdown(query)
        
        # Get and display bot response
        with st.chat_message("assistant", avatar="🏛️"):
            with st.spinner("🔍 Recherche en cours..."):
                answer, sources, tokens, response_time = st.session_state.chatbot.answer(query)
            
            st.markdown(answer)
            
            # Display sources
            if sources and st.session_state.show_sources:
                with st.expander("📚 Sources utilisées", expanded=False):
                    for source in sources:
                        st.markdown(f"""
                        <div class="source-card">
                            <strong>🏛️ {source.get('site', 'N/A')}</strong><br>
                            📍 {source.get('ville', 'N/A')} | 
                            📅 {source.get('periode', 'N/A')} |
                            📖 {source.get('source', 'N/A')}
                            {f"<br>🎯 Pertinence: {source['relevance']:.0%}" if source.get('relevance') else ""}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Show response stats
            if response_time > 0:
                st.caption(f"⚡ Réponse en {response_time}ms")
        
        # Save to session and database
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
        db.add_message(
            st.session_state.current_chat_id, 
            "assistant", 
            answer, 
            sources,
            tokens_used=tokens,
            response_time_ms=response_time
        )

# ==================== FOOTER ====================

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888; font-size: 0.9rem;">
        🏛️ Patrimoine Archéologique Tunisien | Propulsé par RAG + Llama3
    </div>
    """, 
    unsafe_allow_html=True
)
