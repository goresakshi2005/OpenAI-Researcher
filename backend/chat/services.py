import os
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

# Validate API keys (will be checked at startup)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not TAVILY_API_KEY or not OPENAI_API_KEY:
    raise ValueError("Missing API keys in environment")

# Initialize clients (singletons)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)

# ChromaDB for RL memory
client = chromadb.PersistentClient(path="./chroma_db")  # relative to backend/
embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small"
)

pos_collection = client.get_or_create_collection(
    name="successful_interactions",
    embedding_function=embedding_fn
)
neg_collection = client.get_or_create_collection(
    name="unsuccessful_interactions",
    embedding_function=embedding_fn
)

def add_interaction(query: str, response: str, rating: int):
    """Store interaction in ChromaDB based on rating."""
    collection = pos_collection if rating >= 4 else neg_collection
    count = collection.count()
    doc_id = f"interaction_{count}"
    collection.add(
        documents=[f"Q: {query}\nA: {response}"],
        metadatas=[{"query": query, "rating": rating}],
        ids=[doc_id]
    )

def retrieve_examples(query: str, n_pos: int = 2, n_neg: int = 1):
    """Retrieve similar successful/unsuccessful examples."""
    pos_examples = []
    neg_examples = []
    if pos_collection.count() > 0:
        pos_results = pos_collection.query(query_texts=[query], n_results=n_pos)
        if pos_results['documents'][0]:
            for doc, meta in zip(pos_results['documents'][0], pos_results['metadatas'][0]):
                pos_examples.append(f"✅ Good example (rating {meta['rating']}):\n{doc}")
    if neg_collection.count() > 0:
        neg_results = neg_collection.query(query_texts=[query], n_results=n_neg)
        if neg_results['documents'][0]:
            for doc, meta in zip(neg_results['documents'][0], neg_results['metadatas'][0]):
                neg_examples.append(f"❌ Poor example (rating {meta['rating']}) – avoid these mistakes:\n{doc}")
    return "\n\n".join(pos_examples), "\n\n".join(neg_examples)

def search_web(query: str, context_query: str = None) -> str:
    """Query Tavily, optionally expand with context."""
    if context_query and context_query.lower() not in query.lower():
        expanded_query = f"{context_query} {query}"
    else:
        expanded_query = query
    try:
        response = tavily.search(query=expanded_query, search_depth="advanced")
        results = response.get("results", [])
        if not results:
            return "No relevant web search results were found for this query."
        context_lines = ["Web Search Results:"]
        for idx, res in enumerate(results, 1):
            title = res.get("title", "Untitled")
            content = res.get("content", "").strip()
            url = res.get("url", "")
            if len(content) > 500:
                content = content[:500] + "..."
            context_lines.append(f"\n{idx}. **{title}**")
            context_lines.append(f"   {content}")
            context_lines.append(f"   Source: {url}")
        return "\n".join(context_lines)
    except Exception as e:
        return f"Error during web search: {str(e)}"

# System prompt
BASE_SYSTEM_PROMPT = """You are an expert research assistant with access to real-time web search results. Your goal is to provide accurate, well-synthesized answers based on the search results provided.

Guidelines:
- Synthesize information from multiple sources when available.
- Cite your sources by referencing the title or URL from the search results.
- If the search results do not contain relevant information, clearly state that and answer based on your own knowledge, noting the limitation.
- Structure your answers for readability: use paragraphs, bullet points, or headings as appropriate.
- Be concise but thorough. Avoid repeating the same information.
- **If the user asks a follow-up question or a short query, use the conversation history to understand the context and provide a relevant answer.** Always consider the previous topics discussed.
- Always maintain a helpful, neutral tone."""

def build_conversation_summary(conversation_history, max_exchanges=2):
    """
    Create a condensed summary of the most recent exchanges.
    Each exchange consists of a user message and an assistant message.
    """
    if not conversation_history:
        return ""

    # Take the last (max_exchanges * 2) messages (each exchange = user + assistant)
    recent = conversation_history[-(max_exchanges * 2):]
    summary_lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        if len(content) > 200:
            content = content[:200] + "..."
        summary_lines.append(f"{role}: {content}")

    if summary_lines:
        return "Recent conversation summary:\n" + "\n".join(summary_lines)
    return ""

