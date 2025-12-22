import os

def load_comprehensive_rules() -> str:
    """
    Loads the comprehensive rules from the text file.
    Returns the content as a string.
    """
    # Adjust path relative to this file or project root
    # Assuming project structure:
    # app/services/rule_loader.py
    # data/rules/comprehensive_rules.txt
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    rule_path = os.path.join(project_root, "data", "rules", "comprehensive_rules.txt")
    
    try:
        with open(rule_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Rules file not found at: " + rule_path
    except Exception as e:
        return f"Error loading rules: {str(e)}"
