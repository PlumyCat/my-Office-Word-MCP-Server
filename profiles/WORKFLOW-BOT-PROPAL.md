# 🤖 Bot Génération de Propositions Commerciales - Workflow Complet

## 📋 Vue d'ensemble

Ce bot est spécialisé dans la **génération automatique de propositions commerciales Microsoft 365** depuis un template Word.

**Vocation**: Bot autonome appelable depuis un bot maître
**Format de sortie**: Document Word (.docx) avec lien de téléchargement

## 🎯 Cas d'usage

### Utilisation Autonome
```
Utilisateur: "Je veux créer une proposition pour le client Contoso"
Bot: [Demande les infos] → [Génère le document] → [Retourne le lien]
```

### Utilisation depuis Bot Maître
```
Bot Maître: "Créer une proposition pour [client]"
Bot Propal: [Reçoit les données] → [Génère le document] → [Retourne le lien]
Bot Maître: [Utilise le lien pour envoyer au client]
```

## 📊 Workflow Complet - 10 Étapes

### Étape 1: Collecter les Informations Commerciales

**Variables à demander**:
- `commercialName` (string) - Nom du commercial (ex: "John Do")
- `commercialEmail` (string) - Email du commercial (ex: "j.do@mail.com")
- `commercialTel` (string) - Téléphone du commercial (ex: "01 02 03 04 05")
- `clientName` (string) - Nom du client (optionnel, pour le nom du fichier)

**Dans Copilot Studio**:
```yaml
Topic: Collecter Infos Commerciales
Questions:
  - "Quel est le nom du commercial ?"
    → Variable: Topic.commercialName

  - "Quel est l'email du commercial ?"
    → Variable: Topic.commercialEmail

  - "Quel est le téléphone du commercial ?"
    → Variable: Topic.commercialTel

  - "Quel est le nom du client ? (optionnel)"
    → Variable: Topic.clientName
```

### Étape 2: Générer le Contenu des Offres Microsoft 365

**Option A: Contenu Prédéfini**
```yaml
Action: Définir une variable
Variable: Topic.offresTable
Value: |
  | Offre | Utilisateurs | Prix/mois | Features | Support |
  |-------|--------------|-----------|----------|---------|
  | Microsoft 365 Business Basic | 1-300 | 5.60€ | Email, OneDrive, Teams, Office Web | Standard |
  | Microsoft 365 Business Standard | 1-300 | 11.70€ | Basic + Desktop Office Apps | Standard |
  | Microsoft 365 Business Premium | 1-300 | 20.60€ | Standard + Security avancée | Premium |
  | Microsoft 365 Apps for Business | 1-300 | 9.20€ | Office Desktop uniquement | Standard |
  | Microsoft 365 E3 | Illimité | 32.00€ | Entreprise complète | Premium |
  | Microsoft 365 E5 | Illimité | 52.00€ | E3 + Analytics & Security | Premium+ |
  | Office 365 E1 | Illimité | 7.20€ | Web & Mobile uniquement | Standard |
```

**Option B: Génération Dynamique avec Copilot**
```yaml
Action: Créer une invite générative
Invite: |
  Génère un tableau markdown avec les offres Microsoft 365 adaptées pour un client {Topic.clientName}.
  Format: | Offre | Utilisateurs | Prix/mois | Features | Support |
  Inclure 5-7 offres pertinentes.
Réponse → Variable: Topic.offresTable
```

### Étape 3: Créer le Nom du Document

```yaml
Action: Définir une variable
Variable: Topic.documentName
Value: Text.Format("propal_{0}_{1}.docx",
                    Text.Lower(Text.Replace(Topic.clientName, " ", "_")),
                    Text.Format("{0:yyyyMMddHHmmss}", Now()))

Exemple: "propal_contoso_20251010143022.docx"
```

### Étape 4: Parser le Tableau Markdown en Array

**Important**: Copilot Studio nécessite un array 2D pour le paramètre `data` de l'action `AddTable`.

**Option A: Utiliser Power Fx (si disponible)**
```yaml
Action: Définir une variable
Variable: Topic.tableData
Value: ParseMarkdownTable(Topic.offresTable)
```

