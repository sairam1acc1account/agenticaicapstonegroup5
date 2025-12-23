Multi-Agent RAG Legal Compliance System

This project contains a multi-agent system designed to automate legal compliance checking for Memorandums of Understanding (MOUs) using Azure OpenAI, Azure Cognitive Search, and a RAG (Retrieval-Augmented Generation) approach. The system ingests MOUs, extracts clauses, retrieves rules, validates compliance, and provides an interactive chatbot interface for users.

Project Overview:
- Rules are stored as .txt files in Azure Blob Storage.
- Azure Search Indexer transforms the rules into JSON documents with 'id' and 'content' fields.
- The multi-agent system processes MOU documents and performs clause extraction, rule retrieval, and compliance validation.

Architecture Flow:
1. Rule Storage: .txt files in Azure Blob Storage.
2. Indexer & Index: Azure Search Indexer converts text files into structured JSON in a Search Index.
3. Multi-Agent System:
   - Ingestion Agent: Loads MOU documents.
   - Clause Extraction Agent: Extracts structured clauses using Azure OpenAI.
   - RAG Retrieval Agent: Searches rules in Azure Cognitive Search.
   - Compliance Agent: Validates clauses against retrieved rules using Azure OpenAI.
4. Interactive Bot: Users can query compliance results and ask about specific clauses.

When a user uploads an MOU:
- The document is read by the Ingestion Agent.
- Clauses are extracted by the Clause Extraction Agent.
- Each clause is matched against rules stored in the Search Index.
- Compliance Agent validates clauses and produces a JSON report.
- Interactive chatbot allows querying the system for explanations.

Setup Instructions:
1. Clone the repository:
   git clone <repo-url>
   cd <repo-directory>

2. Create a .env file in the root directory with:
   AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint>
   AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
   AZURE_OPENAI_API_VERSION=<api-version>
   AZURE_OPENAI_CHAT_MODEL=<chat-model-name>
   AZURE_SEARCH_ENDPOINT=<your-search-endpoint>
   AZURE_SEARCH_API_KEY=<your-search-api-key>

3. Install dependencies:
   pip install -r requirements.txt

Agents Overview:
- Ingestion Agent: Reads MOU documents from disk.
- Clause Extraction Agent: Uses OpenAI Chat Completions to extract structured clauses.
- RAG Retrieval Agent: Retrieves matching rules from Azure Cognitive Search.
- Compliance Agent: Uses OpenAI to validate clauses against rules and outputs JSON.

Workflow:
1. User uploads an MOU document.
2. Ingestion Agent reads the document content.
3. Clause Extraction Agent extracts structured clauses (e.g., purpose, parties_responsibilities, confidentiality, term_termination).
4. RAG Retrieval Agent searches for corresponding rules in the Azure Search Index.
5. Compliance Agent validates each clause and generates a summary report.
6. Interactive bot interface allows follow-up queries about compliance.

Requirements:
- Python 3.13+
- Azure OpenAI service
- Azure Cognitive Search
- Python packages (see requirements.txt)

Usage:
Run the system:
   python main.py

Example output:
=== Multi-Agent RAG Legal Compliance System ===
[Agent: Ingestion] Loading MOU
[Agent: Clause Extraction] Extracting clauses
[Agent: RAG Retrieval] Searching rule for 'purpose'
[Agent: Compliance] Validating 'purpose'
...
📄 Final Compliance Report
{
  "compliance_status": "Non-compliant",
  "findings": [
    {
      "clause": "purpose",
      "issues": ["Parsing failed"]
    }
  ]
}

Notes:
- Supported clauses: purpose, parties_responsibilities, confidentiality, term_termination.
- Rules must be uploaded as .txt files in Azure Blob Storage and indexed for search.
- SSL warnings from Azure SDK are suppressed in corp network setups.
- The system can be extended to support additional clauses and rules.

Author: Group 5 
Date: 2025-12-23
