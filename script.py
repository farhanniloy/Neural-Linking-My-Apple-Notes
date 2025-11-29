import os
import re
import json
import frontmatter
import requests
from collections import Counter, defaultdict
import nltk

# -----------------------------
# 1️⃣ NLTK setup
# -----------------------------
nltk.download('stopwords')
from nltk.corpus import stopwords
STOPWORDS = set(stopwords.words("english"))

# -----------------------------
# 2️⃣ CONFIG
# -----------------------------
NOTES_FOLDER = "/Users/farhan/Documents/Vault/a. Raw Notes/Apple Notes/iCloud"  # <-- replace with your folder path
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "Phi-3-mini-4k-instruct.Q4_K_M"
MAX_KEYWORDS = 15
BACKLINK_THRESHOLD = 2  # minimum shared keywords to create a backlink

# -----------------------------
# 3️⃣ FUNCTIONS
# -----------------------------
def extract_keywords(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = text.split()
    words = [w for w in words if w not in STOPWORDS and len(w) > 3]
    freq = Counter(words)
    return [word for word, _ in freq.most_common(MAX_KEYWORDS)]


def get_summary_and_tags(note_text, keywords):
    prompt = f"""
You are an assistant analyzing a markdown note.
Summarize the note in 1–2 sentences and suggest relevant tags.
Note content:
{note_text}

Keywords:
{keywords}

Return JSON in the format:
{{
"summary": "...",
"tags": ["tag1", "tag2", ...]
}}
"""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    response = requests.post(LMSTUDIO_API, json=payload)
    response.raise_for_status()
    data = response.json()
    text = data["choices"][0]["message"]["content"]

    try:
        return json.loads(text)
    except:
        return {"summary": text[:200], "tags": []}


def create_backlinks(notes_dict):
    """
    notes_dict: {note_name: {"keywords": [...], ...}}
    Returns: {note_name: [linked_notes]}
    """
    backlinks = defaultdict(list)
    names = list(notes_dict.keys())

    for i, name1 in enumerate(names):
        kw1 = set(notes_dict[name1]["keywords"])
        for j in range(i + 1, len(names)):
            name2 = names[j]
            kw2 = set(notes_dict[name2]["keywords"])
            shared = kw1 & kw2
            if len(shared) >= BACKLINK_THRESHOLD:
                backlinks[name1].append(name2)
                backlinks[name2].append(name1)
    return backlinks

# -----------------------------
# 4️⃣ PROCESS NOTES
# -----------------------------
def process_notes():
    files = [f for f in os.listdir(NOTES_FOLDER) if f.endswith(".md")]
    notes_data = {}

    # First pass: extract keywords + summary/tags
    for f in files:
        path = os.path.join(NOTES_FOLDER, f)
        post = frontmatter.load(path)
        content = post.content
        note_title = os.path.splitext(f)[0]

        keywords = extract_keywords(content)
        result = get_summary_and_tags(content, keywords)

        notes_data[note_title] = {
            "file_path": path,
            "keywords": keywords,
            "summary": result.get("summary", ""),
            "tags": result.get("tags", [])
        }
        print(f"Processed summary & tags for: {note_title}")

    # Second pass: create backlinks
    backlinks = create_backlinks(notes_data)

    # Write YAML front matter with backlinks
    all_keywords = Counter()
    all_tags = Counter()
    for note, data in notes_data.items():
        post = frontmatter.load(data["file_path"])
        post["summary"] = data["summary"]
        post["tags"] = data["tags"]
        post["keywords"] = data["keywords"]
        post["backlinks"] = list(set(backlinks.get(note, [])))  # remove duplicates

        all_keywords.update(data["keywords"])
        all_tags.update(data["tags"])

        with open(data["file_path"], "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        print(f"Written YAML for: {note}")

    # Create Index Note
    index_path = os.path.join(NOTES_FOLDER, "_Index.md")
    index_content = "# Index of Notes\n\n"
    index_content += "## Tags Used\n"
    for tag, count in all_tags.most_common():
        index_content += f"- {tag} ({count})\n"
    index_content += "\n## Common Keywords\n"
    for kw, count in all_keywords.most_common(50):
        index_content += f"- {kw} ({count})\n"
    index_content += "\n## Notes List\n"
    for note in notes_data.keys():
        index_content += f"- [[{note}]]\n"

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    print("Index note created: _Index.md")

# -----------------------------
# 5️⃣ RUN SCRIPT
# -----------------------------
if __name__ == "__main__":
    process_notes()
