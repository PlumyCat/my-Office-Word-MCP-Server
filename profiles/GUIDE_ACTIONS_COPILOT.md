# Guide des Actions - Quand Utiliser Quoi

Guide pour configurer les actions dans Copilot Studio avec des instructions claires.

---

## 🎯 Actions Principales

### 1. WordPropal create proposal from template ⭐

**Quand l'utiliser**: Créer un nouveau document Word depuis un template avec remplacement de variables

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action quand l'utilisateur demande de créer, générer ou faire une proposition commerciale, un document, un contrat, ou tout document basé sur un modèle.

Exemples de phrases déclencheurs:
- "crée une proposition pour Jean Dupont"
- "génère un document pour le client X"
- "je veux faire une offre commerciale"
- "fais-moi un contrat"

Tu dois extraire automatiquement:
- Le nom du client (pour commercialName)
- L'email du client (pour commercialEmail)
- Le téléphone du client (pour commercialTel)
- Le contenu de l'offre (pour propalContent)
- Un nom de fichier (pour new_document_name): utilise le format "proposal_prenom_nom" en minuscules sans espaces

IMPORTANT - Gestion des templates:
Si l'utilisateur mentionne un template spécifique avec sa catégorie (ex: "utilise le template propal-modern-2024 dans Eric FER"):
- template_name: juste le nom "propal-modern-2024"
- category: la catégorie mentionnée "Eric FER"

Si l'utilisateur ne précise pas de template:
- template_name: "template-text"
- category: "general"

