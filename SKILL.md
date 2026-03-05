---
name: local-knowledge-base
description: A local knowledge base Q&A system. Supports extracting knowledge from various documents and building knowledge graphs with hybrid (graph+LLM) mode. Triggered by: reading local files, building knowledge base, Q&A, knowledge base Q&A, local document Q&A, importing documents.
metadata.openclaw: '{"emoji": "📚"}'
---

# Local Knowledge Base Q&A System

You are a local knowledge base Q&A assistant that helps users manage knowledge and retrieve relevant information when asked.

## First Use - Domain Configuration

**Before first use, please set your industry domain:**

```bash
# 1. List available domains
python scripts/domain_config.py list

# 2. Set your domain (e.g., manufacturing, healthcare, finance, education, retail, general)
python scripts/domain_config.py set manufacturing

# 3. View current domain
python scripts/domain_config.py current
```

**Preset Domains:**

| Domain | Description |
|--------|-------------|
| Manufacturing | 3C manufacturing, supply chain, equipment |
| Healthcare | Hospitals, medicine, diseases |
| Finance | Banking, securities, investment |
| Education | Schools, courses, students |
| Retail | Stores, products, inventory |
| General | General knowledge management |

---

## Architecture Upgrade (2026-03-05)

### Technical Features
- **Storage**: SQLite database (`kb_storage.db`)
- **Incremental Update**: Based on file hash, only process changed documents
- **Memory Index**: Pre-load graph to memory for faster queries
- **Entity Disambiguation**: Auto-normalize entity names (e.g., "MES System" → "MES")
- **Semantic Chunking**: Split by paragraphs/headings to preserve knowledge integrity
- **OCR Support**: Extract text from images
- **Domain Customization**: Support multiple industry domains

---

## Table of Contents

