import os
import sys
from dotenv import load_dotenv
from tavily import TavilyClient
from openai_research import OpenAI

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

# System prompt for the research assistant
SYSTEM_PROMPT = """You are an expert research assistant with access to real-time web search results. Your goal is to provide accurate, well-synthesized answers based on the search results provided.

Guidelines:
- Synthesize information from multiple sources when available.
- Cite your sources by referencing the title or URL from the search results.
- If the search results do not contain relevant information, clearly state that and answer based on your own knowledge, noting the limitation.
- Structure your answers for readability: use paragraphs, bullet points, or headings as appropriate.
- Be concise but thorough. Avoid repeating the same information.
- If the user asks a follow-up question, use the conversation history and the new search results to answer contextually.
- Always maintain a helpful, neutral tone."""

# Initialize conversation history (system message + optional past exchanges)
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def search_web(query: str) -> str:
    """
    Query Tavily and return a formatted string of search results.
    """
    try:
        response = tavily.search(query=query, search_depth="advanced")
        results = response.get("results", [])
        if not results:
            return "No relevant web search results were found for this query."

        # Build a clean context block
        context_lines = ["Web Search Results:"]
        for idx, res in enumerate(results, 1):
            title = res.get("title", "Untitled")
            content = res.get("content", "").strip()
            url = res.get("url", "")
            # Truncate content if too long (optional, but helps with token limits)
            if len(content) > 500:
                content = content[:500] + "..."
            context_lines.append(f"\n{idx}. **{title}**")
            context_lines.append(f"   {content}")
            context_lines.append(f"   Source: {url}")
        return "\n".join(context_lines)
    except Exception as e:
        return f"Error during web search: {str(e)}"

def ask_assistant(user_input: str) -> str:
    """
    Get response from OpenAI using conversation history and current web search.
    """
    # 1. Get search results for the current query
    print("\n[🔍 Searching the web...]")
    search_context = search_web(user_input)

    # 2. Build the user message that includes both the query and the search context
    user_message = f"User question: {user_input}\n\n{search_context}\n\nPlease answer based on the above search results."

    # 3. Add the user message to the conversation
    messages.append({"role": "user", "content": user_message})

    # 4. Get completion from OpenAI
    try:
        print("[🤔 Generating answer...]")
        response = openai.chat.completions.create(
            model="gpt-4",  # Change to "gpt-4o" or "gpt-3.5-turbo" as needed
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
            top_p=0.9,
            frequency_penalty=0.2,
            presence_penalty=0.2
        )
        assistant_reply = response.choices[0].message.content

        # 5. Add assistant's reply to history
        messages.append({"role": "assistant", "content": assistant_reply})

        return assistant_reply
    except Exception as e:
        error_msg = f"Error generating answer: {str(e)}"
        # Remove the last user message if we couldn't get a response, to keep history clean
        if messages and messages[-1]["role"] == "user":
            messages.pop()
        return error_msg

def main():
    print("=" * 60)
    print("     OpenAI Researcher with Web Search (type 'exit' to quit)")
    print("=" * 60)

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

if __name__ == "__main__":
    main()