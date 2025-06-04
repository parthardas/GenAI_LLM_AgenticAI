# --- File 1: agents.py ---

from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
import sqlite3

llm = ChatOpenAI(model_name="gpt-4", temperature=0)

# === RAG Agent ===
def build_rag_agent():
    vectorstore = FAISS.load_local("bank_docs", OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()
    rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

    @tool
    def lookup_guideline(query: str) -> str:
        """Searches bank documentation for policy-related questions."""
        return rag_chain.run(query)

    return initialize_agent([lookup_guideline], llm, agent_type="structured-chat-zero-shot-react-description")

# === DB Agent ===
def build_db_agent():
    @tool
    def get_account_balance(user_id: str) -> str:
        """Looks up account balances for a user."""
        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()
        cursor.execute("SELECT account_type, balance FROM accounts WHERE user_id=?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return str(rows) if rows else "No accounts found."

    return initialize_agent([get_account_balance], llm, agent_type="structured-chat-zero-shot-react-description")

# === Bill Payment Agent ===
def build_billing_agent():
    @tool
    def pay_biller(user_id: str, biller_name: str, amount: float) -> str:
        """Pays a biller for the user."""
        # Simulate action
        return f"Paid {amount} to {biller_name} for user {user_id}."

    return initialize_agent([pay_biller], llm, agent_type="structured-chat-zero-shot-react-description")

# Export agent builders
AGENTS = {
    "guidelines": build_rag_agent,
    "accounts": build_db_agent,
    "billing": build_billing_agent,
}
