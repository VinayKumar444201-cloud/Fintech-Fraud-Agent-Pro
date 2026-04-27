# 🛡️ Fintech Fraud Auditor Pro
### Enterprise-Grade Forensic AML Compliance Suite

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gemini 2.5 Flash](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-green.svg)](https://cloud.google.com/vertex-ai)
[![Vector DB: Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-red.svg)](https://qdrant.tech/)

## 📖 Overview
Fintech Fraud Auditor Pro is a specialized Forensic Agent designed to automate Anti-Money Laundering (AML) transaction monitoring. By combining **Retrieval-Augmented Generation (RAG)** with the **FATF (Financial Action Task Force) 2025 Recommendations**, the system provides grounded, legally-defensible audit justifications rather than generic AI guesses.

This tool bridges the gap between high-volume transaction data and complex regulatory frameworks, providing compliance officers with an automated first-look audit and formal report generation.

## ✨ Key Features
- **Grounded Forensic Auditing:** Uses Gemini 2.5 Flash to analyze transactions against a localized vector database of Oct 2025 FATF guidelines.
- **Automated SAR Generation:** Instantly drafts formal Suspicious Activity Report (SAR) narratives based on identified risks.
- **Analytical Dashboard:** Real-time visualization of jurisdiction exposure and risk distribution using Plotly.
- **Professional PDF Reporting:** Generates high-fidelity, compliance-ready PDF audit logs for internal records.
- **PEP & Sanctions Screening:** Integrated entity lookup for Politically Exposed Persons (PEP) and global sanction lists.

## 🛠️ Technical Stack
- **LLM Engine:** Google Vertex AI (Gemini 2.5 Flash)
- **Vector Database:** Qdrant (Cloud/Managed)
- **Frameworks:** LangChain (LCEL), Streamlit, Pydantic v2
- **Data Visualization:** Plotly Express
- **PDF Engine:** WeasyPrint (GTK+ Backend)

## 🏗️ Architecture
1. **Ingestion:** Regulatory PDFs are chunked and embedded into a 768-dimension Qdrant collection.
2. **Retrieval:** The system fetches the top 5 most relevant legal clauses for every audited transaction.
3. **Augmentation:** A Senior Auditor System Prompt ensures the LLM applies the "Risk-Based Approach" (RBA) strictly.
4. **Output:** Results are presented in an interactive UI with human-in-the-loop verification capabilities.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Google Cloud Project with Vertex AI API enabled
- Qdrant Cloud Cluster and API Key

### Installation
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/Fintech-Fraud-Agent.git](https://github.com/YOUR_USERNAME/Fintech-Fraud-Agent.git)
   cd Fintech-Fraud-Agent