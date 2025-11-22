# Module STUDIO

## Rôle
Éditeur No-Code pour créer applications sans coder.

## Utilisateur fait quoi ?

### 1. Créer projet
```bash
POST /api/v1/studio/projects/
```

### 2. Définir tables
```bash
POST /api/v1/studio/projects/{id}/add_table/
```

**Types de champs proposés:**
- text
- number
- email
- boolean
- date
- datetime
- file
- json
- relation

### 3. Créer pages et composants
- Drag & drop
- Configuration data_table
- Configuration form

## APIs CRUD complètes
✅ GET, POST, PUT, DELETE disponibles
