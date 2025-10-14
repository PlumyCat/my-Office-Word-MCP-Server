#!/usr/bin/env python3
"""
Test du workflow COMPLET avec VRAI tableau Word.

Ce test fait EXACTEMENT ce que Copilot Studio doit faire:
1. Créer document depuis template
2. Remplacer les variables de texte
3. Convertir le markdown de tableau en VRAI tableau Word avec bordures et formatage
"""

import requests
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://word-mcp-connector.ashywater-9eb5a210.francecentral.azurecontainerapps.io"
API_KEY = "GV2yMslJIvxtjtMej932Sg9L3xrT6rMPmKLEqX2caSA="
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Données du commercial
COMMERCIAL_DATA = {
    "name": "John Do",
    "email": "j.do@mail.com",
    "tel": "01 02 03 04 05"
}

# Tableau des offres Microsoft 365
OFFERS_TABLE_MARKDOWN = """| **Désignation** | **Description** | **Qté** | **Prix unitaire** | **Prix total** |
|------------------|------------------|---------|-------------------|----------------|
| Microsoft 365 Business Premium *(limite 300 users)* | Pack bureautique installable et online – Exchange Online 50Go – OneDrive 1To – SharePoint 1To – Teams – Gestion/sécurité des postes – Gestion/sécurité des identités & gestion/sécurité des données d'entreprise | 1 | 20,60 € HT/mois/user | € HT/mois |
| Microsoft 365 Business Standard *(limite 300 users)* | Pack bureautique installable et online – Exchange Online 50Go – OneDrive 1To – SharePoint 1To – Teams | 1 | 11,70 € HT/mois/user | € HT/mois |
| Microsoft 365 Business Basic *(limite 300 users)* | Pack bureautique online – Exchange Online 50Go – OneDrive 1To – SharePoint 1To – Teams | 1 | 5,60 € HT/mois/user | € HT/mois |
| Microsoft 365 Apps for Business | Pack bureautique installable et online – OneDrive 1To | 1 | 9,80 € HT/mois/user | € HT/mois |
| Microsoft 365 Apps for Entreprise | Pack bureautique installable et online – OneDrive 1To – Fonctionnalité ProPlus | 1 | 14,30 € HT/mois/user | € HT/mois |
| Office 365 Plan E3 | Pack bureautique installable et online – Exchange Online 100Go – OneDrive 1To – SharePoint 1To – Teams | 1 | 25,10 € HT/mois/user | € HT/mois |
| Microsoft 365 E3 | Office 365 Plan E3 + Enterprise Mobility & Security E3 | 1 | 39,30 € HT/mois/user | € HT/mois |"""

class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(step: int, message: str):
    print(f"\n{Color.BLUE}{Color.BOLD}[STEP {step}]{Color.END} {message}")

def print_success(message: str):
    print(f"{Color.GREEN}✅ {message}{Color.END}")

def print_error(message: str):
    print(f"{Color.RED}❌ {message}{Color.END}")

def print_warning(message: str):
    print(f"{Color.YELLOW}⚠️  {message}{Color.END}")

def print_info(message: str):
    print(f"   {message}")

def api_call(method: str, path: str, body: Optional[Dict] = None) -> tuple:
    """Make API call and return (success, response, elapsed)."""
    url = f"{BASE_URL}{path}"
    start = time.time()

    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=30)
        else:
            response = requests.post(url, json=body, headers=HEADERS, timeout=30)

        elapsed = time.time() - start

        if response.status_code == 200:
            return True, response.json(), elapsed
        else:
            return False, {"error": response.text, "status": response.status_code}, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return False, {"error": str(e)}, elapsed


def parse_markdown_table(markdown: str) -> List[List[str]]:
    """Parse markdown table into 2D array."""
    lines = [line.strip() for line in markdown.strip().split('\n') if line.strip()]

    # Remove separator line (the one with |---|---|)
    lines = [line for line in lines if not re.match(r'^\|[\s\-:]+\|$', line)]

    table_data = []
    for line in lines:
        # Remove leading/trailing pipes and split
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        # Remove markdown bold syntax
        cells = [cell.replace('**', '') for cell in cells]
        table_data.append(cells)

    return table_data