def build_messages(conversation_history, user_input, pos_examples, neg_examples, search_context,
                   previous_user_input=None, previous_response=None, low_rating_flag=False):
    """Construct the list of messages for OpenAI API, including a conversation summary."""
    messages = [{"role": "system", "content": BASE_SYSTEM_PROMPT}]

    # Add conversation history (excluding system prompt)
    for msg in conversation_history:
        if msg['role'] != 'system':
            messages.append(msg)

    # Build the user message with summary, examples, and search context
    user_parts = []

    # 1. Conversation summary (if any)
    summary = build_conversation_summary(conversation_history)
    if summary:
        user_parts.append(summary)

    # 2. Positive examples
    if pos_examples:
        user_parts.append(f"Here are some examples of successful answers to similar questions:\n{pos_examples}")

    # 3. Negative examples
    if neg_examples:
        user_parts.append(f"Pay attention to the following examples that were rated poorly. Do NOT repeat these mistakes:\n{neg_examples}")

    # 4. Current user question (place early to give it prominence)
    user_parts.append(f"User question: {user_input}")

    # 5. Enhanced context hint if previous exchange exists (always include, not just for low ratings)
    if previous_user_input and previous_response:
        context_hint = (
            f"Note: The user's previous question was: \"{previous_user_input}\"\n"
            f"Your previous answer was: \"{previous_response}\"\n"
            f"The current question ('{user_input}') is a follow‑up. Please answer in the context of the previous conversation, "
            f"and if applicable, relate it to the previous topic."
        )
        user_parts.append(context_hint)
    elif previous_user_input:
        context_hint = f"Note: The user's previous question was about '{previous_user_input}'. Please interpret the current query ('{user_input}') in that context."
        user_parts.append(context_hint)

    # 6. Web search results
    user_parts.append(search_context)

    # 7. Improvement note if previous answer was poor
    if low_rating_flag and previous_user_input and previous_response:
        improvement_note = (
            f"Note: The previous answer was rated poorly. Please ensure your new answer for the current question "
            f"(\"{user_input}\") addresses the shortcomings and is significantly improved – be more thorough, "
            f"accurate, well‑cited, and engaging."
        )
        user_parts.append(improvement_note)
    elif low_rating_flag:
        user_parts.append("Note: The previous answer was rated poorly. Please ensure this response is thorough, accurate, and well‑cited.")

    # 8. Final instruction
    user_parts.append("Please answer based on the above search results, and follow the style of the successful examples if relevant.")

    user_message = "\n\n".join(user_parts)
    messages.append({"role": "user", "content": user_message})
    return messages

def ask_assistant(user_input, conversation_history, previous_user_input=None, previous_response=None, low_rating_flag=False, use_web_search=True):
    """Main function to get assistant response."""
    # 1. Retrieve similar past examples
    pos_examples, neg_examples = retrieve_examples(user_input)

    # 2. Get search results if enabled
    search_context = ""
    if use_web_search:
        search_context = search_web(user_input, context_query=previous_user_input)
    else:
        search_context = "Web search was disabled by the user. Please answer based on your own knowledge."

    # 3. Build messages
    messages = build_messages(
        conversation_history=conversation_history,
        user_input=user_input,
        pos_examples=pos_examples,
        neg_examples=neg_examples,
        search_context=search_context,
        previous_user_input=previous_user_input,
        previous_response=previous_response,
        low_rating_flag=low_rating_flag
    )

    # 4. Call OpenAI
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
            top_p=0.9,
            frequency_penalty=0.2,
            presence_penalty=0.2
        )
        assistant_reply = response.choices[0].message.content
        return assistant_reply
    except Exception as e:
        return f"Error generating answer: {str(e)}"