**Option B: Array prédéfini (plus simple)**
```yaml
Action: Définir une variable
Variable: Topic.tableData
Value: [
  "Offre", "Utilisateurs", "Prix/mois", "Features", "Support",
  "Microsoft 365 Business Basic", "1-300", "5.60€", "Email, OneDrive, Teams, Office Web", "Standard",
  "Microsoft 365 Business Standard", "1-300", "11.70€", "Basic + Desktop Office Apps", "Standard",
  "Microsoft 365 Business Premium", "1-300", "20.60€", "Standard + Security avancée", "Premium",
  "Microsoft 365 Apps for Business", "1-300", "9.20€", "Office Desktop uniquement", "Standard",
  "Microsoft 365 E3", "Illimité", "32.00€", "Entreprise complète", "Premium",
  "Microsoft 365 E5", "Illimité", "52.00€", "E3 + Analytics & Security", "Premium+",
  "Office 365 E1", "Illimité", "7.20€", "Web & Mobile uniquement", "Standard",
  "Microsoft 365 F3", "Illimité", "7.10€", "Firstline workers", "Standard"
]
```

### Étape 5: Créer le Document depuis Template

**Action**: `CreateDocumentFromTemplate`

**Paramètres**:
```yaml
template_name: "template-text"
new_document_name: Topic.documentName
category: "general"
variables: {
  "commercialName": Topic.commercialName,
  "commercialEmail": Topic.commercialEmail,
  "commercialTel": Topic.commercialTel,
  "propalContent": "[TABLEAU_OFFRES]"
}
```

**Message utilisateur pendant l'attente**:
```
"📄 Création du document en cours..."
```

**Gestion d'erreur**:
```yaml
Si l'action échoue:
  Message: "❌ Erreur lors de la création du document. Veuillez réessayer."
  Fin du topic
```

### Étape 6: Supprimer le Placeholder du Tableau

**Action**: `ReplaceTextUniversal`

**Paramètres**:
```yaml
filename: Topic.documentName
find_text: "[TABLEAU_OFFRES]"
replace_text: ""
```

**Note**: On supprime le placeholder pour le remplacer par le vrai tableau Word.

### Étape 7: Ajouter le Titre du Tableau

**Action**: `AddParagraph`

**Paramètres**:
```yaml
filename: Topic.documentName
text: "Tableau des offres Microsoft 365:"
style: "Heading 2"
```

### Étape 8: Créer le Tableau Word

**Action**: `AddTable`

**Paramètres**:
```yaml
filename: Topic.documentName
rows: 9
cols: 5
data: Topic.tableData
```

**Note**:
- 9 rows = 1 header + 8 offres
- 5 cols = Offre, Utilisateurs, Prix/mois, Features, Support

### Étape 9: Formater le Tableau

**Actions multiples (séquentielles)**:

#### 9.1 Formater l'En-tête (Bleu/Blanc)
```yaml
Action: HighlightTableHeader
Paramètres:
  filename: Topic.documentName
  table_index: 0
  header_color: "4472C4"
  text_color: "FFFFFF"
```

#### 9.2 Appliquer l'Alternance de Lignes
```yaml
Action: ApplyTableAlternatingRows
Paramètres:
  filename: Topic.documentName
  table_index: 0
  color1: "FFFFFF"
  color2: "F2F2F2"
```

#### 9.3 Ajouter les Bordures
```yaml
Action: FormatTable
Paramètres:
  filename: Topic.documentName
  table_index: 0
  border_style: "single"
  has_header_row: true
```

**Message utilisateur**:
```
"🎨 Formatage du tableau en cours..."
```

### Étape 10: Ajouter le Paragraphe de Conclusion

**Action**: `AddParagraph`

**Paramètres**:
```yaml
filename: Topic.documentName
text: Text.Format("Pour toute question, contactez {0} ({1} - {2})",
                  Topic.commercialName,
                  Topic.commercialEmail,
                  Topic.commercialTel)
style: "Normal"
```

### Étape 11: Générer le Lien de Téléchargement

**Action**: `DownloadDocument`

**Paramètres**:
```yaml
filename: Topic.documentName
```