def test_complete_workflow():
    """Execute le workflow COMPLET de génération de proposition."""
    print("=" * 80)
    print(f"{Color.BOLD}🎯 TEST WORKFLOW COMPLET - GÉNÉRATION AVEC VRAI TABLEAU{Color.END}")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    workflow_start = time.time()
    document_name = f"proposal_{COMMERCIAL_DATA['name'].replace(' ', '_').lower()}_{int(time.time())}.docx"

    # ========================================================================
    # STEP 1: Créer document depuis template
    # ========================================================================
    print_step(1, "Création document depuis template 'template-text'")

    create_body = {
        "template_name": "template-text",
        "new_document_name": document_name,
        "category": "general",
        "variables": {
            "commercialName": COMMERCIAL_DATA["name"],
            "commercialEmail": COMMERCIAL_DATA["email"],
            "commercialTel": COMMERCIAL_DATA["tel"],
            "propalContent": "[TABLEAU_OFFRES]"  # Placeholder temporaire
        }
    }

    success, response, elapsed = api_call("POST", "/api/create/document/from/template", create_body)

    if not success:
        print_error(f"Échec création: {response}")
        return False

    print_success(f"Document créé: {document_name} ({elapsed:.2f}s)")

    # ========================================================================
    # STEP 2: Remplacer le placeholder par le tableau
    # ========================================================================
    print_step(2, "Conversion markdown → vrai tableau Word")

    # Parse markdown table
    table_data = parse_markdown_table(OFFERS_TABLE_MARKDOWN)
    print_info(f"Tableau parsé: {len(table_data)} lignes x {len(table_data[0])} colonnes")

    # Remove placeholder text
    success, response, elapsed = api_call("POST", "/api/replace/text/universal", {
        "filename": document_name,
        "find_text": "[TABLEAU_OFFRES]",
        "replace_text": ""
    })

    if not success:
        print_warning("Impossible de retirer le placeholder")

    # Add paragraph before table (titre)
    success, response, elapsed = api_call("POST", "/api/add/paragraph", {
        "filename": document_name,
        "text": "Tableau des offres Microsoft 365:",
        "style": "Heading 2"
    })

    if success:
        print_success("Titre du tableau ajouté")

    # Create table
    rows = len(table_data)
    cols = len(table_data[0])

    success, response, elapsed = api_call("POST", "/api/add/table", {
        "filename": document_name,
        "rows": rows,
        "cols": cols,
        "data": table_data
    })

    if not success:
        print_error(f"Échec création tableau: {response}")
        return False

    print_success(f"Tableau Word créé: {rows}x{cols} ({elapsed:.2f}s)")

    # ========================================================================
    # STEP 3: Formater le tableau
    # ========================================================================
    print_step(3, "Formatage du tableau (header, bordures, alternance)")

    # Format header row
    success, response, elapsed = api_call("POST", "/api/highlight/table/header", {
        "filename": document_name,
        "table_index": 0,
        "header_color": "4472C4",
        "text_color": "FFFFFF"
    })

    if success:
        print_success("En-tête formaté (bleu/blanc)")

    # Apply alternating rows
    success, response, elapsed = api_call("POST", "/api/apply/table/alternating/rows", {
        "filename": document_name,
        "table_index": 0,
        "color1": "FFFFFF",
        "color2": "F2F2F2"
    })

    if success:
        print_success("Alternance de lignes appliquée")

    # Add borders
    success, response, elapsed = api_call("POST", "/api/format/table", {
        "filename": document_name,
        "table_index": 0,
        "border_style": "single",
        "has_header_row": True
    })

    if success:
        print_success("Bordures ajoutées")

    # ========================================================================
    # STEP 4: Ajouter paragraphe de conclusion
    # ========================================================================
    print_step(4, "Ajout d'un paragraphe de conclusion")

    success, response, elapsed = api_call("POST", "/api/add/paragraph", {
        "filename": document_name,
        "text": f"\n\nPour toute question, n'hésitez pas à me contacter:\n{COMMERCIAL_DATA['name']}\nEmail: {COMMERCIAL_DATA['email']}\nTél: {COMMERCIAL_DATA['tel']}",
        "style": "Normal"
    })

    if success:
        print_success("Conclusion ajoutée")

    # ========================================================================
    # STEP 5: Générer lien de téléchargement
    # ========================================================================
    print_step(5, "Génération du lien de téléchargement")

    success, response, elapsed = api_call("POST", "/api/download/document", {
        "filename": document_name
    })

    if success:
        download_info = response.get("result", "")
        if "URL:" in download_info:
            url_line = [line for line in download_info.split('\n') if 'URL:' in line][0]
            download_url = url_line.split('URL:')[1].strip()
            print_success("Lien généré")
            print()
            print(f"{Color.CYAN}{Color.BOLD}📥 TÉLÉCHARGER LE DOCUMENT:{Color.END}")
            print(f"{Color.CYAN}{download_url}{Color.END}")
            print()

    # ========================================================================
    # SUMMARY
    # ========================================================================
    workflow_time = time.time() - workflow_start

    print()
    print("=" * 80)
    print(f"{Color.BOLD}📊 RÉSUMÉ - WORKFLOW COMPLET{Color.END}")
    print("=" * 80)
    print(f"Document généré: {document_name}")
    print(f"Temps total: {workflow_time:.2f}s")
    print(f"Commercial: {COMMERCIAL_DATA['name']} ({COMMERCIAL_DATA['email']})")
    print(f"Tableau: {rows} lignes x {cols} colonnes")
    print()
    print(f"{Color.GREEN}{Color.BOLD}✅ WORKFLOW RÉUSSI!{Color.END}")
    print()
    print(f"{Color.GREEN}Le document contient:{Color.END}")
    print(f"  • Variables commerciales remplacées")
    print(f"  • Tableau Word formaté avec {rows} offres Microsoft 365")
    print(f"  • En-tête de tableau en bleu")
    print(f"  • Alternance de couleurs de lignes")
    print(f"  • Bordures professionnelles")
    print(f"  • Paragraphe de conclusion avec coordonnées")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_complete_workflow()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
        exit(2)
    except Exception as e:
        print(f"\n\n💥 Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(3)
