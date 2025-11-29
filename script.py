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
NOTES_FOLDER = "/Users/farhan/Documents/Vault/a. Raw Notes/Apple Notes/iCloud"  # your exported Apple Notes folder
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "phi-3-mini-4k-instruct.gguf"  # exact model name from LMStudio
MAX_TAGS = 5  # max tags per note

# -----------------------------
# 3️⃣ FUNCTIONS
# -----------------------------
def get_tags(note_text):
    """
    Sends note content to LMStudio and returns a list of tags.
    """
    prompt = f"""
You are an assistant analyzing a markdown note.
Suggest up to {MAX_TAGS} relevant tags for this note content.
Return only a JSON array of tags.

Note content:
{note_text}

Example JSON output:
["Tag1", "Tag2", "Tag3"]
"""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        response = requests.post(LMSTUDIO_API, json=payload)
        response.raise_for_status()
        data = response.json()
        # LMStudio response uses OpenAI-style chat completion
        text = data["choices"][0]["message"]["content"]
        return json.loads(text)
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return []
    except json.JSONDecodeError:
        print("Could not parse JSON from LLM response, skipping tags.")
        return []

def find_all_md_files(root_folder):
    """
    Recursively find all .md files in the folder.
    """
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