**Réponse → Variable**: `Topic.downloadUrl`

### Étape 12: Retourner le Résultat à l'Utilisateur

**Message final**:
```yaml
Message: Text.Format("✅ Votre proposition commerciale est prête !

📄 Document: {0}
👤 Commercial: {1}
📧 Email: {2}
📞 Tél: {3}

🔗 Télécharger: {4}

Le document contient un tableau formaté avec les offres Microsoft 365.",
  Topic.documentName,
  Topic.commercialName,
  Topic.commercialEmail,
  Topic.commercialTel,
  Topic.downloadUrl
)
```

**Carte adaptative (optionnel)**:
```json
{
  "type": "AdaptiveCard",
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "version": "1.3",
  "body": [
    {
      "type": "TextBlock",
      "text": "✅ Proposition Commerciale Générée",
      "weight": "Bolder",
      "size": "Large",
      "color": "Good"
    },
    {
      "type": "FactSet",
      "facts": [
        {
          "title": "Document:",
          "value": "${Topic.documentName}"
        },
        {
          "title": "Commercial:",
          "value": "${Topic.commercialName}"
        },
        {
          "title": "Email:",
          "value": "${Topic.commercialEmail}"
        },
        {
          "title": "Téléphone:",
          "value": "${Topic.commercialTel}"
        }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "📥 Télécharger",
      "url": "${Topic.downloadUrl}"
    }
  ]
}
```

## 🔗 Intégration avec Bot Maître

### Appel depuis un Bot Maître

**Topic dans Bot Maître**:
```yaml
Topic: Demander Proposition Commerciale

Condition: User dit "créer une proposition" OU "générer une propal"

Actions:
  1. Message: "Je vais créer une proposition commerciale pour vous."

  2. Rediriger vers bot enfant: "Bot Génération Propal"
     Paramètres à passer:
       - commercialName: Global.DefaultCommercialName (ou demander)
       - commercialEmail: Global.DefaultCommercialEmail
       - commercialTel: Global.DefaultCommercialTel
       - clientName: demander ou extraire du contexte

  3. Attendre réponse du bot enfant

  4. Récupérer: Topic.downloadUrl

  5. Message: Text.Format("Voici votre proposition: {0}", Topic.downloadUrl)

  6. [Optionnel] Envoyer par email au client
     Action: Office365Outlook.SendEmail
     Paramètres:
       To: Topic.clientEmail
       Subject: Text.Format("Proposition Microsoft 365 - {0}", Topic.clientName)
       Body: Text.Format("Bonjour,\n\nVeuillez trouver ci-joint notre proposition Microsoft 365.\n\nLien: {0}\n\nCordialement,\n{1}",
                         Topic.downloadUrl,
                         Topic.commercialName)
```

### Paramètres d'Entrée pour Bot Enfant

Si le bot propal est appelé depuis un bot maître, il doit accepter des paramètres d'entrée:

**Configuration dans Copilot Studio**:
```yaml
Variables d'entrée (Input Variables):
  - commercialName (string, optionnel)
  - commercialEmail (string, optionnel)
  - commercialTel (string, optionnel)
  - clientName (string, optionnel)
  - offresTable (string, optionnel) - si le maître génère déjà le tableau
```

**Logique de Fallback**:
```yaml
Si commercialName est vide:
  → Demander "Quel est le nom du commercial ?"
Sinon:
  → Utiliser la valeur fournie

Si commercialEmail est vide:
  → Demander "Quel est l'email du commercial ?"
Sinon:
  → Utiliser la valeur fournie

(Idem pour les autres paramètres)
```

### Variables de Sortie pour Bot Enfant

**Configuration dans Copilot Studio**:
```yaml
Variables de sortie (Output Variables):
  - downloadUrl (string) - Lien de téléchargement du document
  - documentName (string) - Nom du fichier généré
  - success (boolean) - Succès ou échec de la génération
  - errorMessage (string) - Message d'erreur si échec
```

**Retour au Bot Maître**:
```yaml
Fin du topic:
  Retourner:
    downloadUrl: Topic.downloadUrl
    documentName: Topic.documentName
    success: true
    errorMessage: ""
```

