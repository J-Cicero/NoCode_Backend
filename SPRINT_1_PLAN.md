# Sprint 1 - MVP Fonctionnel

## 🎯 Objectifs
1. ✅ Node/Edge pour Automation
2. ❌ Database Manager (créer tables dynamiques)
3. ❌ Frontend Generator (HTML basique)
4. ❌ Auth apps générées

## 📋 Plan détaillé

### 1. Node/Edge Integration (30 min)
- [x] Models créés (Node, Edge)
- [ ] Ajouter serializers
- [ ] Créer endpoints CRUD
- [ ] Tester sauvegarde graphe

### 2. Database Manager (45 min)
- [ ] Service `DatabaseManager`
  - Lire DataSchema du projet
  - Générer models.py dynamique
  - Créer migrations dynamiques
  - Exécuter migrations
- [ ] Test: Créer table "clients" depuis Studio
- [ ] Vérifier table PostgreSQL créée

### 3. Frontend Generator (45 min)
- [ ] Service `FrontendGenerator`
  - Lire ComponentInstance
  - Générer HTML templates
  - Créer pages navigables
- [ ] Templates de base:
  - Button
  - Input
  - Table
  - Form
- [ ] Test: Page HTML générée avec formulaire

### 4. Auth apps générées (30 min)
- [ ] Service `AuthGenerator`
  - Ajouter User model dans apps générées
  - Générer Login/Register pages
  - JWT auth par défaut
- [ ] Test: Connexion sur app générée

---

## 🔧 Fichiers à créer

```
apps/runtime/services/
  ├─ database_manager.py      # Service création DB
  ├─ frontend_generator.py    # Service génération HTML
  └─ auth_generator.py        # Service auth

apps/automation/
  ├─ serializers_graph.py     # Serializers Node/Edge
  └─ views_graph.py          # Endpoints CRUD
```

---

## 🧪 Tests à faire

1. **Foundation**: Inscription/Connexion ✅
2. **Studio**: Créer projet + table
3. **Runtime**: Générer DB réelle
4. **Frontend**: Voir page HTML générée
5. **Auth**: Se connecter sur app générée

---

## ⚡ Workflow complet

1. User crée projet dans Studio
2. Définit table "clients" (nom, email, téléphone)
3. Runtime génère la table PostgreSQL
4. Frontend génère page avec formulaire
5. Auth génère login/register
6. User peut utiliser son app !

**Prêt à commencer ?** 🚀
