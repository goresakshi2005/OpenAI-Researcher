import os
import sys
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions

# Load environment variables
load_dotenv()

# Validate API keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TAVILY_API_KEY:
    print("Error: TAVILY_API_KEY not found in environment variables.")
    sys.exit(1)
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in environment variables.")
    sys.exit(1)

# Initialize clients
tavily = TavilyClient(api_key=TAVILY_API_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)

# -------------------- RL Memory (ChromaDB) --------------------
client = chromadb.PersistentClient(path="./chroma_db")
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
    print(f"[✓] Stored {'successful' if rating >=4 else 'unsuccessful'} interaction (rating {rating})")

def retrieve_examples(query: str, n_pos: int = 2, n_neg: int = 1) -> tuple:
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

# -------------------- System Prompt --------------------
BASE_SYSTEM_PROMPT = """You are an expert research assistant with access to real-time web search results. Your goal is to provide accurate, well-synthesized answers based on the search results provided.

Guidelines:
- Synthesize information from multiple sources when available.
- Cite your sources by referencing the title or URL from the search results.
- If the search results do not contain relevant information, clearly state that and answer based on your own knowledge, noting the limitation.
- Structure your answers for readability: use paragraphs, bullet points, or headings as appropriate.
- Be concise but thorough. Avoid repeating the same information.
- **Use the conversation history to understand context, especially for follow-up questions.** Always consider what has been discussed before.
- Always maintain a helpful, neutral tone."""

messages = [{"role": "system", "content": BASE_SYSTEM_PROMPT}]

low_rating_flag = False
last_user_input = None
last_assistant_response = None

# -------------------- Web Search with Contextual Expansion --------------------
def search_web(query: str, context_query: str = None) -> str:
    """
    Query Tavily. If context_query is provided and not already contained in the query,
    combine them for better context.
    """
    if context_query and context_query.lower() not in query.lower():
        expanded_query = f"{context_query} {query}"
        print(f"[🔍] Expanded search: '{expanded_query}'")
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

# -------------------- Assistant with RL Memory and Context --------------------
def ask_assistant(user_input: str) -> str:
    global low_rating_flag, last_user_input, last_assistant_response

    # 1. Retrieve similar past examples
    pos_examples, neg_examples = retrieve_examples(user_input)
    if pos_examples:
        print("[📚] Found relevant successful past interactions.")
    if neg_examples:
        print("[⚠️] Found past low‑rated interactions to avoid.")

    # 2. Get fresh search results, expanded with previous topic if available
    print("\n[🔍 Searching the web...]")
    search_context = search_web(user_input, context_query=last_user_input)

    # 3. Build a conversation summary from the last few exchanges
    conversation_summary = ""
    if len(messages) > 1:  # there are previous exchanges
        # Take the last 2 exchanges (user+assistant) for brevity
        recent = messages[-4:] if len(messages) >= 4 else messages[1:]  # skip system
        summary_lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            # Truncate long messages for the summary
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            summary_lines.append(f"{role}: {content}")
        if summary_lines:
            conversation_summary = "Recent conversation summary:\n" + "\n".join(summary_lines)

    # 4. Build the user message
    user_message_parts = []

    if conversation_summary:
        user_message_parts.append(conversation_summary)

    if pos_examples:
        user_message_parts.append(f"Here are some examples of successful answers to similar questions:\n{pos_examples}")

    if neg_examples:
        user_message_parts.append(f"Pay attention to the following examples that were rated poorly. Do NOT repeat these mistakes:\n{neg_examples}")

    # Add a contextual reminder if we have a previous topic
    if last_user_input:
        context_hint = f"Note: The user's previous question was about '{last_user_input}'. Please interpret the current query ('{user_input}') in that context."
        user_message_parts.append(context_hint)

    user_message_parts.append(f"User question: {user_input}")
    user_message_parts.append(search_context)

    if low_rating_flag and last_user_input and last_assistant_response:
        improvement_note = (
            f"Note: The previous question was: \"{last_user_input}\" and your answer was:\n"
            f"\"{last_assistant_response}\"\n"
            f"That answer was rated poorly. Please ensure your new answer for the current question "
            f"(\"{user_input}\") addresses the shortcomings and is significantly improved – be more thorough, "
            f"accurate, well‑cited, and engaging. Use examples, analogies, and important details."
        )
        user_message_parts.append(improvement_note)
        low_rating_flag = False
    elif low_rating_flag:
        user_message_parts.append("Note: The previous answer was rated poorly. Please ensure this response is thorough, accurate, and well‑cited.")
        low_rating_flag = False

    user_message_parts.append("Please answer based on the above search results, and follow the style of the successful examples if relevant.")
    user_message = "\n\n".join(user_message_parts)

    messages.append({"role": "user", "content": user_message})

    try:
        print("[🤔 Generating answer...]")
        response = openai.chat.completions.create(
            model="gpt-4",  # or "gpt-4o" / "gpt-3.5-turbo"
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
            top_p=0.9,
            frequency_penalty=0.2,
            presence_penalty=0.2
        )
        assistant_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_reply})

        # Store this exchange for future context
        last_user_input = user_input
        last_assistant_response = assistant_reply

        return assistant_reply
    except Exception as e:
        error_msg = f"Error generating answer: {str(e)}"
        if messages and messages[-1]["role"] == "user":
            messages.pop()
        return error_msg

# -------------------- Main Loop --------------------
def main():
    global low_rating_flag, last_user_input, last_assistant_response
    print("=" * 60)
    print("     OpenAI Researcher with RL Memory (type 'exit' to quit)")
    print("=" * 60)
    print("\nAfter each answer, rate it from 1 (poor) to 5 (excellent).")
    print("High ratings (4‑5) will be stored as good examples.")
    print("Low ratings (1‑3) will be stored as examples to avoid.\n")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not user_input:
            continue

        answer = ask_assistant(user_input)
        print(f"\nAssistant:\n{answer}\n")
        print("-" * 60)

        while True:
            try:
                rating = int(input("\nRate this response (1-5): ").strip())
                if 1 <= rating <= 5:
                    break
                else:
                    print("Please enter a number between 1 and 5.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        add_interaction(user_input, answer, rating)

        if rating < 4:
            low_rating_flag = True
            print("[↗️] Low rating noted – next answer will aim to improve based on this context.")
        else:
            low_rating_flag = False

if __name__ == "__main__":
    main()