## ⚙️ Configuration dans Copilot Studio

### 1. Créer le Topic Principal

**Nom**: `Générer Proposition Commerciale`

**Déclencheurs**:
- "créer une proposition"
- "générer une propal"
- "nouvelle proposition Microsoft 365"
- "faire une proposition commerciale"
- "propal client"

### 2. Ajouter les Variables du Topic

```yaml
Variables locales:
  - commercialName (string)
  - commercialEmail (string)
  - commercialTel (string)
  - clientName (string)
  - documentName (string)
  - offresTable (string)
  - tableData (array)
  - downloadUrl (string)
```

### 3. Séquence des Nœuds

```
[1] Question - commercialName
  ↓
[2] Question - commercialEmail
  ↓
[3] Question - commercialTel
  ↓
[4] Question - clientName
  ↓
[5] Définir variable - documentName
  ↓
[6] Définir variable - tableData
  ↓
[7] Message - "📄 Création du document..."
  ↓
[8] Action - CreateDocumentFromTemplate
  ↓
[9] Condition - Vérifier succès de création
  ↓ (succès)
[10] Action - ReplaceTextUniversal
  ↓
[11] Action - AddParagraph (titre tableau)
  ↓
[12] Message - "📊 Ajout du tableau..."
  ↓
[13] Action - AddTable
  ↓
[14] Message - "🎨 Formatage..."
  ↓
[15] Action - HighlightTableHeader
  ↓
[16] Action - ApplyTableAlternatingRows
  ↓
[17] Action - FormatTable
  ↓
[18] Action - AddParagraph (conclusion)
  ↓
[19] Action - DownloadDocument
  ↓
[20] Message - Afficher résultat avec lien
  ↓
[21] Fin du topic
```

### 4. Gestion des Erreurs

**Après chaque action critique**:
```yaml
Condition: Si action.IsSuccessful = false
  Actions:
    - Message: Text.Format("❌ Erreur: {0}", action.ErrorMessage)
    - Log: Enregistrer l'erreur
    - Fin du topic avec erreur
```

**Actions critiques à surveiller**:
- CreateDocumentFromTemplate
- AddTable
- DownloadDocument

## 📊 Temps d'Exécution Estimés

