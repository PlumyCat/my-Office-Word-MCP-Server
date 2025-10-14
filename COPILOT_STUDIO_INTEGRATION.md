# Intégration Copilot Studio - Word MCP Server

## 🎯 Problème Résolu

**Problème initial:** Copilot Studio ne supporte PAS le protocole MCP nativement. La couche bot intercepte les appels et force l'utilisateur à saisir manuellement les paramètres, ce qui empêche l'orchestration IA.

**Solution:** Créer un **Custom Connector Power Apps** avec Swagger 2.0 qui expose les tools MCP comme endpoints REST standard.

## 📋 Architecture

```
┌─────────────────────────────────────────┐
│  Word MCP Server (existant)             │
│  https://word-mcp-server.*.azurecontai  │
│  nerapps.io/mcp                         │
│                                          │
│  ✅ Claude Desktop/Code                  │
│  ✅ ChatGPT                              │
│  ✅ Better-Chatbot                       │
└──────────────┬──────────────────────────┘
               │ (Tools MCP partagés)
               │
┌──────────────▼──────────────────────────┐
│  Word MCP Connector Wrapper (nouveau)   │
│  https://word-mcp-connector.*.azureco   │
│  ntainerapps.io/api                     │
│                                          │
│  REST API ─► Appels MCP internes        │
│  Swagger 2.0 + x-ms-summary             │
│  API Key auth (query param)             │
└──────────────┬──────────────────────────┘
               │
               └─► ✅ Copilot Studio
                   (Custom Connector)
```

## 🚀 Déploiement

### 1. Déployer le Connector Wrapper

```bash
# Avec API key (recommandé)
./deploy-connector.sh <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> <API_KEY>

# Exemple
./deploy-connector.sh myacr rg-word-docs env-word-mcp my-secret-api-key-123
```

Le script va:
- ✅ Récupérer la config Azure Storage du serveur MCP existant
- ✅ Builder l'image Docker du wrapper
- ✅ Créer/mettre à jour le Container App
- ✅ Configurer la managed identity
- ✅ Afficher l'URL du connector

### 2. Mettre à jour le Swagger

Après le déploiement, mettre à jour le fichier `word-connector.swagger.json`:

```json
{
  "host": "word-mcp-connector.ashywater-XXXX.francecentral.azurecontainerapps.io",
  ...
}
```

Remplacer par l'URL affichée par le script (sans `https://`).

### 3. Créer le Custom Connector dans Power Apps