1. [First Use](#first-use---domain-configuration)
2. [Domain定位](#domain-focus)
3. [Supported Formats](#supported-file-formats)
4. [Core Features](#core-features)
5. [Storage Structure](#storage-structure)
6. [Workflow](#workflow)
7. [Script Reference](#script-reference)
8. [Q&A Process](#qanda-process)

---

## Domain Focus

After setting the domain, the system automatically loads corresponding entity type definitions.

### Manufacturing Core Knowledge Areas (Default)

| Area | Description | Examples |
|------|------------|----------|
| **Supply Chain** | Suppliers, procurement, inventory | Supplier management, procurement strategy, inventory optimization |
| **Planning** | Production planning, capacity planning | MPS, APS, scheduling |
| **Manufacturing** | Production process, line management | SMT, assembly, testing, packaging |
| **New Product** | NPI, trial production, mass production | Trial follow-up, DFM, ramp-up plan |
| **Quality** | IQC, IPQC, FQC, OQC | Incoming inspection, in-process inspection, outgoing inspection |
| **Warehouse** | Warehouse management, in/out | WMS, inventory turnover, bin management |
| **Logistics** | Transportation, distribution, coordination | TMS, cross-border logistics |

### Other Preset Domains

- **Healthcare**: Departments, diseases, medicine, exams, hospitals, doctors
- **Finance**: Institutions, products, metrics, clients, transactions
- **Education**: Schools, students, teachers, courses, grades
- **Retail**: Stores, products, clients, suppliers, inventory, sales

---

## Supported File Formats

| Format | Extensions | Notes |
|--------|------------|-------|
| Word | .docx | Microsoft Word |
| PDF | .pdf | PDF documents (with table extraction) |
| Text | .txt | Plain text |
| Excel | .xlsx, .xls | Excel spreadsheets |
| PPT | .pptx, .ppt | PowerPoint presentations (with OCR) |
| Markdown | .md | Markdown documents |

---

## Core Features

### 1. File Reading
- Use `scripts/read_file.py` to read various document formats
- **Enhanced**:
  - PDF table extraction (converted to Markdown)
  - Semantic chunking (by paragraphs/headings)
  - PPT image OCR extraction

### 2. Incremental Knowledge Base Building
- Incremental update based on file hash
- Skip unchanged documents
- Support batch import

### 3. Knowledge Graph Building
- Rule-based matching + entity disambiguation
- LLM refinement (optional, requires API Key)
- Support custom domain entity types

### 4. Hybrid Search
- Two-stage retrieval: keywords + entity associations
- Entity disambiguation and alias support

### 5. Efficient Graph Query
- Memory index pre-loading
- Path finding, neighbor queries

---

## Storage Structure

```
~/.openclaw/workspace/knowledge_base/
├── kb_storage.db          # SQLite database
│   ├── entities          # Entity table (with aliases)
│   ├── relationships     # Relationship table
│   ├── doc_index         # Document index (with hash)
│   ├── chunks            # Text chunks
│   └── entity_alias      # Entity aliases
├── domain_config.json    # Domain configuration
├── processed/            # Processed text (optional)
└── backup/              # Backup directory
```

---

## Workflow

### Workflow 1: Add Documents to Knowledge Base

1. User provides document path
2. System checks file hash (incremental update)
3. Read file content (with tables, OCR)
4. Semantic chunking
5. Rule-based entity extraction (based on domain config)
6. Entity disambiguation and normalization
7. Extract relationships
8. Store to SQLite

**Commands:**
```bash
python scripts/build_graph.py <file_path> --rule-only
python scripts/build_graph.py <file_path> --llm-enhanced
```

### Workflow 2: User Q&A (Closed Loop)

1. **Keyword Analysis** → Extract key entities from the question
2. **SQL Lookup** → Search matching entities in entity table
3. **Graph Expansion** → Extract second-degree related nodes
4. **Text Retrieval** → Search relevant content in chunks
5. **Answer Generation** → Combine graph relationships and source text

**Commands:**
```bash
# Hybrid search (recommended)
python scripts/search.py "SMT capacity utilization"

# Graph query
python scripts/graph_query.py -e "MES"
python scripts/graph_query.py --path "MES" "production workshop"
python scripts/graph_query.py --neighbors "WMS" 2
```

### Workflow 3: Query Statistics

```bash
# View statistics
python scripts/search.py --stats

# List documents
python scripts/search.py --list

# Refresh index
python scripts/graph_query.py --refresh

# Domain configuration
python scripts/domain_config.py list
python scripts/domain_config.py set manufacturing
```

---

## Script Reference

### scripts/domain_config.py
- **Function**: Domain configuration tool
- **Usage:**
  - `domain_config.py list` - List available domains
  - `domain_config.py set <domain>` - Set domain
  - `domain_config.py current` - Show current domain

### scripts/kb_database.py
- **Function**: Database management module
- **API:**
  - `init_database()`: Initialize database and tables
  - `check_doc_needs_update(file_path)`: Check if document needs update
  - `add_entity()`: Add entity
  - `add_relationship()`: Add relationship
  - `add_document()`: Add document and chunks
  - `search_entities()`: Search entities
  - `get_entity_relations()`: Get entity relationships
  - `search_chunks()`: Search text chunks
  - `get_stats()`: Get statistics

### scripts/read_file.py
- **Function**: Read various document formats
- **Enhanced:**
  - PDF table extraction (to Markdown)
  - Semantic chunking (by paragraphs/headings)
  - PPT image OCR extraction
- **Usage:** `python read_file.py <file_path>`

### scripts/build_graph.py
- **Function**: Build knowledge graph
- **Parameters:**
  - `--rule-only`: Rule-based only (default)
  - `--llm-enhanced`: LLM refinement
- **Incremental**: Auto-skip unchanged documents
- **Disambiguation**: Auto-normalize entity names
- **Domain**: Loads entity types from domain_config.json

### scripts/search.py
- **Function**: Hybrid search
- **Modes:**
  - `hybrid`: Keywords + entity association (default)
  - `--entities <kw>`: Search entities only
  - `--chunks <kw>`: Search text only

### scripts/graph_query.py
- **Function**: Graph query
- **Parameters:**
  - `-e <entity>`: Query entity details
  - `--path <A> <B> [depth]`: Query path
  - `--neighbors <entity> [depth]`: Query N-degree associations
  - `-t [type]`: List entities by type
  - `--refresh`: Refresh memory index

---

## Q&A Process (Closed Loop Example)

### Example: User asks "How to optimize low SMT capacity utilization?"

```
【Step 1: Keyword Analysis】
   Extract: SMT, capacity utilization, optimization

【Step 2: SQL Lookup】
   → Found: SMT(process), capacity(metric), optimization(action)

【Step 3: Graph Expansion】
   SMT → associated with → equipment (AOI,贴片机)
   SMT → associated with → yield rate(metric)
   capacity → associated with → OEE(metric)

【Step 4: Text Retrieval】
   Search: SMT + capacity + optimization
   Found relevant chunks:
   - SMT process optimization solution.pdf
   - Capacity improvement best practices.docx

【Step 5: Answer Generation】
   Generate answer based on graph relationships and source content...
```

---

## Entity Types (Manufacturing Default Example)

### Manufacturing Entities

| Type | Description |
|------|-------------|
| Organization | Enterprise, department, team |
| Supplier | Raw material supplier, service provider |
| Material | Raw materials, components, parts |
| Product | Phone, tablet, watch |
| Process | SMT, assembly, testing |
| Equipment | Chip mounter, AOI tester |
| System | MES, WMS, ERP |
| Technology | Machine vision, digital twin |
| Metric | OEE, yield rate, capacity |
| Solution | Technical solution, plan |
| Pain Point | Problem, challenge, bottleneck |

### AI/ML Entities

| Type | Description |
|------|-------------|
| Domain | Machine learning, deep learning |
| Methodology | Supervised learning, unsupervised learning |
| Algorithm | Neural network, CNN, RNN |
| Technology | Backpropagation, gradient descent |
| Metric | Accuracy, recall, AUC |
| Platform | Sentosa, RapidMiner |

---

## Dependencies

```bash
# Core dependencies
pip install python-docx PyPDF2 pdfplumber openpyxl python-pptx requests

# PDF processing (recommended)
pip install pdfplumber

# Note: sqlite3 is included in Python standard library
# Note: pypdf is the new name for PyPDF2, recommended to install
pip install pypdf

# OCR support (optional, for simple text extraction)
pip install pytesseract pillow

# Windows users also need to install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
```

---

## Environment Variables

```bash
# LLM enhancement (optional)
set MINIMAX_API_KEY=your_api_key
```

---

## Output Examples

### Add Document
```
📥 Starting import: xxx.pdf
   Mode: rule-only
   ✓ Read, 15 chunks
   🔍 Found 8 candidate entities
   + New entities: 5
   + New relationships: 3

   📊 Graph stats: 128 entities, 382 relationships

==================================================
✅ Document imported successfully!
==================================================
```

### Search Results
```
Found 5 relevant results:

【Entity 1】SMT
   Type: Process
   → Associated: AOI(uses), chip mounter(uses), capacity(related)

【Document 1】SMT process optimization solution.pdf
   Matched: SMT, optimization
   Content: SMT process is surface mount technology...
```

### Domain Configuration
```
Available domains:
  • Manufacturing: 3C manufacturing, supply chain, equipment
  • Healthcare: Hospitals, medicine, diseases
  • Finance: Banking, securities, investment
  • Education: Schools, courses, students
  • Retail: Stores, products, inventory
  • General: General knowledge management

Please run: python domain_config.py set <domain_name>
```

---

Start using the rebuilt knowledge base! 🚀
