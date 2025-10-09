# Configuration Copilot Studio - Word MCP Server

## 🔗 URL de votre serveur MCP

```
https://word-mcp-server.ashywater-9eb5a210.francecentral.azurecontainerapps.io/mcp
```

## 📋 Configuration pas à pas dans Copilot Studio

### Étape 1: Accéder à Copilot Studio
1. Allez sur https://copilotstudio.microsoft.com
2. Sélectionnez votre environnement
3. Créez ou ouvrez votre agent/copilot

### Étape 2: Ajouter le serveur MCP
1. Dans votre agent, allez dans **Settings** (Paramètres)
2. Cliquez sur **Advanced** > **Tools** (Outils)
3. Cliquez sur **Add Tool** > **Model Context Protocol (MCP)**

### Étape 3: Configuration du serveur
Remplissez les champs suivants:

- **Name**: `Word MCP Server`
- **Description**: `Create and manipulate Word documents`
- **Server URL**:
  ```
  https://word-mcp-server.ashywater-9eb5a210.francecentral.azurecontainerapps.io/mcp
  ```
- **Transport**: `HTTP`
- **Authentication**: `None` (pour commencer)

### Étape 4: Test de connexion
1. Cliquez sur **Test Connection**
2. Vous devriez voir ~31 outils disponibles
3. Cliquez sur **Save**

## 🔐 Configuration avec sécurité (Optionnel mais recommandé)

Si vous voulez ajouter une clé API pour la sécurité:

### 1. Redéployer avec une clé API
```bash
./deploy-azure-with-storage.sh mywordmcpacr my-word-mcp-rg my-word-mcp-env "votre-cle-secrete-123"
```

### 2. Configuration dans Copilot Studio
- **Authentication**: `API Key`
- **Header Name**: `X-API-Key`
- **API Key Value**: `votre-cle-secrete-123`

## 🛠️ Outils disponibles (31 outils)

### Gestion des documents
- `create_document` - Créer un nouveau document Word
- `list_available_documents` - Lister les documents stockés
- `download_document` - Obtenir l'URL de téléchargement
- `check_document_exists` - Vérifier l'existence d'un document

### Contenu
- `add_paragraph` - Ajouter du texte
- `add_heading` - Ajouter un titre
- `add_page_break` - Ajouter un saut de page
- `add_table` - Créer un tableau
- `add_image_from_url` - Insérer une image

### Formatage
- `format_paragraph` - Formater un paragraphe
- `format_text_in_paragraph` - Formater du texte spécifique
- `apply_style_to_paragraph` - Appliquer un style

### Templates
- `create_document_from_template` - Créer à partir d'un template
- `list_templates` - Lister les templates disponibles

### Azure Storage
- `cleanup_expired_documents` - Nettoyer les fichiers expirés
- `debug_storage` - Diagnostiquer le stockage

## 🧪 Test dans Copilot Studio

### Test 1: Créer un document simple
```
Create a Word document named "test.docx" with a heading "Hello World" and a paragraph "This is a test."
```

### Test 2: Document avec tableau
```
Create a document named "report.docx" with:
- A heading "Sales Report"
- A table with 3 rows and 2 columns containing product names and prices
```

### Test 3: Utiliser un template
```
List available templates, then create a document from the business_letter template
```

## 🔍 Dépannage

### Le serveur ne répond pas
```bash
# Vérifier le statut
az containerapp show --name word-mcp-server --resource-group my-word-mcp-rg

# Voir les logs
az containerapp logs show --name word-mcp-server --resource-group my-word-mcp-rg --tail 50
```

### Tester l'endpoint directement
```bash
curl -X GET "https://word-mcp-server.ashywater-9eb5a210.francecentral.azurecontainerapps.io/mcp" \
  -H "Accept: text/event-stream"
```

### Trop d'outils dans Copilot Studio?
Le serveur utilise déjà la version "light" avec seulement 31 outils (bien en dessous de la limite de 70).

Si vous avez besoin de réduire encore:
1. Modifiez `word_mcp_server_light.py` pour désactiver certains modules
2. Redéployez avec `./update-azure-app.sh mywordmcpacr my-word-mcp-rg`

## 📊 Monitoring

### Voir les logs en temps réel
```bash
az containerapp logs tail --name word-mcp-server --resource-group my-word-mcp-rg --follow
```

### Redémarrer le serveur
```bash
az containerapp restart --name word-mcp-server --resource-group my-word-mcp-rg
```

## 🔄 Mise à jour du serveur

Après modification du code:
```bash
./update-azure-app.sh mywordmcpacr my-word-mcp-rg
```

## 💾 Stockage des documents

- **Type**: Azure Blob Storage
- **Compte**: `mywordmcpacrstorage`
- **Container**: `word-documents`
- **TTL**: 24 heures (configurable)
- **Accès**: Public en lecture

Les URLs de téléchargement sont générées automatiquement et restent valides pendant la durée de vie du document.
