# Word Document Proposal Generator

REST API pour la génération automatique de propositions commerciales Microsoft 365 depuis des templates Word avec remplacement de variables et gestion de tableaux.

Conçu pour l'intégration avec **Microsoft Copilot Studio**.

## 🎯 Cas d'Usage

Créer des propositions commerciales professionnelles pour Microsoft 365:
- ✅ Générer des documents depuis des templates personnalisés
- ✅ Remplacer automatiquement les variables (nom client, email, téléphone, contenu)
- ✅ Ajouter des lignes de produits/services dans les tableaux existants
- ✅ Formater automatiquement les tableaux (bordures, en-têtes colorés, lignes alternées)
- ✅ Stocker les documents dans Azure Blob Storage
- ✅ Obtenir des URLs signées pour télécharger les documents

## 📋 Fonctionnalités

### Gestion de Documents
- `POST /api/create/document/from/template` - Créer un document depuis un template avec variables
- `GET /api/get/document/url` - Obtenir l'URL de téléchargement d'un document
- `GET /api/list/all/documents` - Lister tous les documents générés
- `POST /api/check/document/exists` - Vérifier si un document existe
- `POST /api/delete/document` - Supprimer un document

### Gestion de Templates
- `GET /api/list/all/templates` - Lister tous les templates disponibles
- `POST /api/add/document/template` - Ajouter un nouveau template
- `POST /api/delete/document/template` - Supprimer un template

### Gestion de Contenu
- `POST /api/add/paragraph` - Ajouter un paragraphe de texte
- `POST /api/add/heading` - Ajouter un titre de section
- `POST /api/add/table/with/rows` - Ajouter un nouveau tableau avec données
- `POST /api/add/table/row` - **Ajouter une ligne à un tableau existant**

### Formatage de Tableaux
- `POST /api/format/table/with/borders` - Formater un tableau avec bordures
- `POST /api/highlight/table/header/colors` - Colorer l'en-tête d'un tableau
- `POST /api/apply/alternating/row/colors` - Appliquer des couleurs alternées
- `POST /api/format/cell/text/appearance` - Formater une cellule spécifique

## 🚀 Déploiement Azure

### Prérequis

- Compte Azure avec souscription active
- Azure CLI installé et connecté (`az login`)
- Azure Container Registry (ACR)
- Azure Container Apps Environment
- Azure Storage Account avec conteneur `word-documents` et `word-templates`

### Variables d'Environnement Requises

```bash
# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=<votre-storage-account>
AZURE_STORAGE_CONNECTION_STRING=<connection-string>

# API Security (optionnel)
API_KEY=<votre-cle-api>

# Debug (optionnel)
DEBUG_MODE=false
```

### Déploiement Rapide

```bash
# 1. Cloner le repository
git clone https://github.com/votre-username/word-proposal-generator.git
cd word-proposal-generator

# 2. Configurer les variables (editez le script)
nano deploy-azure-with-storage.sh

# 3. Déployer
chmod +x deploy-azure-with-storage.sh
./deploy-azure-with-storage.sh <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME>
```

Le script va:
1. Construire l'image Docker et la pousser vers ACR
2. Créer/mettre à jour le Container App
3. Configurer l'authentification managed identity avec le Storage Account
4. Assigner les rôles nécessaires (Storage Blob Data Contributor)

### Déploiement Manuel

```bash
# Build et push de l'image
az acr build -t word-proposal-api:latest -r <ACR_NAME> -f Dockerfile.connector .

# Créer Container App
az containerapp create \
  --name word-proposal-api \
  --resource-group <RESOURCE_GROUP> \
  --environment <ENVIRONMENT_NAME> \
  --image <ACR_NAME>.azurecr.io/word-proposal-api:latest \
  --target-port 8080 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    AZURE_STORAGE_ACCOUNT_NAME=<storage-account> \
    API_KEY=<your-api-key>

# Activer managed identity
az containerapp identity assign \
  --name word-proposal-api \
  --resource-group <RESOURCE_GROUP> \
  --system-assigned

# Assigner le rôle Storage Blob Data Contributor
PRINCIPAL_ID=$(az containerapp show -n word-proposal-api -g <RESOURCE_GROUP> --query identity.principalId -o tsv)
STORAGE_ID=$(az storage account show -n <STORAGE_ACCOUNT> -g <RESOURCE_GROUP> --query id -o tsv)

az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID
```

## 📖 Utilisation avec Copilot Studio

### Configuration des Actions

