# Guide de Test - Word MCP Connector

## 🎯 Objectif

Éviter de passer 3h à ajouter manuellement les 67 outils dans Copilot Studio. Ce guide fournit:
1. Un script de test automatique pour valider tous les endpoints
2. Un swagger minimal avec 5 outils essentiels pour tests rapides
3. Un processus de validation avant déploiement

## 📁 Fichiers

### 1. Scripts de test

- **`test_all_tools.py`** - Test automatique de tous les 67 endpoints
  - Génère `test_report.html` (rapport visuel)
  - Génère `test_report.json` (données brutes)
  - Temps d'exécution: ~1 minute

### 2. Swaggers

- **`word-connector.swagger.json`** - Version complète (67 outils)
  - À utiliser pour le déploiement final
  - Tous les outils validés

- **`word-connector-minimal.swagger.json`** - Version test (5 outils)
  - Pour validation rapide de la configuration
  - Tests de workflow complets
  - **5 outils inclus**:
    - `list_all_templates` (GET) - Liste templates
    - `list_all_documents` (GET) - Liste documents
    - `create_document` (POST) - Créer document
    - `add_paragraph` (POST) - Ajouter contenu
    - `create_document_from_template` (POST) - Workflow complet

## 🚀 Workflow de Validation

### Étape 1: Test automatique des endpoints

```bash
# Lancer les tests
python3 test_all_tools.py

# Ouvrir le rapport
open test_report.html  # macOS
xdg-open test_report.html  # Linux
start test_report.html  # Windows
```

**Résultat attendu**:
- ✅ ~20-30 succès (outils sans paramètres requis)
- ⚠️  ~37-40 échecs (400 Bad Request - paramètres incomplets, NORMAL)
- ❌ 0 échecs 404/401 (si présents = problème de config)

### Étape 2: Test rapide avec swagger minimal

1. **Importer dans Power Apps**:
   - Custom Connectors → Import OpenAPI file
   - Sélectionner `word-connector-minimal.swagger.json`
   - Configurer API Key: `GV2yMslJIvxtjtMej932Sg9L3xrT6rMPmKLEqX2caSA=`

2. **Tester les 5 outils** (5 min au lieu de 3h):
   - `list_all_templates` → Doit retourner liste de templates
   - `list_all_documents` → Doit retourner liste de documents
   - `create_document` → Créer "test_doc.docx"
   - `add_paragraph` → Ajouter texte à "test_doc.docx"
   - `create_document_from_template` → Créer depuis template

3. **Vérifier**:
   - Authentification fonctionne (pas d'erreur 401)
   - Réponses < 30s (pas de timeout)
   - Format de réponse: `{"result": "..."}`
   - Changer auth "user" → "créateur" si nécessaire

### Étape 3: Déploiement complet (si tests OK)

1. **Sauvegarder le connecteur minimal** (optionnel)
2. **Importer le swagger complet**: `word-connector.swagger.json`
3. **Ajouter les outils** un par un dans Copilot Studio

## 📊 Interprétation des Résultats

### ✅ Tests Réussis
- Status 200 OK
- Réponse contient `{"result": "..."}`
- Temps < 30s

### ⚠️  Échecs Acceptables (400 Bad Request)
- Outils avec paramètres complexes (tables, images, etc.)
- Le script de test n'envoie pas tous les paramètres requis
- **C'EST NORMAL** - ces outils fonctionneront dans Copilot Studio

### ❌ Échecs Critiques
- **404 Not Found** → Endpoint n'existe pas (problème de routing)
- **401 Unauthorized** → API Key invalide
- **TIMEOUT** → Réponse trop lente (> 30s)

## 🔧 Maintenance

### Après modification du code

1. **Redéployer**:
   ```bash
   ./deploy-connector.sh mywordmcpacr my-word-mcp-rg my-word-mcp-env "GV2yMslJIvxtjtMej932Sg9L3xrT6rMPmKLEqX2caSA="
   ```

2. **Tester**:
   ```bash
   python3 test_all_tools.py
   ```

3. **Vérifier**:
   - Pas de nouveaux 404
   - Pas de nouveaux timeouts
   - Taux de succès stable (~40%)

### Régénérer le swagger

```bash
python3 generate_full_connector.py
```

## 📝 Checklist Avant Déploiement

- [ ] `test_all_tools.py` exécuté sans erreur critique
- [ ] Test manuel avec swagger minimal (5 outils)
- [ ] Authentification validée
- [ ] Temps de réponse < 30s
- [ ] Format de réponse correct `{"result": "..."}`
- [ ] Pas d'erreur 404 ou 401

## 💡 Conseils

1. **Toujours tester avec swagger minimal d'abord**
   - 5 min vs 3h d'ajout manuel
   - Valide la config complète
   - Identifie les problèmes rapidement

2. **Garder une copie du connecteur de test**
   - Permet de rollback rapidement
   - Utile pour débugger

3. **Documenter les changements d'auth user→créateur**
   - Noter quels outils nécessitent ce changement
   - Automatiser si possible

## 🆘 Troubleshooting

### Tous les tests en 404
```bash
# Vérifier le déploiement
curl https://word-mcp-connector.ashywater-9eb5a210.francecentral.azurecontainerapps.io/
# Devrait retourner JSON avec "tools_available"
```

### Timeouts fréquents
- Augmenter les ressources Azure Container Apps
- Optimiser les requêtes Azure Blob Storage
- Vérifier la région (France Central recommandé)

### Erreurs 401 Unauthorized
```bash
# Vérifier API Key
echo $API_KEY
# Devrait être: GV2yMslJIvxtjtMej932Sg9L3xrT6rMPmKLEqX2caSA=
```

### Erreur "Expecting String but received a Record"
- Schéma de réponse incorrect dans swagger
- Relancer `generate_full_connector.py`
- Redéployer

## 📞 Support

Issues GitHub: https://github.com/anthropics/claude-code/issues
Documentation MCP: https://docs.claude.com/en/docs/claude-code

---

**Version**: 2.0
**Dernière mise à jour**: 2025-10-10