| Étape | Action | Temps |
|-------|--------|-------|
| 1-4 | Collecte informations | Variable (dépend de l'utilisateur) |
| 5 | CreateDocumentFromTemplate | ~25s |
| 6 | ReplaceTextUniversal | ~0.1s |
| 7 | AddParagraph | ~0.1s |
| 8 | AddTable | ~0.4s |
| 9 | HighlightTableHeader | ~0.1s |
| 10 | ApplyTableAlternatingRows | ~0.1s |
| 11 | FormatTable | ~0.1s |
| 12 | AddParagraph (conclusion) | ~0.1s |
| 13 | DownloadDocument | ~0.1s |
| **Total (hors collecte)** | | **~27s** |

**Note**: Bien en dessous de la limite de 30s de Copilot Studio ✅

## 🧪 Tests et Validation

### Test Unitaire par Étape

**Dans Copilot Studio Test Panel**:
```
Étape 1: Tester la collecte d'infos
  Input: "créer une proposition"
  Vérifier: Les 4 questions sont posées

Étape 2: Tester la création du document
  Input: Fournir les infos commerciales
  Vérifier: Le document est créé

Étape 3: Tester le formatage du tableau
  Vérifier: Le tableau a bien les bonnes couleurs

Étape 4: Tester le lien de téléchargement
  Vérifier: Le lien est cliquable et télécharge le document
```

### Test End-to-End

**Scénario complet**:
```
User: "Je veux créer une proposition"
Bot: "Quel est le nom du commercial ?"
User: "Jean Dupont"
Bot: "Quel est l'email du commercial ?"
User: "jean.dupont@company.com"
Bot: "Quel est le téléphone du commercial ?"
User: "01 23 45 67 89"
Bot: "Quel est le nom du client ?"
User: "Contoso"
Bot: "📄 Création du document en cours..."
Bot: "📊 Ajout du tableau..."
Bot: "🎨 Formatage..."
Bot: "✅ Votre proposition est prête ! [Lien de téléchargement]"
```

**Validation**:
1. ✅ Document créé en moins de 30s
2. ✅ Tableau Word formaté (pas du texte markdown)
3. ✅ Variables commerciales remplacées
4. ✅ Lien de téléchargement fonctionnel
5. ✅ Document professionnel et présentable

### Test depuis Bot Maître

**Scénario**:
```
Bot Maître: [Appelle Bot Propal avec paramètres]
Bot Propal: [Génère le document]
Bot Propal: [Retourne downloadUrl]
Bot Maître: [Affiche le lien ou envoie par email]
```

## 📝 Template Word Requis

Le bot utilise le template `template-text.docx` qui doit contenir:

**Variables à remplacer**:
- `{{commercialName}}` - Nom du commercial
- `{{commercialEmail}}` - Email du commercial
- `{{commercialTel}}` - Téléphone du commercial
- `{{propalContent}}` ou `[TABLEAU_OFFRES]` - Sera remplacé par le tableau

**Structure minimale**:
```
Proposition Commerciale Microsoft 365
=====================================

Commercial: {{commercialName}}
Email: {{commercialEmail}}
Téléphone: {{commercialTel}}

[TABLEAU_OFFRES]

Cordialement,
{{commercialName}}
```

## 🚀 Déploiement

### Prérequis
- [x] Profile `create-propal` déployé
- [x] Custom Connector configuré dans Power Apps
- [x] API Key configurée
- [x] Template `template-text.docx` uploadé sur Azure Storage

### Checklist de Déploiement
- [ ] Topic créé dans Copilot Studio
- [ ] 13 actions ajoutées et configurées
- [ ] Variables d'entrée/sortie définies (si bot enfant)
- [ ] Tests unitaires passés
- [ ] Test end-to-end validé
- [ ] Gestion d'erreurs configurée
- [ ] Messages utilisateur personnalisés
- [ ] Documentation partagée avec l'équipe

## 📞 Support

### Problèmes Courants

**1. Timeout > 30s**
```
Cause: Le CreateDocumentFromTemplate prend trop de temps
Solution: Vérifier que le cold start est passé (attendre 1-2 min après déploiement)
```

**2. Tableau pas formaté**
```
Cause: Les actions de formatage ne sont pas exécutées dans l'ordre
Solution: Vérifier la séquence des nœuds (HighlightTableHeader → ApplyTableAlternatingRows → FormatTable)
```

**3. Variables non remplacées**
```
Cause: Le template ne contient pas les bons placeholders
Solution: Vérifier que le template contient {{commercialName}}, {{commercialEmail}}, etc.
```

**4. Lien de téléchargement ne fonctionne pas**
```
Cause: Le document n'existe pas dans Azure Storage
Solution: Vérifier que CreateDocumentFromTemplate a réussi (pas d'erreur)
```

### Logs et Debugging

**Vérifier les logs du connector**:
```bash
az containerapp logs show \
  --name word-mcp-proposal \
  --resource-group my-word-mcp-rg \
  --tail 50
```

**Tester directement l'API**:
```bash
# Test création document
curl -X POST \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "template-text",
    "new_document_name": "test.docx",
    "category": "general",
    "variables": {
      "commercialName": "Test",
      "commercialEmail": "test@test.com",
      "commercialTel": "0123456789",
      "propalContent": "[TABLEAU_OFFRES]"
    }
  }' \
  https://word-mcp-proposal.ashywater-9eb5a210.francecentral.azurecontainerapps.io/api/create/document/from/template
```

## 📚 Ressources

### Fichiers Importants
- `profiles/swagger-create-propal.json` - Swagger à importer
- `profiles/DEPLOYMENT-SUCCESS.md` - Guide de déploiement
- `profiles/README-PROFILES.md` - Documentation du système de profiles
- `test_workflow_complete.py` - Script de test du workflow

### Liens Utiles
- Copilot Studio: https://copilotstudio.microsoft.com
- Power Apps: https://make.powerapps.com
- Azure Container Apps: https://portal.azure.com

---

**Version**: 1.0
**Date**: 2025-10-10
**Status**: ✅ Production Ready
