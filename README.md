# opeclaw-Local-Knowledge-Base-Skill
# Local Knowledge Base Skill

A universal local knowledge base Q&A system that supports extracting knowledge from various documents and building knowledge graphs.

## Features

- **Multi-format Support**: PDF, Word, Excel, PPT, TXT, Markdown
- **SQLite Storage**: Efficient local database storage
- **Incremental Update**: Based on file hash, only process changed documents
- **Knowledge Graph**: Auto-extract entities and relationships
- **Hybrid Search**: Keywords + entity association retrieval
- **OCR Support**: Extract text from images
- **LLM Enhancement**: Optional AI-powered entity recognition
- **Domain Customization**: Support for multiple industry domains

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. First Use - Set Domain

```bash
# List available domains
python scripts/domain_config.py list

# Set your domain
python scripts/domain_config.py set manufacturing
```

### 3. Import Documents

```bash
python scripts/build_graph.py your_document.pdf --rule-only
```

### 4. Query Knowledge Base

```bash
# Search
python scripts/search.py "your query"

# Graph query
python scripts/graph_query.py -e "entity name"
python scripts/graph_query.py --path "entity A" "entity B"
```

## Preset Domains

| Domain | Description |
|--------|-------------|
| Manufacturing | 3C manufacturing, supply chain, equipment |
| Healthcare | Hospitals, medicine, diseases |
| Finance | Banking, securities, investment |
| Education | Schools, courses, students |
| Retail | Stores, products, inventory |
| General | General knowledge management |

## Directory Structure

```
.
├── README.md
├── SKILL.md
├── requirements.txt
├── LICENSE
├── .gitignore
└── scripts/
    ├── domain_config.py           # Domain configuration tool
    ├── build_graph.py           # Build knowledge graph
    ├── read_file.py             # Read documents
    ├── search.py                # Hybrid search
    ├── graph_query.py           # Graph query
    ├── kb_database.py           # Database management
    ├── llm_enhancer.py         # LLM enhancement
    └── industry_config_example.py  # Industry config example
```

## Usage Examples

### Import PDF Documents

```bash
python scripts/build_graph.py document.pdf --rule-only
python scripts/build_graph.py document.pdf --llm-enhanced
```

### Search Knowledge

```bash
python scripts/search.py "machine learning"
python scripts/search.py --entities "AI"
python scripts/search.py --chunks "neural network"
```

### Query Entity Relationships

```bash
python scripts/graph_query.py -e "artificial intelligence"
python scripts/graph_query.py --path "artificial intelligence" "machine learning"
python scripts/graph_query.py --neighbors "MES" 2
python scripts/graph_query.py -t "system"
```

### View Statistics

```bash
python scripts/search.py --stats
python scripts/search.py --list
```

### Domain Configuration

```bash
python scripts/domain_config.py list
python scripts/domain_config.py set healthcare
python scripts/domain_config.py current
```

## Configuration

### Knowledge Base Path

Default: `~/.openclaw/workspace/knowledge_base/`

### Environment Variables

```bash
# LLM enhancement (optional)
set MINIMAX_API_KEY=your_api_key
```

### Custom Domains

To customize industry-specific entity types:

1. Use preset domains: `python scripts/domain_config.py set <domain>`
2. Or modify `scripts/industry_config_example.py` to create custom configuration

## Dependencies

- python-docx
- PyPDF2 / pdfplumber
- openpyxl
- python-pptx
- requests
- pillow (optional)
- pytesseract (optional, requires Tesseract OCR installation)

## FAQ

**Q: OCR not working**
A: Make sure Tesseract OCR is installed and added to system PATH

**Q: LLM enhancement not working**
A: Make sure MINIMAX_API_KEY environment variable is set

**Q: How to add new domains?**
A: Reference `scripts/industry_config_example.py` to create custom configuration

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

