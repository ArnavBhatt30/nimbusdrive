from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")

client = Groq(api_key=api_key)

def search_files(query: str, files: list, db_contents: dict = {}):
    if not files:
        return {"success": True, "results": [], "explanation": "No files found in storage.", "total_matches": 0}

    # Build file list — include extracted content if available
    file_list_text = ""
    for f in files:
        line = f"- Filename: {f['filename']}, Size: {f['size']} bytes, Modified: {f['last_modified']}"
        content = db_contents.get(f['filename'])
        if content:
            # Trim content so prompt doesn't get too long
            trimmed = content[:400].replace('\n', ' ')
            line += f", Content preview: \"{trimmed}\""
        file_list_text += line + "\n"

    prompt = f"""You are a smart file search assistant. A user has these files in cloud storage:

{file_list_text}

User's search query: "{query}"

Find the most relevant files based on filename AND content if available.

Respond exactly like this:
MATCHING_FILES: filename1.pdf, filename2.jpg
EXPLANATION: Your explanation here

If nothing matches:
MATCHING_FILES:
EXPLANATION: No files matched your query."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        response_text = response.choices[0].message.content
        matching_filenames = []
        explanation = "Search complete."

        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('MATCHING_FILES:'):
                raw = line.replace('MATCHING_FILES:', '').strip()
                matching_filenames = [f.strip() for f in raw.split(',') if f.strip()]
            elif line.startswith('EXPLANATION:'):
                explanation = line.replace('EXPLANATION:', '').strip()

        matched = [f for f in files if f['filename'] in matching_filenames]

        return {
            "success": True,
            "query": query,
            "results": matched,
            "explanation": explanation,
            "total_matches": len(matched)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"AI search error: {str(e)}"
        }