NE JAMAIS mettre la catégorie DANS le template_name (pas de "Eric FER/propal-modern-2024").
```

**Paramètres**:
- `template_name`: ✅ Généré par l'IA ou Valeur par défaut
  - **FORMAT 1 (recommandé)**: Juste le nom du template + paramètre category séparé
    - Exemple: `template_name = "propal-modern-2024"` + `category = "Eric FER"`
  - **FORMAT 2 (alternatif)**: Nom avec catégorie incluse (le paramètre category est ignoré)
    - Exemple: `template_name = "Eric FER/propal-modern-2024"`
- `new_document_name`: ✅ Généré par l'IA (ex: "proposal_jean_dupont")
- `category`: ✅ Généré par l'IA ou Valeur par défaut = `"general"`
  - Si template_name contient "/", ce paramètre est ignoré
- `variables`: ✅ Généré par l'IA (objet JSON avec les infos client)

---

### 2. WordPropal get document download URL

**Quand l'utiliser**: Récupérer l'URL d'un document déjà créé

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action quand l'utilisateur demande:
- Le lien d'un document
- L'URL d'un fichier
- De télécharger un document
- "où est le document X"

Exemples:
- "donne-moi le lien du document"
- "où je peux télécharger la proposition"
- "l'URL du fichier pour Jean Dupont"
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA (nom du document créé précédemment)

---

## 📝 Actions d'Édition de Contenu

### 3. WordPropal add heading to document

**Quand l'utiliser**: Ajouter un TITRE de section dans un document Word

**Ce que ça fait**:
- Ajoute un titre formaté (gras, grande taille)
- Le titre apparaît dans la table des matières
- Structure le document en sections

**Différence avec "add paragraph"**:
- `add_heading` = Titre de section (ex: "1. Introduction", "Chapitre 2")
- `add_paragraph` = Texte normal (ex: un paragraphe de contenu)

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action pour ajouter un TITRE ou SECTION au document.

Exemples de demandes:
- "ajoute un titre 'Introduction'"
- "crée une section 'Conditions Générales'"
- "mets un chapitre 'Tarifs'"
- "j'ai besoin d'un heading 'Présentation'"

NE PAS utiliser pour du texte normal - utilise "add paragraph" à la place.

Le paramètre 'level' détermine le niveau du titre:
- level 1 = Titre principal (le plus grand)
- level 2 = Sous-titre
- level 3 = Sous-sous-titre
- etc.

Utilise level 1 par défaut sauf si l'utilisateur précise "sous-titre" ou "section secondaire".
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA
- `text`: ✅ Généré par l'IA (le texte du titre)
- `level`: Valeur par défaut = `1` (peut être 1-9)

---

### 4. WordPropal add paragraph to document

**Quand l'utiliser**: Ajouter du TEXTE NORMAL dans un document

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action pour ajouter du texte normal, un paragraphe de contenu.

Exemples:
- "ajoute le texte suivant..."
- "écris un paragraphe qui dit..."
- "mets du contenu dans le doc"
- "ajoute cette description..."

NE PAS utiliser pour les titres - utilise "add heading" à la place.
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA
- `text`: ✅ Généré par l'IA (le texte du paragraphe)
- `style`: Optionnel (laisser vide par défaut)

---

### 5. WordPropal replace text in document

**Quand l'utiliser**: Remplacer du texte existant dans un document

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action quand l'utilisateur veut:
- Remplacer un texte par un autre
- Corriger une info dans le document
- Modifier une variable

Exemples:
- "remplace {{companyName}} par Contoso"
- "change tous les 'M.' par 'Monsieur'"
- "corrige le prix de 100€ à 120€"
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA
- `find_text`: ✅ Généré par l'IA (texte à chercher)
- `replace_text`: ✅ Généré par l'IA (texte de remplacement)

---

## 📊 Actions pour Tableaux

### 6. WordPropal add table to document with rows

**Quand l'utiliser**: Ajouter un nouveau tableau vide ou avec données

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action quand l'utilisateur demande:
- Un tableau
- Une grille
- Un listing en colonnes

Exemples:
- "ajoute un tableau 3x4"
- "crée une table avec 5 lignes et 3 colonnes"
- "fais un tableau de prix"

Paramètres:
- rows = nombre de lignes
- cols = nombre de colonnes
- data = données à mettre (optionnel)
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA
- `rows`: ✅ Généré par l'IA (nombre entier)
- `cols`: ✅ Généré par l'IA (nombre entier)
- `data`: Optionnel (array 2D)

---

### 7. WordPropal format table with borders

**Quand l'utiliser**: Formater un tableau existant (bordures, style)

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action APRÈS avoir créé un tableau, pour le mettre en forme.

Exemples:
- "mets des bordures sur le tableau"
- "formate la table"
- "style le tableau"
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA
- `table_index`: ✅ Généré par l'IA (0 pour le premier tableau, 1 pour le deuxième, etc.)
- Autres paramètres: Optionnels

---

### 8. WordPropal highlight table header colors

**Quand l'utiliser**: Colorer la première ligne du tableau (en-tête)

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action pour colorer l'en-tête d'un tableau.

Exemples:
- "mets l'en-tête en bleu"
- "colore la première ligne du tableau"
- "header en couleur"
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA
- `table_index`: ✅ Généré par l'IA (0 = premier tableau)
- `header_color`: Optionnel (ex: "4472C4" pour bleu)
- `text_color`: Optionnel (ex: "FFFFFF" pour blanc)

---

### 9. WordPropal apply alternating row colors

**Quand l'utiliser**: Appliquer des couleurs alternées aux lignes (zebra striping)

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action pour rendre un tableau plus lisible avec des lignes alternées.

Exemples:
- "lignes alternées sur le tableau"
- "zebra striping"
- "alterne les couleurs des lignes"
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA
- `table_index`: ✅ Généré par l'IA
- `color1`: Optionnel (ex: "FFFFFF")
- `color2`: Optionnel (ex: "F2F2F2")

---

### 10. WordPropal format cell text appearance

**Quand l'utiliser**: Formater le texte d'UNE cellule spécifique

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action pour modifier le style d'une cellule précise.

Exemples:
- "mets la cellule en gras"
- "change la couleur de la cellule ligne 2 colonne 3"
- "texte rouge dans la cellule Total"
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA
- `table_index`: ✅ Généré par l'IA (0 = premier tableau)
- `row_index`: ✅ Généré par l'IA (0 = première ligne)
- `col_index`: ✅ Généré par l'IA (0 = première colonne)
- Autres paramètres de style: Optionnels

---

## 🗂️ Actions de Gestion

### 11. WordPropal list all available templates

**Quand l'utiliser**: Lister les templates disponibles

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action quand l'utilisateur demande:
- "quels templates existent"
- "liste des modèles"
- "montre-moi les templates"

Note: Cette action retourne juste "ok" à cause du raccourcissement.
Pour avoir la vraie liste, informe l'utilisateur qu'il y a un template "template-text" disponible.
```

---

### 12. WordPropal list all generated documents

**Quand l'utiliser**: Lister les documents créés

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action quand l'utilisateur demande:
- "quels documents j'ai créés"
- "liste mes fichiers"
- "montre-moi mes documents"