1. **Importer le Swagger**: Utiliser `/openapi.json` depuis votre Container App URL
2. **Ajouter l'API Key**: Configurer l'header `X-API-Key` dans l'authentification
3. **Créer les Actions**: Voir le guide complet dans `profiles/GUIDE_ACTIONS_COPILOT.md`

### Workflow Typique

```
User: "Crée une proposition pour Jean Dupont, email j.dupont@mail.com"

Bot: [Appelle create/document/from/template]
  - template_name: "template-text"
  - new_document_name: "proposal_jean_dupont"
  - variables: {
      "commercialName": "Jean Dupont",
      "commercialEmail": "j.dupont@mail.com",
      ...
    }

Bot: [Appelle add/table/row pour chaque produit Microsoft 365]
  - filename: "proposal_jean_dupont"
  - table_index: 0
  - row_data: ["Microsoft 365 Business Premium", "Description...", "1", "21.00", "25.00"]

Bot: [Appelle highlight/table/header/colors]
  - filename: "proposal_jean_dupont"
  - table_index: 0
  - header_color: "4472C4"
  - text_color: "FFFFFF"

Bot: "Voici votre proposition: https://storage.blob.core.windows.net/..."
```

## 🛠️ Développement Local

### Installation

```bash
# Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env`:

```env
AZURE_STORAGE_ACCOUNT_NAME=<votre-storage-account>
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
API_KEY=<votre-cle-api>
DEBUG_MODE=true
PORT=8080
```

### Lancement Local

```bash
python connector_wrapper.py
```

L'API sera disponible sur `http://localhost:8080`

### Test des Endpoints

```bash
# Lister les templates
curl -H "X-API-Key: <your-key>" http://localhost:8080/api/list/all/templates

# Créer un document
curl -X POST http://localhost:8080/api/create/document/from/template \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-key>" \
  -d '{
    "template_name": "template-text",
    "new_document_name": "test_proposal",
    "variables": {
      "commercialName": "Test Client",
      "commercialEmail": "test@client.com",
      "commercialTel": "0123456789",
      "propalContent": "Test content"
    }
  }'
```

## 📁 Structure du Projet

```
.
├── connector_wrapper.py          # API REST FastAPI
├── Dockerfile.connector           # Dockerfile pour Container Apps
├── requirements.txt              # Dépendances Python
├── deploy-azure-with-storage.sh  # Script de déploiement Azure
├── word_document_server/
│   ├── tools/
│   │   ├── document_tools.py     # Gestion documents
│   │   ├── content_tools.py      # Ajout contenu (paragraphes, tableaux)
│   │   ├── format_tools.py       # Formatage tableaux
│   │   └── template_tools.py     # Gestion templates
│   └── utils/
│       ├── azure_storage.py      # Intégration Azure Blob Storage
│       ├── file_utils.py         # Utilitaires fichiers
│       └── template_storage.py   # Gestion templates Azure
└── profiles/
    ├── GUIDE_ACTIONS_COPILOT.md  # Guide configuration Copilot Studio
    └── create-propal.swagger.json # Swagger pour import

```

## 🔐 Sécurité

- **API Key**: Protection des endpoints via header `X-API-Key`
- **Managed Identity**: Authentification Azure sans clés de stockage
- **RBAC**: Contrôle d'accès granulaire avec rôles Azure
- **URLs signées**: Accès temporaire aux documents (24h par défaut)

## 🔧 Dépannage

### ContentFiltered Error (Copilot Studio)

Si vous rencontrez des erreurs "ContentFiltered" dans Copilot Studio:

1. Les réponses sont automatiquement raccourcies à `ok` ou `error: <type>`
2. Les URLs de documents sont préservées
3. Activer `DEBUG_MODE=true` pour voir les réponses complètes (développement uniquement)

### Document Not Found

- Vérifier que le managed identity a le rôle "Storage Blob Data Contributor"
- Vérifier le nom du conteneur dans Azure Storage (`word-documents`)
- Vérifier les logs du Container App: `az containerapp logs show -n <app-name> -g <rg>`

### Permission Denied

```bash
# Re-assigner le rôle
az role assignment create \
  --assignee <PRINCIPAL_ID> \
  --role "Storage Blob Data Contributor" \
  --scope <STORAGE_ID>
```

## 📝 License

MIT

## 🤝 Contribution

Les contributions sont les bienvenues! N'hésitez pas à ouvrir une issue ou une pull request.

## 📞 Support

Pour toute question ou problème:
- Ouvrir une issue sur GitHub
- Consulter le guide Copilot Studio dans `profiles/GUIDE_ACTIONS_COPILOT.md`
