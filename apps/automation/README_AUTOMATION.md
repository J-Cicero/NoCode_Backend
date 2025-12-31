# Module AUTOMATION

## Rôle
Workflows automatisés avec éditeur visuel basé sur un système de graphes (Node/Edge).

## ✅ SYSTÈME ACTUEL - Node/Edge (Graphe Visuel)

### Architecture Moderne
Le module utilise un **système de graphe visuel** avec des Nodes et Edges pour créer des workflows complexes.

### Modèles Principaux
- **Node** : Nœuds du workflow (trigger, action, condition, math, string, data, api, email, etc.)
- **Edge** : Connexions entre les nœuds avec ports source/target
- **Workflow** : Conteneur principal du workflow
- **WorkflowExecution** : Historique et tracking des exécutions

### Types de Nodes Supportés
- `trigger` : Déclenche le workflow (webhook, schedule, event)
- `action` : Effectue une action (create_record, update_record, delete_record)
- `condition` : Branchement conditionnel (if/else)
- `math` : Opérations mathématiques
- `string` : Manipulation de texte
- `data` : Transformation de données
- `api` : Appels API externes
- `email` : Envoi d'emails
- `delay` : Temporisation

### Éditeur Visuel
Chaque Node possède :
- `position_x` et `position_y` : Coordonnées pour l'interface graphique
- `config` : Configuration JSON du nœud
- Connexions via Edges avec ports d'entrée/sortie

### ⚠️ Note : Ancien Système (Déprécié)
L'ancien système `WorkflowStep` (séquentiel) est conservé pour compatibilité mais **ne devrait plus être utilisé**. Utilisez exclusivement le système Node/Edge pour les nouveaux workflows.
