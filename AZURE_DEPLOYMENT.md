# Azure Container Apps Deployment Guide

Ce guide décrit comment déployer l'Office Word MCP Server sur Azure Container Apps pour l'utiliser avec Copilot Studio.

## Vue d'ensemble

Le serveur a été transformé pour supporter le transport HTTP streamable, permettant son déploiement sur Azure Container Apps et son utilisation directe via URL dans Copilot Studio.

## Prérequis

- Azure CLI installé et connecté (`az login`)
- Azure Container Registry (ACR) créé
- Azure Container Apps Environment créé
- Permissions appropriées sur la ressource groupe

## Déploiement rapide

### Option 1: Déploiement sans authentification

```bash
# Rendre le script exécutable
chmod +x deploy-azure.sh

# Déployer
./deploy-azure.sh <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME>
```

### Option 2: Déploiement sécurisé avec API Key

```bash
# Rendre le script exécutable
chmod +x deploy-azure-secure.sh

# Déployer avec sécurité
./deploy-azure-secure.sh <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> [API_KEY]
```

## Déploiement manuel

### 1. Build et push de l'image

```bash
az acr build \
    --registry <ACR_NAME> \
    --image word-mcp-server:latest \
    --file Dockerfile \
    .
```

### 2. Déploiement Container App

```bash
az containerapp create \
    --name word-mcp-server \
    --resource-group <RESOURCE_GROUP> \
    --environment <ENVIRONMENT_NAME> \
    --image <ACR_NAME>.azurecr.io/word-mcp-server:latest \
    --ingress external \
    --target-port 8000 \
    --min-replicas 0 \
    --max-replicas 1 \
    --cpu 0.5 \
    --memory 1.0Gi \
    --env-vars \
        MCP_TRANSPORT=http \
        MCP_HOST=0.0.0.0 \
        MCP_PORT=8000 \
        MCP_PATH=/mcp \
        FASTMCP_LOG_LEVEL=INFO
```

## Configuration Copilot Studio

1. Accéder à votre agent Copilot Studio
2. Aller dans **Tools** → **Add** → **Model Context Protocol**
3. Configurer :
   - **Server URL**: `https://<FQDN>/mcp`
   - **Auth**: None (ou Bearer Token si sécurisé)

## Variables d'environnement

### Variables principales

| Variable | Valeur | Description |
|----------|--------|-------------|
| `MCP_TRANSPORT` | `http` | Active le mode HTTP streamable |
| `MCP_HOST` | `0.0.0.0` | Host d'écoute |
| `MCP_PORT` | `8000` | Port d'écoute |
| `MCP_PATH` | `/mcp` | Chemin de l'endpoint MCP |
| `FASTMCP_LOG_LEVEL` | `INFO` | Niveau de logging |

### Variables optionnelles

| Variable | Description |
|----------|-------------|
| `MCP_API_KEY` | Clé API pour l'authentification Bearer |

## Scaling et coûts

- **Min replicas**: 0 (scale-to-zero pour économiser les coûts)
- **Max replicas**: 1 (suffisant pour la plupart des cas d'usage)
- **CPU**: 0.5 vCPU
- **Memory**: 1.0 GiB

Le scale-to-zero signifie que l'application ne coûte rien quand elle n'est pas utilisée.

## Tests

### Test de base
```bash
curl -i https://<FQDN>/mcp
```

### Test avec authentification
```bash
curl -i -H "Authorization: Bearer <API_KEY>" https://<FQDN>/mcp
```

### Test de santé
```bash
curl -i https://<FQDN>/mcp/health
```

## Troubleshooting

### Erreurs communes

1. **Container ne démarre pas**
   - Vérifier les logs : `az containerapp logs show --name word-mcp-server --resource-group <RG>`
   - Vérifier les variables d'environnement

2. **Erreur 404 sur /mcp**
   - S'assurer que `MCP_TRANSPORT=http`
   - Vérifier que le chemin est bien `/mcp`

3. **Timeout de connexion**
   - Vérifier que l'ingress est configuré en `external`
   - Vérifier le target-port (8000)

### Logs et monitoring

```bash
# Voir les logs
az containerapp logs show \
    --name word-mcp-server \
    --resource-group <RESOURCE_GROUP> \
    --follow

# Voir les métriques
az containerapp show \
    --name word-mcp-server \
    --resource-group <RESOURCE_GROUP> \
    --query "properties.template.containers[0]"
```

## Sécurité

### Authentification

Le serveur supporte l'authentification Bearer Token via la variable `MCP_API_KEY`. Quand configurée, toutes les requêtes doivent inclure l'header :

```
Authorization: Bearer <your-api-key>
```

### Bonnes pratiques

1. Utiliser des API Keys longues et aléatoires
2. Stocker les secrets dans Azure Key Vault pour la production
3. Activer les logs Azure Monitor pour l'audit
4. Configurer des alertes sur les erreurs d'authentification

## Structure du projet transformé

```
Office-Word-MCP-Server/
├── word_document_server/          # Code du serveur MCP inchangé
│   ├── main.py                   # Support HTTP ajouté
│   ├── tools/                    # Outils MCP existants
│   ├── core/                     # Logique métier
│   └── utils/                    # Utilitaires
├── Dockerfile                    # Optimisé pour Azure Container Apps
├── deploy-azure.sh              # Script de déploiement simple
├── deploy-azure-secure.sh       # Script de déploiement sécurisé
├── .dockerignore                # Optimisation build Docker
├── .env.example                 # Variables d'environnement
└── AZURE_DEPLOYMENT.md          # Ce guide
```

Le serveur conserve toutes ses fonctionnalités Word existantes, seul le transport a été étendu pour supporter HTTP en plus de stdio.