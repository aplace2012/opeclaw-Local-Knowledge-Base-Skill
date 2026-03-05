# -*- coding: utf-8 -*-
"""
Domain Configuration Tool
Run this script when first using to set your industry domain
"""
import os
import json
import sys

KB_DIR = os.path.expanduser("~/.openclaw/workspace/knowledge_base")
CONFIG_FILE = os.path.join(KB_DIR, "domain_config.json")

# Preset domain configurations
DOMAIN_PRESETS = {
    "manufacturing": {
        "name": "Manufacturing",
        "entity_types": {
            "Organization": ["Department", "Workshop", "Division", "Team", "Factory"],
            "Supplier": ["Supplier", "Vendor", "Service Provider", "Manufacturer"],
            "Material": ["Material", "Raw Material", "Component", "Part", "Component"],
            "Product": ["Phone", "Tablet", "Watch", "Terminal", "Product"],
            "Process": ["Process", "Technique", "Flow", "SMT", "Assembly", "Testing"],
            "Equipment": ["Equipment", "Machine", "Instrument", "Fixture"],
            "System": ["MES", "WMS", "ERP", "PLM", "SRM", "APS"],
            "Technology": ["AI", "Machine Vision", "Digital Twin", "Edge Computing", "IoT"],
            "Metric": ["OEE", "Yield Rate", "Capacity", "Utilization", "Turnover"],
            "Solution": ["Solution", "Plan", "Suggestion", "Strategy"],
            "Pain Point": ["Problem", "Difficulty", "Challenge", "Bottleneck", "Risk"]
        },
        "description": "3C Manufacturing, Supply Chain, Equipment"
    },
    "healthcare": {
        "name": "Healthcare",
        "entity_types": {
            "Department": ["Internal Medicine", "Surgery", "Pediatrics", "Gynecology", "Emergency"],
            "Disease": ["Hypertension", "Diabetes", "Pneumonia", "Heart Disease", "Cancer"],
            "Medicine": ["Aspirin", "Ibuprofen", "Cephalosporin", "Penicillin"],
            "Examination": ["Blood Test", "Urine Test", "CT", "MRI", "Ultrasound"],
            "Hospital": ["Hospital", "Clinic", "Health Center"],
            "Doctor": ["Chief Physician", "Associate Chief Physician", "Attending Physician"],
            "Patient": ["Patient"],
            "Treatment": ["Surgery", "Medication", "Physical Therapy"],
            "Equipment": ["CT Scanner", "MRI Machine", "Ultrasound", "Monitor"]
        },
        "description": "Medical Services, Medical Equipment"
    },
    "finance": {
        "name": "Finance",
        "entity_types": {
            "Institution": ["Bank", "Securities", "Insurance", "Fund"],
            "Product": ["Stock", "Bond", "Fund", "Insurance", "Wealth Management"],
            "Metric": ["Return Rate", "Risk Rate", "P/E Ratio", "P/B Ratio"],
            "Client": ["Individual Client", "Corporate Client", "Institutional Client"],
            "Transaction": ["Buy", "Sell", "Subscribe", "Redeem"],
            "Account": ["Savings Account", "Investment Account", "Credit Card"]
        },
        "description": "Banking, Securities, Insurance, Investment"
    },
    "education": {
        "name": "Education",
        "entity_types": {
            "School": ["University", "Middle School", "Primary School", "Kindergarten", "Training Institution"],
            "Student": ["Primary Student", "Middle School Student", "College Student", "Graduate Student"],
            "Teacher": ["Teacher", "Professor", "Instructor", "Coach"],
            "Course": ["Required Course", "Elective Course", "Open Course"],
            "Grade": ["Score", "GPA", "Ranking"],
            "Equipment": ["Projector", "Computer", "Whiteboard"]
        },
        "description": "Schools, Training, Online Education"
    },
    "retail": {
        "name": "Retail",
        "entity_types": {
            "Store": ["Supermarket", "Convenience Store", "Specialty Store", "Mall"],
            "Product": ["Food", "Daily Necessities", "Clothing", "Electronics"],
            "Client": ["Customer", "Member", "VIP Customer"],
            "Supplier": ["Brand Owner", "Distributor", "Agent"],
            "Inventory": ["Inbound", "Outbound", "Stock Check"],
            "Sales": ["Sales Amount", "Average Order Value", "Conversion Rate"]
        },
        "description": "Retail, E-commerce, Chain Stores"
    },
    "general": {
        "name": "General",
        "entity_types": {
            "Organization": ["Company", "Department", "Team", "Group"],
            "Person": ["CEO", "Director", "Manager", "Employee"],
            "Project": ["Project", "Task", "Milestone"],
            "Document": ["Report", "Plan", "Contract", "Solution"],
            "Tool": ["Software", "System", "Platform"],
            "Time": ["Date", "Time", "Deadline"]
        },
        "description": "General Knowledge Management"
    }
}

def load_config():
    """Load domain configuration"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_config(config):
    """Save domain configuration"""
    os.makedirs(KB_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def set_domain(domain_name):
    """Set domain"""
    domain_key = domain_name.lower()
    if domain_key not in DOMAIN_PRESETS:
        print(f"Unknown domain: {domain_name}")
        print(f"Available domains: {', '.join(DOMAIN_PRESETS.keys())}")
        return False
    
    config = {
        "domain": DOMAIN_PRESETS[domain_key]["name"],
        "entity_types": DOMAIN_PRESETS[domain_key]["entity_types"],
        "description": DOMAIN_PRESETS[domain_key]["description"]
    }
    
    save_config(config)
    print(f"Domain set to: {DOMAIN_PRESETS[domain_key]['name']}")
    print(f"Description: {config['description']}")
    return True

def list_domains():
    """List available domains"""
    print("\nAvailable domains:")
    for key, info in DOMAIN_PRESETS.items():
        print(f"  - {key}: {info['description']}")
    print()

def show_current_domain():
    """Show current domain"""
    config = load_config()
    if config:
        print(f"\nCurrent domain: {config['domain']}")
        print(f"Description: {config['description']}")
        print(f"Entity types: {', '.join(config['entity_types'].keys())}")
    else:
        print("\nNo domain set. Run: python domain_config.py set <domain>")
    print()

def main():
    if len(sys.argv) < 2:
        print("=" * 50)
        print("Domain Configuration Tool")
        print("=" * 50)
        print("\nUsage:")
        print("  python domain_config.py list        - List available domains")
        print("  python domain_config.py current     - Show current domain")
        print("  python domain_config.py set <domain> - Set domain")
        print()
        show_current_domain()
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_domains()
    elif command == "current":
        show_current_domain()
    elif command == "set":
        if len(sys.argv) < 3:
            print("Please specify domain name")
            print("Available domains: ", ", ".join(DOMAIN_PRESETS.keys()))
        else:
            domain_name = sys.argv[2]
            set_domain(domain_name)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
