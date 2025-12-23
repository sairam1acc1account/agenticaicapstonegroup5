import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.core.pipeline.transport import RequestsTransport
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings globally
warnings.simplefilter("ignore", InsecureRequestWarning)
# ---------------- ENV ----------------
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_MODEL")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX = "mou_index"

# ---------------- CLIENTS ----------------
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION
)

# SSL bypass (corp network fix)
transport = RequestsTransport(connection_verify=False)

search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY),
    transport=transport
)

# ---------------- AGENT 1: INGEST ----------------
def agent_ingest_mou(path="proper_mou_document.txt"):
    print("\n🤖 Agent [Ingestion]: Loading MOU")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"✅ Agent [Ingestion]: Loaded {len(text.split())} words")
    return text

# ---------------- AGENT 2: CLAUSE EXTRACTION ----------------
CLAUSE_KEYS = [
    "purpose",
    "parties_responsibilities",
    "confidentiality",
    "term_termination"
]

def agent_extract_clauses(mou_text):
    print("\n🤖 Agent [Clause Extraction]: Extracting clauses")

    response = openai_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": "Extract legal clauses from MOU."},
            {"role": "user", "content": mou_text}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "mou_clauses",
                "schema": {
                    "type": "object",
                    "properties": {k: {"type": "string"} for k in CLAUSE_KEYS},
                    "required": CLAUSE_KEYS
                }
            }
        }
    )

    try:
        clauses = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        print("[WARN] JSON parsing failed, using fallback")
        clauses = {k: "Parsing failed" for k in CLAUSE_KEYS}
    return clauses

# ---------------- AGENT 3: RAG RULE RETRIEVAL ----------------
def agent_retrieve_rule(clause_name):
    print(f"\n🤖 Agent [RAG Retrieval]: Searching rule for '{clause_name}'")

    results = search_client.search(
        search_text=clause_name.replace("_", " "),
        top=1,
        select=["content"]
    )

    for doc in results:
        print("✅ Rule found")
        return doc["content"]

    print("⚠ No rule found")
    return "No rule found"

# ---------------- AGENT 4: COMPLIANCE CHECK ----------------
def agent_validate_clause(clause_name, clause_text, rule_text):
    print(f"\n🤖 Agent [Compliance ({clause_name})]:")

    response = openai_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a legal compliance validator."},
            {"role": "user", "content": f"Rule:\n{rule_text}\n\nClause:\n{clause_text}"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "compliance_result",
                "schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["Compliant", "Non-compliant"]},
                        "issues": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["status", "issues"]
                }
            }
        }
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        result = {"status": "Non-compliant", "issues": ["Parsing failed"]}
    return result

# ---------------- ORCHESTRATOR ----------------
def run_system():
    print("\n=== Multi-Agent RAG Legal Compliance System ===")

    mou = agent_ingest_mou()
    clauses = agent_extract_clauses(mou)

    final = {"compliance_status": "Compliant", "findings": []}

    for name in CLAUSE_KEYS:
        text = clauses.get(name, "Parsing failed")
        rule = agent_retrieve_rule(name)
        result = agent_validate_clause(name, text, rule)

        if result["status"] == "Non-compliant":
            final["compliance_status"] = "Non-compliant"
            final["findings"].append({"clause": name, "issues": result.get("issues", ["Parsing failed"])})

    print("\n📄 Final Compliance Report")
    print(json.dumps(final, indent=2))

# ---------------- MAIN BOT ----------------
if __name__ == "__main__":
    run_system()

    print("\n=== Interactive Legal Compliance Bot ===\n")
    while True:
        user_input = input("[User] ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Exiting bot.")
            break
        print("🤖 Bot: I am a multi-agent system. Currently, I processed ingestion, clause extraction, RAG retrieval, and compliance check.")
