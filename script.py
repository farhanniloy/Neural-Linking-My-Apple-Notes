import os
import json
import frontmatter
import requests

# -----------------------------
# 1️⃣ CONFIG
# -----------------------------
NOTES_FOLDER = "/Users/farhan/Documents/Vault/a. Raw Notes/Apple Notes/iCloud"  # <-- replace with your folder path
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "Phi-3-mini-4k-instruct.Q4_K_M"
MAX_TAGS = 5  # max number of tags to generate

# -----------------------------
# 2️⃣ FUNCTIONS
# -----------------------------
def get_tags_from_summary(summary_text):
    """
    Sends the note's summary to Phi 3 Mini to get 1-5 niche, linkable tags in Obsidian [[tag]] format.
    """
    prompt = f"""
You are an assistant analyzing a note's summary.  
Suggest **1–5 highly niche, linkable tags** based ONLY on this summary.  
Return them in **Obsidian [[tag]] format**, separated by spaces.  
Do not include anything else.  

Summary:
{summary_text}
"""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    response = requests.post(LMSTUDIO_API, json=payload)
    response.raise_for_status()
    data = response.json()
    text = data["choices"][0]["message"]["content"].strip()

    # Ensure at most MAX_TAGS
    tags = text.split()
    return tags[:MAX_TAGS]


# -----------------------------
# 3️⃣ PROCESS NOTES
# -----------------------------
def process_notes():
    files = [f for f in os.listdir(NOTES_FOLDER) if f.endswith(".md")]

    for f in files:
        path = os.path.join(NOTES_FOLDER, f)
        post = frontmatter.load(path)
        title = post.metadata.get("title", os.path.splitext(f)[0])
        summary = post.metadata.get("summary", "")

        if not summary:
            print(f"Skipping {f}: no summary found")
            continue

        # Generate tags from summary
        tags = get_tags_from_summary(summary)

        # Rewrite the note: insert after title
        content_lines = post.content.splitlines()
        if content_lines:
            content_lines.insert(1, f"tag: {' '.join(tags)}")
        else:
            content_lines = [f"tag: {' '.join(tags)}"]

        post.content = "\n".join(content_lines)

        # Save the note back
        with open(path, "w", encoding="utf-8") as out_f:
            out_f.write(frontmatter.dumps(post))

        print(f"Updated tags for: {f} -> {' '.join(tags)}")


# -----------------------------
# 4️⃣ RUN SCRIPT
# -----------------------------
if __name__ == "__main__":
    process_notes()
