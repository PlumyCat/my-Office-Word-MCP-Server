#!/usr/bin/env python3
"""
Test automatique de TOUS les outils du connecteur Word MCP.
Génère un rapport HTML avec le statut de chaque endpoint.
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
BASE_URL = "https://word-mcp-connector.ashywater-9eb5a210.francecentral.azurecontainerapps.io"
API_KEY = "GV2yMslJIvxtjtMej932Sg9L3xrT6rMPmKLEqX2caSA="
HEADERS = {"X-API-Key": API_KEY}

# Données de test
TEST_DATA = {
    "filename": "test_document.docx",
    "text": "Test paragraph",
    "title": "Test Title",
    "template_name": "my_first_template",
    "category": "general",
    "search_text": "test",
    "author": "Test Author",
    "paragraph_index": 0,
}

def test_endpoint(method: str, path: str, params: Dict = None) -> Tuple[bool, str, float, str]:
    """
    Test un endpoint et retourne (success, status_code, response_time, message).
    """
    # Add /api prefix if not present
    if not path.startswith("/api/"):
        path = f"/api{path}"
    url = f"{BASE_URL}{path}"
    start = time.time()

    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=30)
        else:  # POST
            # Prepare minimal valid data based on path
            body = {}
            if params:
                body = params
            elif "filename" in path or "document" in path:
                body = {"filename": TEST_DATA["filename"]}
            elif "template" in path:
                body = {"template_name": TEST_DATA["template_name"]}
            elif "text" in path:
                body = {"text": TEST_DATA["text"]}

            response = requests.post(url, json=body, headers=HEADERS, timeout=30)

        elapsed = time.time() - start

        # Check response
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                return True, "200 OK", elapsed, f"✅ Success ({len(str(data['result']))} chars)"
            else:
                return False, "200", elapsed, "⚠️  No 'result' in response"
        elif response.status_code == 400:
            return False, "400", elapsed, "❌ Bad Request (invalid params)"
        elif response.status_code == 404:
            return False, "404", elapsed, "❌ Not Found"
        elif response.status_code == 401:
            return False, "401", elapsed, "❌ Unauthorized"
        else:
            return False, str(response.status_code), elapsed, f"❌ {response.text[:100]}"

    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        return False, "TIMEOUT", elapsed, "⏱️  Timeout (>30s)"
    except Exception as e:
        elapsed = time.time() - start
        return False, "ERROR", elapsed, f"💥 Exception: {str(e)[:100]}"


def load_swagger() -> Dict:
    """Load swagger definition."""
    with open("word-connector.swagger.json") as f:
        return json.load(f)


def test_all_tools():
    """Test tous les outils et génère un rapport."""
    swagger = load_swagger()
    results = []

    print("🔍 Testing all endpoints...")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
    print(f"📊 Total endpoints: {len(swagger['paths'])}\n")

    for i, (path, methods) in enumerate(swagger["paths"].items(), 1):
        for method, definition in methods.items():
            method_upper = method.upper()
            summary = definition.get("summary", "No summary")

            print(f"[{i}/{len(swagger['paths'])}] Testing {method_upper} {path}...")

            # Determine test params
            params = None
            if method == "post" and "parameters" in definition:
                # Extract required params from swagger
                param_def = definition["parameters"][0]
                if "schema" in param_def and "properties" in param_def["schema"]:
                    props = param_def["schema"]["properties"]
                    required = param_def["schema"].get("required", [])
                    params = {}
                    for req in required[:3]:  # Only test first 3 required params
                        if req in TEST_DATA:
                            params[req] = TEST_DATA[req]

            # Test endpoint
            success, status, elapsed, message = test_endpoint(method_upper, path, params)

            results.append({
                "path": path,
                "method": method_upper,
                "summary": summary,
                "success": success,
                "status": status,
                "response_time": round(elapsed, 2),
                "message": message
            })

            print(f"  → {status} in {elapsed:.2f}s - {message}\n")

            # Small delay to avoid rate limiting
            time.sleep(0.5)

    return results


def generate_html_report(results: List[Dict]):
    """Génère un rapport HTML."""
    total = len(results)
    success_count = sum(1 for r in results if r["success"])
    fail_count = total - success_count
    avg_time = sum(r["response_time"] for r in results) / total

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Word MCP Connector Test Report</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0;
            font-size: 36px;
            color: #2c3e50;
        }}
        .stat-card p {{
            margin: 5px 0 0;
            color: #7f8c8d;
        }}
        .success {{ background: #d4edda; color: #155724; }}
        .fail {{ background: #f8d7da; color: #721c24; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-success {{ background: #28a745; color: white; }}
        .badge-danger {{ background: #dc3545; color: white; }}
        .badge-warning {{ background: #ffc107; color: black; }}
        .method-get {{ color: #28a745; }}
        .method-post {{ color: #007bff; }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Word MCP Connector - Test Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <div class="stats">
            <div class="stat-card">
                <h3>{total}</h3>
                <p>Total Endpoints</p>
            </div>
            <div class="stat-card success">
                <h3>{success_count}</h3>
                <p>Succès ({success_count/total*100:.1f}%)</p>
            </div>
            <div class="stat-card fail">
                <h3>{fail_count}</h3>
                <p>Échecs ({fail_count/total*100:.1f}%)</p>
            </div>
            <div class="stat-card">
                <h3>{avg_time:.2f}s</h3>
                <p>Temps Moyen</p>
            </div>
        </div>

        <h2>📋 Détails des Tests</h2>
        <table>
            <thead>
                <tr>
                    <th>Method</th>
                    <th>Path</th>
                    <th>Summary</th>
                    <th>Status</th>
                    <th>Time</th>
                    <th>Result</th>
                </tr>
            </thead>
            <tbody>
"""

    for r in results:
        method_class = f"method-{r['method'].lower()}"
        status_badge = "badge-success" if r["success"] else "badge-danger"

        html += f"""
                <tr>
                    <td class="{method_class}"><strong>{r['method']}</strong></td>
                    <td><code>{r['path']}</code></td>
                    <td>{r['summary'][:60]}</td>
                    <td><span class="badge {status_badge}">{r['status']}</span></td>
                    <td>{r['response_time']}s</td>
                    <td>{r['message']}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    with open("test_report.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ Rapport HTML généré: test_report.html")


def generate_json_report(results: List[Dict]):
    """Génère un rapport JSON."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "total": len(results),
        "success": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "avg_response_time": round(sum(r["response_time"] for r in results) / len(results), 2),
        "results": results
    }

    with open("test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ Rapport JSON généré: test_report.json")


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 WORD MCP CONNECTOR - TEST AUTOMATIQUE")
    print("=" * 80)
    print()

    results = test_all_tools()

    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 80)

    total = len(results)
    success = sum(1 for r in results if r["success"])
    failed = total - success

    print(f"✅ Succès: {success}/{total} ({success/total*100:.1f}%)")
    print(f"❌ Échecs: {failed}/{total} ({failed/total*100:.1f}%)")
    print(f"⏱️  Temps moyen: {sum(r['response_time'] for r in results)/total:.2f}s")

    if failed > 0:
        print(f"\n⚠️  Échecs détectés:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['method']} {r['path']}: {r['message']}")

    print("\n📄 Génération des rapports...")
    generate_html_report(results)
    generate_json_report(results)

    print("\n✅ Tests terminés!")
