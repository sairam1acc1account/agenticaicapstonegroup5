import os
import json
import numpy as np
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI

# ---------------- Load .env ----------------
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

AZURE_BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "legal-documents")

# ---------------- OpenAI Client ----------------
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION
)

def get_embedding(text: str):
    return client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_MODEL,
        input=text
    ).data[0].embedding

# ---------------- Connect to Blob ----------------
blob_service = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
container_client = blob_service.get_container_client(AZURE_BLOB_CONTAINER)

def load_blob_text(blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    return blob_client.download_blob().readall().decode("utf-8")

# ---------------- Utils ----------------
def chunk_text(text, chunk_size=400):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# ---------------- Step 1: Prepare RAG JSONs ----------------
os.makedirs("data", exist_ok=True)

# Rules JSON
rules_text = load_blob_text("all_rules.txt")
rules_chunks = chunk_text(rules_text)
rules_json = []
for i, chunk in enumerate(rules_chunks):
    rules_json.append({
        "id": f"rule_{i+1}",
        "text": chunk,
        "embedding": get_embedding(chunk)
    })
with open("data/rules.json", "w", encoding="utf-8") as f:
    json.dump(rules_json, f, indent=2)
print(f"Saved {len(rules_json)} rule chunks to data/rules.json")

# MOU JSON
mou_text = load_blob_text("proper_mou_document.txt")
mou_chunks_list = chunk_text(mou_text)
mou_json = []
for i, chunk in enumerate(mou_chunks_list):
    mou_json.append({
        "id": f"mou_{i+1}",
        "text": chunk,
        "embedding": get_embedding(chunk)
    })
with open("data/mou.json", "w", encoding="utf-8") as f:
    json.dump(mou_json, f, indent=2)
print(f"Saved {len(mou_json)} MOU chunks to data/mou.json")

# ---------------- Step 2: Load JSONs ----------------
with open("data/rules.json", "r", encoding="utf-8") as f:
    rules = json.load(f)

with open("data/mou.json", "r", encoding="utf-8") as f:
    mou_chunks = json.load(f)

# ---------------- Agents ----------------

# Clause Extraction Agent
def extract_clauses(mou_chunks):
    clauses = {}
    markers = ["Purpose and Scope", "Parties and Responsibilities", "Confidentiality", "Term and Termination",
               "Dispute Resolution", "Governing Law"]
    for sec in markers:
        sec_text = ""
        for chunk in mou_chunks:
            # simple case-insensitive match for clause start
            if sec.lower() in chunk["text"].lower():
                sec_text += chunk["text"].strip() + "\n"
        clauses[sec] = sec_text.strip() if sec_text else "Not found"
    return clauses

# Rule Retrieval Agent
def retrieve_rules(rules_json):
    return rules_json  # return full objects with embeddings

# Compliance Validation Agent
def validate_compliance(clauses, rules_json, threshold=0.75):
    findings = []
    compliant = True
    for sec, text in clauses.items():
        text_emb = get_embedding(text)
        sims = [cosine_similarity(text_emb, rule["embedding"]) for rule in rules_json]
        max_sim = max(sims)
        if max_sim < threshold:
            compliant = False
            findings.append(f"{sec} does not match any rule (max similarity={max_sim:.2f})")
    findings_text = "All clauses meet rules" if compliant else "; ".join(findings)
    return {"compliance_status": "Compliant" if compliant else "Non-compliant",
            "findings": findings_text}

# Summary Agent
def generate_summary(clauses, compliance):
    summary = "Executive Summary:\n\n"
    for key, val in clauses.items():
        summary += f"{key}:\n{val}\n\n"
    summary += f"Compliance Status: {compliance['compliance_status']}\nFindings: {compliance['findings']}"
    return summary

# ---------------- Step 3: Run Pipeline ----------------
clauses = extract_clauses(mou_chunks)
print("\n--- Extracted Clauses ---\n", clauses)

rules_json = retrieve_rules(rules)
print(f"\nRetrieved {len(rules_json)} rules from RAG JSON")

compliance = validate_compliance(clauses, rules_json)
print("\n--- Compliance Validation ---\n", compliance)

summary = generate_summary(clauses, compliance)
print("\n--- Executive Summary ---\n", summary)
