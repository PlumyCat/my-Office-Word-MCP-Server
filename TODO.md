# TODO - Office Word MCP Server

## 📋 Vue d'ensemble du projet

Implémentation d'un serveur MCP pour la manipulation de documents Word avec stockage Azure Blob Storage et système de templates.

## ✅ Fonctionnalités complétées

- [x] Serveur MCP de base avec FastMCP
- [x] Outils de manipulation Word (création, édition, formatage)
- [x] Intégration Azure Blob Storage pour persistance
- [x] Support multi-transport (stdio, HTTP, SSE)
- [x] Scripts de déploiement Azure Container Apps
- [x] Gestion TTL des documents
- [x] URLs publiques temporaires pour accès aux documents

## 🚀 Prochaines étapes prioritaires

### 1. 📄 Système de Templates

#### Architecture
- [ ] Créer un container blob dédié pour les templates (`word-templates`)
- [ ] Structure de stockage : `/templates/{category}/{template_name}.docx`
- [ ] Métadonnées des templates en tags blob (description, auteur, date)

#### Nouveaux Tools MCP

##### Tool 1: `list_templates`
- [ ] Lister tous les templates disponibles
- [ ] Filtrage par catégorie
- [ ] Retour : nom, description, catégorie, URL preview
```python
async def list_templates(category: Optional[str] = None) -> str:
    # Implémenter la liste depuis Azure Blob Storage
    pass
```

##### Tool 2: `add_template`
- [ ] Upload d'un document existant comme template
- [ ] Définition de la catégorie et métadonnées
- [ ] Validation du format .docx
```python
async def add_template(
    source_document: str,
    template_name: str,
    category: str,
    description: str
) -> str:
    # Implémenter l'ajout de template
    pass
```

##### Tool 3: `create_from_template`
- [ ] Créer un nouveau document depuis un template
- [ ] Copie du template vers le stockage documents
- [ ] Préservation du formatage et styles
```python
async def create_from_template(
    template_name: str,
    new_document_name: str,
    variables: Optional[Dict[str, str]] = None
) -> str:
    # Implémenter la création depuis template
    pass
```

#### Fichiers à modifier
- [ ] `word_document_server/tools/template_tools.py` (nouveau)
- [ ] `word_document_server/utils/template_storage.py` (nouveau)
- [ ] `word_document_server/main.py` (enregistrer les nouveaux tools)

### 2. 🐳 Déploiement Docker

#### Configuration Docker
- [ ] Mettre à jour `Dockerfile` pour la production
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 8000
  CMD ["python", "word_mcp_server.py"]
  ```

- [ ] Créer `docker-compose.yml` pour tests locaux
  ```yaml
  version: '3.8'
  services:
    word-mcp-server:
      build: .
      ports:
        - "8000:8000"
      environment:
        - MCP_TRANSPORT=http
        - MCP_HOST=0.0.0.0
        - MCP_PORT=8000
        - AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING}
  ```

- [ ] Script de build et push : `build-docker.sh`
- [ ] Test local avec Docker avant push Azure

### 3. 🧪 Tests avec MCP Inspector et Playwright

#### MCP Inspector
- [ ] Mettre à jour `run-mcp-inspector.sh` pour tester les nouveaux tools
- [ ] Scénarios de test :
  - [ ] Lister les templates disponibles
  - [ ] Ajouter un nouveau template
  - [ ] Créer un document depuis un template
  - [ ] Vérifier la persistance dans Azure Blob

#### Tests Playwright automatisés
- [ ] Créer `test_templates.py` avec tests E2E
  ```python
  async def test_template_workflow():
      # 1. Navigate vers MCP Inspector
      # 2. Connect au serveur
      # 3. Test list_templates
      # 4. Test add_template
      # 5. Test create_from_template
      # 6. Vérifier le document créé
  ```

- [ ] Script de lancement : `test-templates-e2e.sh`
- [ ] CI/CD avec GitHub Actions

### 4. 📦 Intégration complète

#### Tests d'intégration
- [ ] Test complet avec Azure Blob Storage
- [ ] Test de performance avec templates volumineux
- [ ] Test de concurrence (multiple users)
- [ ] Test de résilience (perte connexion, retry)

#### Documentation
- [ ] README mise à jour avec exemples templates
- [ ] Guide d'utilisation des templates
- [ ] API documentation pour les nouveaux tools
- [ ] Exemples de templates par défaut

## 🎯 Milestones

### Milestone 1 - Templates Core (Sprint 1)
- [ ] Architecture templates définie
- [ ] Storage layer implémenté
- [ ] 3 tools créés et fonctionnels
- **Deadline estimée : 3 jours**

### Milestone 2 - Docker & Deployment (Sprint 2)
- [ ] Dockerfile optimisé
- [ ] Docker compose pour dev local
- [ ] Déploiement Azure Container Apps
- **Deadline estimée : 2 jours**

### Milestone 3 - Testing & QA (Sprint 3)
- [ ] Tests MCP Inspector complets
- [ ] Tests Playwright E2E
- [ ] Documentation complète
- **Deadline estimée : 2 jours**

## 🐛 Bugs connus

- [ ] Gestion des erreurs lors de timeout Azure
- [ ] Validation des formats de fichiers
- [ ] Cleanup des documents expirés (amélioration nécessaire)

## 💡 Idées futures

- [ ] Support de variables dans les templates ({{name}}, {{date}})
- [ ] Versioning des templates
- [ ] Templates partagés vs privés
- [ ] Preview des templates (générer image/PDF)
- [ ] Import/Export en masse de templates
- [ ] Intégration avec Microsoft Graph API
- [ ] Cache local pour performance
- [ ] Support multi-langues pour templates

## 📝 Notes de développement

### Priorités
1. **URGENT** : Implémenter les 3 tools de templates
2. **IMPORTANT** : Dockerisation pour déploiement facile
3. **NICE TO HAVE** : Tests automatisés complets

### Dépendances à surveiller
- FastMCP version : vérifier compatibilité
- python-docx : limitations avec templates complexes
- Azure SDK : mise à jour régulière nécessaire

### Points de vigilance
- Sécurité : validation stricte des uploads de templates
- Performance : cache pour templates fréquemment utilisés
- Coûts Azure : optimiser les requêtes blob storage

## 🔗 Ressources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Azure Blob Storage SDK](https://docs.microsoft.com/azure/storage/blobs/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [Playwright Python](https://playwright.dev/python/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 📊 Progression globale

![Progress](https://progress-bar.dev/40/?title=Completion)

**Statut actuel : 40% - Core fonctionnel, templates en développement**