1. Aller sur [make.powerapps.com](https://make.powerapps.com)
2. **Custom Connectors** > **New custom connector** > **Import an OpenAPI file**
3. Charger `word-connector.swagger.json`
4. Dans **Security**:
   - Type: **API Key**
   - Parameter label: `API Key`
   - Parameter name: `code`
   - Parameter location: **Query**
5. **Create connector**
6. **Test** > Configurer la connexion avec votre API key
7. Tester un endpoint (ex: ListAllTemplates)

### 4. Utiliser dans Copilot Studio

1. Ouvrir Copilot Studio
2. Créer/éditer un agent
3. **Actions** > **Add an action**
4. Sélectionner votre Custom Connector
5. Choisir l'action (ex: `CreateDocumentFromTemplate`)

**Avantage clé:** Dans la configuration de l'action, vous pouvez cocher **"Cette valeur est générée par l'IA"** pour chaque paramètre. Copilot va alors inférer les valeurs du contexte de conversation au lieu de demander à l'utilisateur!

## 📝 Endpoints Disponibles

### Gestion des Templates

#### `GET /api/templates/list`
Liste tous les templates disponibles.

**Paramètres:** Aucun (sauf `code` pour l'auth)

**Réponse:**
```json
{
  "result": "Templates disponibles:\n- template-text\n- template-placeholders\n..."
}
```

---

#### `POST /api/template/create`
Crée un document depuis un template avec remplacement de variables.

**Paramètres:**
```json
{
  "template_name": "template-text",
  "new_document_name": "proposal_john_doe",
  "commercialName": "John Doe",
  "commercialEmail": "j.doe@mail.com",
  "commercialTel": "01 02 03 04 05",
  "propalContent": "Microsoft 365 Business Basic: 5€/user/month"
}
```

**Réponse:**
```json
{
  "message": "Document created successfully...",
  "document_url": "https://..."
}
```

**💡 Dans Copilot Studio:**
- Marquer tous les paramètres comme "générés par l'IA"
- L'agent va extraire les infos de la conversation

### Manipulation de Documents

#### `POST /api/document/text/replace`
Remplace du texte dans un document (paragraphes, tableaux, en-têtes, pieds de page).

**Paramètres:**
```json
{
  "filename": "proposal_john_doe.docx",
  "find_text": "{{companyName}}",
  "replace_text": "Contoso Ltd"
}
```

---

#### `POST /api/document/paragraph/add`
Ajoute un paragraphe à un document.

**Paramètres:**
```json
{
  "filename": "report.docx",
  "text": "Ceci est un nouveau paragraphe.",
  "style": "Normal"  // Optionnel
}
```

---

#### `POST /api/document/heading/add`
Ajoute un titre à un document.

**Paramètres:**
```json
{
  "filename": "report.docx",
  "text": "Chapitre 1: Introduction",
  "level": 1  // 1-9, défaut: 1
}
```

---

#### `POST /api/document/table/add`
Ajoute un tableau à un document.

**Paramètres:**
```json
{
  "filename": "report.docx",
  "rows": 3,
  "cols": 4,
  "data": "[[\"Header 1\", \"Header 2\"], [\"Cell 1\", \"Cell 2\"]]"  // JSON optionnel
}
```

---

#### `POST /api/document/text/get`
Extrait tout le texte d'un document.

**Paramètres:**
```json
{
  "filename": "report.docx"
}
```

**Réponse:**
```json
{
  "text": "Contenu complet du document..."
}
```

---

#### `POST /api/document/info/get`
Récupère les métadonnées d'un document.

**Paramètres:**
```json
{
  "filename": "report.docx"
}
```

**Réponse:**
```json
{
  "info": "Title: Report\nAuthor: John Doe\nPages: 5\n..."
}
```

---

#### `POST /api/document/create`
Crée un nouveau document vierge.

**Paramètres:**
```json
{
  "filename": "new_report.docx",
  "title": "Rapport Annuel",  // Optionnel
  "author": "John Doe"         // Optionnel
}
```

## 🎭 Exemple d'Utilisation dans Copilot Studio

### Scénario: Générer une proposition commerciale

**Configuration de l'action:**

1. Action: `CreateDocumentFromTemplate`
2. Paramètres:
   - `template_name`: Valeur par défaut = `"template-text"`
   - `new_document_name`: ✅ **Généré par l'IA**
   - `commercialName`: ✅ **Généré par l'IA**
   - `commercialEmail`: ✅ **Généré par l'IA**
   - `commercialTel`: ✅ **Généré par l'IA**
   - `propalContent`: ✅ **Généré par l'IA**

**Conversation exemple:**

```
User: Je dois créer une proposition pour Jean Dupont,
      email j.dupont@example.com, tel 06 12 34 56 78.
      La proposition est pour Microsoft 365 Business Standard à 12€/user/month.

Copilot: [Appelle CreateDocumentFromTemplate automatiquement]
         ✅ Document créé: proposal_jean_dupont.docx
         📄 Lien: https://...

         La proposition a été générée avec les informations de Jean Dupont.
```

**Ce qui se passe en coulisses:**

Copilot extrait automatiquement:
- `new_document_name`: "proposal_jean_dupont"
- `commercialName`: "Jean Dupont"
- `commercialEmail`: "j.dupont@example.com"
- `commercialTel`: "06 12 34 56 78"
- `propalContent`: "Microsoft 365 Business Standard à 12€/user/month"

**🎉 Pas de demande manuelle à l'utilisateur!**

## 🔒 Sécurité

### API Key Authentication

L'API key est passée en query parameter `code`:

```
GET /api/templates/list?code=my-secret-api-key-123
```

### Recommandations

1. **Générer une API key forte:**
   ```bash
   openssl rand -base64 32
   ```

2. **Stocker de façon sécurisée:**
   - Variables d'environnement Azure Container App
   - Azure Key Vault (avancé)

3. **Rotation régulière:**
   - Changer l'API key tous les 90 jours
   - Mettre à jour dans Power Apps et Azure Container App

## 🔧 Maintenance

### Logs

```bash
# Logs du connector
az containerapp logs show \
  --name word-mcp-connector \
  --resource-group <RG> \
  --follow

# Logs du serveur MCP (backend)
az containerapp logs show \
  --name word-mcp-server \
  --resource-group <RG> \
  --follow
```

### Mise à jour

```bash
# Re-déployer avec les dernières modifications
./deploy-connector.sh <ACR> <RG> <ENV> <API_KEY>
```

### Scaling

Le connector est configuré pour:
- **Min replicas:** 0 (scale to zero si inactif)
- **Max replicas:** 3
- **CPU:** 0.5 core
- **RAM:** 1 GB

Ajuster si nécessaire dans `deploy-connector.sh`.

## 🐛 Troubleshooting

### Erreur 401 Unauthorized

- Vérifier que l'API key est correcte dans la connexion Power Apps
- Vérifier que `API_KEY` est configurée dans le Container App

### Erreur 500 Internal Server Error

- Vérifier les logs du connector
- Vérifier que `AZURE_STORAGE_CONNECTION_STRING` est correcte
- Vérifier que le serveur MCP backend est déployé et accessible

### Tools non visibles dans Copilot Studio

- Vérifier que le Custom Connector est créé et testé dans Power Apps
- Rafraîchir la liste des actions dans Copilot Studio
- Vérifier que la connexion est active

### Paramètres toujours demandés à l'utilisateur

- ✅ Cocher **"Cette valeur est générée par l'IA"** pour chaque paramètre
- Fournir des exemples dans la description de l'action
- Tester dans le simulateur Copilot Studio

## 📚 Références

- [Power Apps Custom Connectors](https://learn.microsoft.com/en-us/connectors/custom-connectors/)
- [Copilot Studio Actions](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-plugin-actions)
- [OpenAPI 2.0 Specification](https://swagger.io/specification/v2/)
- [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)

## 🎉 Avantages de cette Approche

✅ **Multi-paramètres supportés** - Pas de limitation à 1 paramètre
✅ **Orchestration IA** - L'agent infère les valeurs du contexte
✅ **Compatible Claude/ChatGPT** - Le serveur MCP original reste utilisable
✅ **Sécurisé** - API Key authentication
✅ **Scalable** - Auto-scaling Azure Container Apps
✅ **Maintenable** - Code séparé, déploiement indépendant

---

**Note:** Cette approche contourne les limitations de Copilot Studio en utilisant des Custom Connectors Power Apps au lieu d'une connexion MCP directe.
