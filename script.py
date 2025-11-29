import os
import json
import requests
import nltk
from nltk.corpus import stopwords

# -----------------------------
# 1️⃣ NLTK setup
# -----------------------------
try:
    STOPWORDS = set(stopwords.words("english"))
except LookupError:
    nltk.download('stopwords')
    STOPWORDS = set(stopwords.words("english"))

# -----------------------------
# 2️⃣ CONFIG
# -----------------------------
NOTES_FOLDER = "/Users/farhan/Documents/Vault/a. Raw Notes/Apple Notes/iCloud"  # your notes folder
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "phi-3-mini-4k-instruct.gguf"  # exact model name from LMStudio
MAX_TAGS = 5
MAX_CHUNK_TOKENS = 1500  # max words per chunk to avoid context overflow

# -----------------------------
# 3️⃣ HELPERS
# -----------------------------
def split_text_into_chunks(text, max_tokens=MAX_CHUNK_TOKENS):
    """Split long note into smaller chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunks.append(" ".join(words[i:i+max_tokens]))
    return chunks

def get_tags_from_chunk(chunk_text):
    """Send one chunk to LMStudio and return a list of string tags."""
    prompt = f"""
You are an assistant analyzing a markdown note.
Suggest up to {MAX_TAGS} relevant tags for this note content.
Return only a JSON array of strings.

Note content:
{chunk_text}

Example JSON output:
["Tag1", "Tag2", "Tag3"]
"""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_output_tokens": 200
    }

    try:
        response = requests.post(LMSTUDIO_API, json=payload)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        tags = json.loads(text)

        # Ensure all tags are strings
        clean_tags = []
        for t in tags:
            if isinstance(t, str):
                clean_tags.append(t)
            elif isinstance(t, dict) and "tag" in t:
                clean_tags.append(str(t["tag"]))
        return clean_tags

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return []
    except json.JSONDecodeError:
        print("Could not parse JSON from LLM response.")
        return []

def get_tags(note_text):
    """Split long notes into chunks and merge all tags."""
    chunks = split_text_into_chunks(note_text)
    all_tags = set()
    for chunk in chunks:
        tags = get_tags_from_chunk(chunk)
        all_tags.update(tags)
    return list(all_tags)[:MAX_TAGS]

def find_all_md_files(root_folder):
    """Recursively find all .md files in the folder."""
    md_files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for f in filenames:
            if f.endswith(".md"):
                md_files.append(os.path.join(dirpath, f))
    return md_files

# -----------------------------
# 4️⃣ PROCESS NOTES
# -----------------------------
def process_notes():
    files = find_all_md_files(NOTES_FOLDER)

    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()

        # Skip empty notes
        if not content.strip():
            continue

        tags = get_tags(content)
        if tags:
            with open(f, "a", encoding="utf-8") as file:
                file.write("\n" + " ".join(f"[[{tag}]]" for tag in tags) + "\n")
            print(f"Added tags to: {os.path.basename(f)} -> {tags}")
        else:
            print(f"No tags added to: {os.path.basename(f)}")

# -----------------------------
# 5️⃣ RUN SCRIPT
# -----------------------------
if __name__ == "__main__":
    process_notes()
