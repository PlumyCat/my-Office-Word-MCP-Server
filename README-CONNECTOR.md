# Word MCP Server - Copilot Studio Connector

## 🎯 Solution pour Copilot Studio

Ce repository contient **DEUX déploiements distincts**:

### 1. 🔧 Word MCP Server (Original)
**Pour:** Claude Desktop, Claude Code, ChatGPT, applications personnalisées

**Protocole:** MCP natif (Model Context Protocol)

**Endpoint:** `/mcp`

**Déploiement:**
```bash
./deploy-azure-with-storage.sh <ACR> <RG> <ENV>
```

---

### 2. 🔌 Word MCP Connector (Nouveau)
**Pour:** Copilot Studio via Custom Connector Power Apps

**Protocole:** REST API (Swagger 2.0)

**Endpoint:** `/api/*`

**Déploiement:**
```bash
./deploy-connector.sh <ACR> <RG> <ENV> <API_KEY>
```

## 🚀 Quick Start - Copilot Studio

### Étape 1: Déployer le Connector

```bash
# Exemple avec vos valeurs
./deploy-connector.sh myacr rg-word-docs env-word-mcp my-api-key-123
```

### Étape 2: Mettre à jour le Swagger

Le script affichera l'URL du connector. Modifier `word-connector.swagger.json`:

```json
{
  "host": "word-mcp-connector.XXXXX.francecentral.azurecontainerapps.io",
  ...
}
```

### Étape 3: Importer dans Power Apps

1. [make.powerapps.com](https://make.powerapps.com)
2. **Custom Connectors** > **Import an OpenAPI file**
3. Charger `word-connector.swagger.json`
4. Configurer auth: API Key, parameter `code`, location Query
5. Tester les endpoints

### Étape 4: Utiliser dans Copilot Studio

1. Créer/éditer un agent
2. **Actions** > **Add action** > Votre connector
3. **Important:** Cocher ✅ **"Cette valeur est générée par l'IA"** pour chaque paramètre
4. Tester dans le simulateur

## 📋 Fichiers Principaux

| Fichier | Description |
|---------|-------------|
| `word-connector.swagger.json` | Spécification OpenAPI 2.0 pour Power Apps |
| `connector_wrapper.py` | Wrapper FastAPI qui convertit REST → MCP |
| `Dockerfile.connector` | Image Docker du connector |
| `deploy-connector.sh` | Script de déploiement Azure |
| `COPILOT_STUDIO_INTEGRATION.md` | Documentation complète |

## 🔑 Endpoints Principaux

- `GET /api/templates/list` - Liste les templates
- `POST /api/template/create` - Crée un document depuis template
- `POST /api/document/text/replace` - Remplace du texte
- `POST /api/document/paragraph/add` - Ajoute un paragraphe
- `POST /api/document/table/add` - Ajoute un tableau
- `POST /api/document/text/get` - Extrait le texte
- `POST /api/document/create` - Crée un document vierge

Voir `COPILOT_STUDIO_INTEGRATION.md` pour tous les endpoints.

## 🎭 Exemple d'Usage

**Conversation utilisateur:**
```
User: Je veux créer une proposition pour Marie Martin,
      email m.martin@example.com, tel 01 23 45 67 89.
      Proposition: Microsoft 365 E3 à 35€/user/month

Copilot: ✅ Document créé: proposal_marie_martin.docx
         📄 https://...
```

**Ce qui se passe:**
- Copilot appelle automatiquement `CreateDocumentFromTemplate`
- Extrait les valeurs: nom, email, tel, contenu
- Pas de saisie manuelle demandée à l'utilisateur

## 🔐 Sécurité

**Auth:** API Key en query parameter `code`

**Génération d'une clé:**
```bash
openssl rand -base64 32
```

**Configuration:**
- Container App: Variable `API_KEY`
- Power Apps: Connexion avec la clé

## 🐛 Debug

**Logs du connector:**
```bash
az containerapp logs show \
  --name word-mcp-connector \
  --resource-group <RG> \
  --follow
```

**Erreur 401:**
- Vérifier l'API key dans Power Apps
- Vérifier `API_KEY` dans le Container App

**Paramètres demandés manuellement:**
- ✅ Cocher "généré par l'IA" dans Copilot Studio

## 📚 Documentation Complète

- **[COPILOT_STUDIO_INTEGRATION.md](./COPILOT_STUDIO_INTEGRATION.md)** - Guide complet
- **[word-connector.swagger.json](./word-connector.swagger.json)** - Spec OpenAPI
- **[connector_wrapper.py](./connector_wrapper.py)** - Code source

## 🏗️ Architecture

```
Copilot Studio
     │
     │ (Custom Connector)
     ▼
word-mcp-connector.*.azurecontainerapps.io
     │ (REST API)
     │
     │ (Appels MCP internes)
     ▼
word_document_server (Python package)
     │
     │ (Azure SDK)
     ▼
Azure Blob Storage (documents + templates)
```

## ✅ Avantages

✅ **Multi-paramètres** - Pas de limite à 1-2 paramètres
✅ **Orchestration IA** - Valeurs inférées du contexte
✅ **Compatible tout** - MCP natif + REST API
✅ **Sécurisé** - API Key auth
✅ **Scalable** - Auto-scaling Azure

---

**Créé pour résoudre les limitations de connexion MCP directe dans Copilot Studio.**