Note: Cette action retourne juste "ok" à cause du raccourcissement.
```

---

### 13. WordPropal check if document exists

**Quand l'utiliser**: Vérifier si un document existe avant de le modifier

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action avant de modifier un document pour vérifier qu'il existe.

Retourne "ok" si le document existe, "error: not found" sinon.
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA

---

### 14. WordPropal remove document from storage

**Quand l'utiliser**: Supprimer un document

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action UNIQUEMENT si l'utilisateur demande explicitement de supprimer un document.

Exemples:
- "supprime le document X"
- "efface le fichier Y"

Demande confirmation avant de supprimer!
```

**Paramètres**:
- `filename`: ✅ Généré par l'IA

---

### 15. WordPropal get document information

**Quand l'utiliser**: Obtenir les métadonnées d'un document

**Instructions à mettre dans Copilot Studio**:
```
Utilise cette action pour obtenir des infos sur un document:
- Titre
- Auteur
- Nombre de pages
- Date de création

Note: Retourne juste "ok" à cause du raccourcissement, pas les vraies infos.
```

---

## 🔧 Actions Avancées (Rarement Utilisées)

### 16. WordPropal add document as template

**Quand l'utiliser**: Transformer un document existant en template

**Instructions**: Réservé à l'admin. Ne pas proposer automatiquement.

---

### 17. WordPropal remove template from library

**Quand l'utiliser**: Supprimer un template

**Instructions**: Réservé à l'admin. Ne pas proposer automatiquement.

---

## 📋 Résumé : Workflow Typique

### Scénario 1: Créer une Proposition Simple

1. User: "Crée une proposition pour Jean Dupont, email j.dupont@mail.com"
2. **Action**: `WordPropalCreateDocument`
   - Extrait: nom, email, tel (si fourni), contenu
   - Génère filename: "proposal_jean_dupont"
3. **Réponse**: URL du document créé

---

### Scénario 2: Créer et Enrichir un Document

1. User: "Crée une proposition pour Paul Martin"
2. **Action**: `WordPropalCreateDocument` → retourne URL
3. User: "Ajoute un titre 'Conditions Générales'"
4. **Action**: `WordPropalAddHeading`
   - filename: "proposal_paul_martin.docx"
   - text: "Conditions Générales"
   - level: 1
5. User: "Ajoute le paragraphe suivant: Paiement à 30 jours"
6. **Action**: `WordPropalAddParagraph`
   - filename: "proposal_paul_martin.docx"
   - text: "Paiement à 30 jours"

---

### Scénario 3: Créer avec Tableau

1. User: "Crée une proposition avec un tableau de prix"
2. **Action**: `WordPropalCreateDocument`
3. **Action**: `WordPropalAddTable`
   - rows: 4
   - cols: 3
   - data: [["Produit", "Prix", "Quantité"], ...]
4. **Action**: `WordPropalHighlightHeader`
   - Colore l'en-tête

---

## 🎯 Checklist Configuration Copilot Studio

Pour chaque action:

- [ ] Nom de l'action reconnaissable (avec "WordPropal")
- [ ] Instructions claires dans la description
- [ ] Exemples de phrases déclencheurs
- [ ] Tous les paramètres marqués "Généré par l'IA" ✅
- [ ] Valeurs par défaut pour paramètres optionnels
- [ ] Test dans le simulateur

---

## 💡 Tips pour l'IA Copilot

### Extraction Automatique d'Infos

L'IA Copilot peut extraire automatiquement:
- **Noms**: "Jean Dupont" → `commercialName: "Jean Dupont"`
- **Emails**: "j.dupont@mail.com" → `commercialEmail: "j.dupont@mail.com"`
- **Téléphones**: "06 12 34 56 78" → `commercialTel: "06 12 34 56 78"`
- **Offre**: "Microsoft 365 à 5€/user" → `propalContent: "Microsoft 365 à 5€/user"`

### Génération de Noms de Fichiers

Format recommandé: `proposal_prenom_nom`
- "Jean Dupont" → `"proposal_jean_dupont"`
- "Marie-Claire Martin" → `"proposal_marie_claire_martin"`
- "Mr Smith" → `"proposal_mr_smith"`

Règles:
- Minuscules
- Underscore au lieu d'espaces
- Pas de caractères spéciaux
- Extension .docx automatique
