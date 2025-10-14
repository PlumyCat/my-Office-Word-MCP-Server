#!/usr/bin/env python3
"""
Test du workflow principal: Génération de proposition commerciale depuis template.

Scénario:
1. Lister les templates disponibles
2. Créer un document depuis template-text.docx
3. Remplacer les variables:
   - {{commercialName}} → John Do
   - {{commercialEmail}} → j.do@mail.com
   - {{commercialTel}} → 01 02 03 04 05
   - {{propalContent}} → Tableau des offres Microsoft 365
4. Vérifier le document généré
5. Télécharger pour validation
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional

# Configuration
BASE_URL = "https://word-mcp-connector.ashywater-9eb5a210.francecentral.azurecontainerapps.io"
API_KEY = "GV2yMslJIvxtjtMej932Sg9L3xrT6rMPmKLEqX2caSA="
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Données de test
TEST_DATA = {
    "commercialName": "John Do",
    "commercialEmail": "j.do@mail.com",
    "commercialTel": "01 02 03 04 05",
    "propalContent": """| **Désignation** | **Description** | **Qté** | **Prix unitaire** | **Prix total** |
|------------------|------------------|---------|-------------------|----------------|
| Microsoft 365 Business Premium *(limite 300 users)* | Pack bureautique installable et online – Exchange Online 50Go – OneDrive 1To – SharePoint 1To – Teams – Gestion/sécurité des postes – Gestion/sécurité des identités & gestion/sécurité des données d'entreprise | 1 | 20,60 € HT/mois/user | € HT/mois |
| Microsoft 365 Business Standard *(limite 300 users)* | Pack bureautique installable et online – Exchange Online 50Go – OneDrive 1To – SharePoint 1To – Teams | 1 | 11,70 € HT/mois/user | € HT/mois |
| Microsoft 365 Business Basic *(limite 300 users)* | Pack bureautique online – Exchange Online 50Go – OneDrive 1To – SharePoint 1To – Teams | 1 | 5,60 € HT/mois/user | € HT/mois |
| Microsoft 365 Apps for Business | Pack bureautique installable et online – OneDrive 1To | 1 | 9,80 € HT/mois/user | € HT/mois |
| Microsoft 365 Apps for Entreprise | Pack bureautique installable et online – OneDrive 1To – Fonctionnalité ProPlus | 1 | 14,30 € HT/mois/user | € HT/mois |
| Office 365 Plan E3 | Pack bureautique installable et online – Exchange Online 100Go – OneDrive 1To – SharePoint 1To – Teams | 1 | 25,10 € HT/mois/user | € HT/mois |
| Microsoft 365 E3 | Office 365 Plan E3 + Enterprise Mobility & Security E3 | 1 | 39,30 € HT/mois/user | € HT/mois |"""
}

class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(step: int, message: str):
    """Print step with formatting."""
    print(f"\n{Color.BLUE}{Color.BOLD}[STEP {step}]{Color.END} {message}")

def print_success(message: str):
    """Print success message."""
    print(f"{Color.GREEN}✅ {message}{Color.END}")

def print_error(message: str):
    """Print error message."""
    print(f"{Color.RED}❌ {message}{Color.END}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Color.YELLOW}⚠️  {message}{Color.END}")

def print_info(message: str):
    """Print info message."""
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
            return False, {"error": response.text}, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return False, {"error": str(e)}, elapsed


def test_workflow():
    """Execute complete workflow test."""
    print("=" * 80)
    print(f"{Color.BOLD}🧪 TEST WORKFLOW COMPLET - GÉNÉRATION PROPOSITION COMMERCIALE{Color.END}")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        "timestamp": datetime.now().isoformat(),
        "steps": [],
        "success": False,
        "total_time": 0
    }

    workflow_start = time.time()

    # ========================================================================
    # STEP 1: List available templates
    # ========================================================================
    print_step(1, "Liste des templates disponibles")
    success, response, elapsed = api_call("GET", "/api/list/all/templates")

    results["steps"].append({
        "step": 1,
        "name": "list_templates",
        "success": success,
        "time": elapsed
    })

    if not success:
        print_error(f"Échec de la liste des templates: {response.get('error')}")
        return results

    templates_data = response.get("result", "{}")
    try:
        templates = json.loads(templates_data)
        template_names = [t["name"] for t in templates.get("templates", [])]
        print_success(f"Trouvé {len(template_names)} templates")

        # Check if target templates exist
        target_templates = ["template-text", "template-placeholders"]
        available = [t for t in target_templates if t in template_names]

        if not available:
            print_error(f"Templates cibles non trouvés: {target_templates}")
            print_info(f"Templates disponibles: {template_names}")
            return results

        selected_template = available[0]
        print_info(f"Template sélectionné: {selected_template}")

    except json.JSONDecodeError as e:
        print_error(f"Erreur parsing templates: {e}")
        return results

    # ========================================================================
    # STEP 2: Create document from template
    # ========================================================================
    print_step(2, f"Création document depuis template '{selected_template}'")

    output_filename = f"proposal_{TEST_DATA['commercialName'].replace(' ', '_').lower()}_{int(time.time())}.docx"

    create_body = {
        "template_name": selected_template,
        "new_document_name": output_filename,
        "category": "general",
        "variables": {
            "commercialName": TEST_DATA["commercialName"],
            "commercialEmail": TEST_DATA["commercialEmail"],
            "commercialTel": TEST_DATA["commercialTel"],
            "propalContent": TEST_DATA["propalContent"]
        }
    }

    success, response, elapsed = api_call("POST", "/api/create/document/from/template", create_body)

    results["steps"].append({
        "step": 2,
        "name": "create_from_template",
        "success": success,
        "time": elapsed,
        "document": output_filename
    })

    if not success:
        print_error(f"Échec création document: {response.get('error')}")
        print_info(f"Body envoyé: {json.dumps(create_body, indent=2)}")
        return results

    print_success(f"Document créé: {output_filename}")
    print_info(f"Temps: {elapsed:.2f}s")

    # ========================================================================
    # STEP 3: Verify document exists
    # ========================================================================
    print_step(3, "Vérification de l'existence du document")

    success, response, elapsed = api_call("POST", "/api/check/document/exists", {
        "filename": output_filename
    })

    results["steps"].append({
        "step": 3,
        "name": "check_exists",
        "success": success,
        "time": elapsed
    })

    if not success:
        print_warning("Document non trouvé immédiatement (peut être normal)")
    else:
        print_success("Document existe dans le stockage")

    # ========================================================================
    # STEP 4: Get document info
    # ========================================================================
    print_step(4, "Récupération des informations du document")

    success, response, elapsed = api_call("POST", "/api/get/document/info", {
        "filename": output_filename
    })

    results["steps"].append({
        "step": 4,
        "name": "get_info",
        "success": success,
        "time": elapsed
    })

    if success:
        doc_info = response.get("result", "")
        print_success("Informations récupérées")
        print_info(f"Détails: {doc_info[:200]}...")
    else:
        print_warning(f"Impossible de récupérer les infos: {response.get('error')}")

    # ========================================================================
    # STEP 5: Download document URL
    # ========================================================================
    print_step(5, "Génération du lien de téléchargement")

    success, response, elapsed = api_call("POST", "/api/download/document", {
        "filename": output_filename
    })

    results["steps"].append({
        "step": 5,
        "name": "download_url",
        "success": success,
        "time": elapsed
    })

    if success:
        download_info = response.get("result", "")
        print_success("Lien de téléchargement généré")

        # Extract URL from response
        if "URL:" in download_info:
            url_line = [line for line in download_info.split('\n') if 'URL:' in line]
            if url_line:
                download_url = url_line[0].split('URL:')[1].strip()
                print_info(f"URL: {download_url[:80]}...")
                results["download_url"] = download_url
        else:
            print_info("Voir résultat complet dans le rapport JSON")
    else:
        print_error(f"Échec génération lien: {response.get('error')}")

    # ========================================================================
    # STEP 6: Verify replacements (optional - read document text)
    # ========================================================================
    print_step(6, "Vérification des remplacements de variables")

    success, response, elapsed = api_call("POST", "/api/get/document/text", {
        "filename": output_filename
    })

    results["steps"].append({
        "step": 6,
        "name": "verify_replacements",
        "success": success,
        "time": elapsed
    })

    if success:
        doc_text = response.get("result", "")

        # Check if variables were replaced
        checks = {
            "commercialName": TEST_DATA["commercialName"] in doc_text,
            "commercialEmail": TEST_DATA["commercialEmail"] in doc_text,
            "commercialTel": TEST_DATA["commercialTel"] in doc_text,
            "propalContent": "Microsoft 365" in doc_text
        }

        all_replaced = all(checks.values())

        if all_replaced:
            print_success("Toutes les variables ont été remplacées")
            for var, found in checks.items():
                print_info(f"  ✓ {var}")
        else:
            print_warning("Certaines variables n'ont pas été remplacées")
            for var, found in checks.items():
                status = "✓" if found else "✗"
                print_info(f"  {status} {var}")

        results["replacements_ok"] = all_replaced
    else:
        print_warning("Impossible de vérifier les remplacements")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    workflow_time = time.time() - workflow_start
    results["total_time"] = workflow_time
    results["success"] = all(step["success"] for step in results["steps"])

    print()
    print("=" * 80)
    print(f"{Color.BOLD}📊 RÉSUMÉ DU WORKFLOW{Color.END}")
    print("=" * 80)

    success_count = sum(1 for step in results["steps"] if step["success"])
    print(f"Étapes réussies: {success_count}/{len(results['steps'])}")
    print(f"Temps total: {workflow_time:.2f}s")
    print(f"Document généré: {output_filename}")

    if results["success"]:
        print()
        print_success("✅ WORKFLOW COMPLET RÉUSSI!")
        print()
        print(f"{Color.GREEN}Le document de proposition a été généré avec succès.{Color.END}")
        if "download_url" in results:
            print(f"{Color.GREEN}Téléchargez-le pour vérification.{Color.END}")
    else:
        print()
        print_error("❌ WORKFLOW ÉCHOUÉ")
        failed_steps = [s for s in results["steps"] if not s["success"]]
        print(f"\nÉtapes en échec:")
        for step in failed_steps:
            print(f"  - Step {step['step']}: {step['name']}")

    # Save results
    with open("workflow_test_report.json", "w") as f:
        json.dump(results, f, indent=2)

    print()
    print(f"Rapport détaillé sauvegardé: workflow_test_report.json")
    print()

    return results


if __name__ == "__main__":
    try:
        results = test_workflow()
        exit(0 if results["success"] else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        exit(2)
    except Exception as e:
        print(f"\n\n💥 Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        exit(3)
