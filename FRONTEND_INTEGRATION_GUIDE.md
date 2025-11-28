# 📚 Guide d'Intégration Frontend/Backend - NoCode Platform

## 🎯 Vue d'ensemble

Ce guide explique comment intégrer une application frontend (React/Vue/Angular) avec l'API backend NoCode Platform pour créer des applications dynamiques.

## 🔐 Authentification

### Login JWT
```javascript
// POST /api/v1/foundation/auth/login/
const login = async (email, password) => {
  const response = await fetch('/api/v1/foundation/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  // Stocker les tokens
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  
  return data.user;
};
```

### Headers d'authentification
```javascript
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json'
});
```

### Refresh token
```javascript
// POST /api/v1/foundation/auth/refresh/
const refreshToken = async () => {
  const response = await fetch('/api/v1/foundation/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      refresh: localStorage.getItem('refresh_token') 
    })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  return data.access;
};
```

## 🏗️ Gestion des Projets

### Lister les projets
```javascript
// GET /api/v1/runtime/projects/
const getProjects = async () => {
  const response = await fetch('/api/v1/runtime/projects/', {
    headers: getAuthHeaders()
  });
  return response.json();
};
```

### Créer un projet
```javascript
// POST /api/v1/runtime/projects/
const createProject = async (projectData) => {
  const response = await fetch('/api/v1/runtime/projects/', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(projectData)
  });
  return response.json();
};
```

## 📊 Schéma de Données Dynamique

### Obtenir le schéma complet d'un projet
```javascript
// GET /api/v1/runtime/projects/{id}/schema/
const getProjectSchema = async (projectId) => {
  const response = await fetch(`/api/v1/runtime/projects/${projectId}/schema/`, {
    headers: getAuthHeaders()
  });
  
  const schema = await response.json();
  
  // Structure retournée:
  // {
  //   "project": {
  //     "id": "uuid",
  //     "name": "Mon Projet",
  //     "schema_name": "mon_projet"
  //   },
  //   "tables": {
  //     "products": {
  //       "table_name": "products",
  //       "display_name": "Produits",
  //       "icon": "🛒",
  //       "description": "Catalogue des produits",
  //       "fields": [...]
  //     }
  //   }
  // }
  
  return schema;
};
```

### Obtenir le schéma d'une table spécifique
```javascript
// GET /api/v1/runtime/projects/{id}/schema/{table}/
const getTableSchema = async (projectId, tableName) => {
  const response = await fetch(`/api/v1/runtime/projects/${projectId}/schema/${tableName}/`, {
    headers: getAuthHeaders()
  });
  
  const schema = await response.json();
  
  // Structure pour formulaire:
  // {
  //   "table_name": "products",
  //   "display_name": "Produits",
  //   "fields": [
  //     {
  //       "name": "name",
  //       "display_name": "Nom du produit",
  //       "field_type": "TEXT_SHORT",
  //       "is_required": true,
  //       "validation": {"max_length": 255}
  //     }
  //   ]
  // }
  
  return schema;
};
```

## 🔄 Opérations CRUD

### Lister les données
```javascript
// GET /api/v1/runtime/projects/{id}/tables/{table}/
const listData = async (projectId, tableName, page = 1, pageSize = 20) => {
  const response = await fetch(
    `/api/v1/runtime/projects/${projectId}/tables/${tableName}/?page=${page}&page_size=${pageSize}`,
    { headers: getAuthHeaders() }
  );
  return response.json();
};
```

### Créer une entrée
```javascript
// POST /api/v1/runtime/projects/{id}/tables/{table}/
const createItem = async (projectId, tableName, data) => {
  const response = await fetch(`/api/v1/runtime/projects/${projectId}/tables/${tableName}/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return response.json();
};
```

### Mettre à jour une entrée
```javascript
// PUT /api/v1/runtime/projects/{id}/tables/{table}/{pk}/
const updateItem = async (projectId, tableName, itemId, data) => {
  const response = await fetch(`/api/v1/runtime/projects/${projectId}/tables/${tableName}/${itemId}/`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return response.json();
};
```

### Supprimer une entrée
```javascript
// DELETE /api/v1/runtime/projects/{id}/tables/{table}/{pk}/
const deleteItem = async (projectId, tableName, itemId) => {
  const response = await fetch(`/api/v1/runtime/projects/${projectId}/tables/${tableName}/${itemId}/`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  return response.ok;
};
```

## 🎨 Composants React Exemples

### Dashboard des projets
```jsx
import React, { useState, useEffect } from 'react';

const ProjectDashboard = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await getProjects();
      setProjects(data.results || data);
    } catch (error) {
      console.error('Erreur chargement projets:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Chargement...</div>;

  return (
    <div className="project-dashboard">
      <h1>Mes Projets</h1>
      <div className="project-grid">
        {projects.map(project => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  );
};

const ProjectCard = ({ project }) => (
  <div className="project-card">
    <h3>{project.name}</h3>
    <p>{project.description}</p>
    <a href={`/projects/${project.id}`}>Voir le projet</a>
  </div>
);
```

### Tableau dynamique
```jsx
import React, { useState, useEffect } from 'react';

const DynamicTable = ({ projectId, tableName }) => {
  const [schema, setSchema] = useState(null);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTableData();
  }, [projectId, tableName]);

  const loadTableData = async () => {
    try {
      const [schemaData, tableData] = await Promise.all([
        getTableSchema(projectId, tableName),
        listData(projectId, tableName)
      ]);
      
      setSchema(schemaData);
      setData(tableData.results || tableData);
    } catch (error) {
      console.error('Erreur chargement table:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Chargement...</div>;
  if (!schema) return <div>Schéma non trouvé</div>;

  return (
    <div className="dynamic-table">
      <h2>{schema.display_name}</h2>
      
      <table>
        <thead>
          <tr>
            {schema.fields.map(field => (
              <th key={field.name}>{field.display_name}</th>
            ))}
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.map(item => (
            <tr key={item.id}>
              {schema.fields.map(field => (
                <td key={field.name}>{item[field.name]}</td>
              ))}
              <td>
                <button onClick={() => editItem(item)}>Éditer</button>
                <button onClick={() => deleteItem(item.id)}>Supprimer</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <button onClick={() => createNewItem()}>Nouveau</button>
    </div>
  );
};
```

### Formulaire dynamique
```jsx
import React, { useState, useEffect } from 'react';

const DynamicForm = ({ projectId, tableName, itemId = null, onSave, onCancel }) => {
  const [schema, setSchema] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSchema();
    if (itemId) {
      loadItemData();
    }
  }, [projectId, tableName, itemId]);

  const loadSchema = async () => {
    try {
      const schemaData = await getTableSchema(projectId, tableName);
      setSchema(schemaData);
      
      // Initialiser formData avec valeurs par défaut
      const initialData = {};
      schemaData.fields.forEach(field => {
        initialData[field.name] = field.default_value || '';
      });
      setFormData(initialData);
    } catch (error) {
      console.error('Erreur chargement schéma:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadItemData = async () => {
    try {
      const response = await fetch(`/api/v1/runtime/projects/${projectId}/tables/${tableName}/${itemId}/`, {
        headers: getAuthHeaders()
      });
      const itemData = await response.json();
      setFormData(itemData);
    } catch (error) {
      console.error('Erreur chargement item:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      if (itemId) {
        await updateItem(projectId, tableName, itemId, formData);
      } else {
        await createItem(projectId, tableName, formData);
      }
      onSave();
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    } finally {
      setSaving(false);
    }
  };

  const renderField = (field) => {
    const value = formData[field.name] || '';
    
    switch (field.field_type) {
      case 'TEXT_SHORT':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
            required={field.is_required}
            maxLength={field.validation?.max_length}
          />
        );
        
      case 'TEXT_LONG':
        return (
          <textarea
            value={value}
            onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
            required={field.is_required}
          />
        );
        
      case 'NUMBER_INT':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => setFormData({...formData, [field.name]: parseInt(e.target.value)})}
            required={field.is_required}
          />
        );
        
      case 'NUMBER_DECIMAL':
        return (
          <input
            type="number"
            step="0.01"
            value={value}
            onChange={(e) => setFormData({...formData, [field.name]: parseFloat(e.target.value)})}
            required={field.is_required}
          />
        );
        
      case 'EMAIL':
        return (
          <input
            type="email"
            value={value}
            onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
            required={field.is_required}
          />
        );
        
      case 'BOOLEAN':
        return (
          <input
            type="checkbox"
            checked={value}
            onChange={(e) => setFormData({...formData, [field.name]: e.target.checked})}
          />
        );
        
      case 'DATE':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
            required={field.is_required}
          />
        );
        
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
            required={field.is_required}
          />
        );
    }
  };

  if (loading) return <div>Chargement...</div>;
  if (!schema) return <div>Schéma non trouvé</div>;

  return (
    <form onSubmit={handleSubmit} className="dynamic-form">
      <h3>{itemId ? 'Éditer' : 'Créer'} {schema.display_name}</h3>
      
      {schema.fields.map(field => (
        <div key={field.name} className="form-field">
          <label>
            {field.display_name} {field.is_required && '*'}
          </label>
          {renderField(field)}
        </div>
      ))}
      
      <div className="form-actions">
        <button type="submit" disabled={saving}>
          {saving ? 'Sauvegarde...' : (itemId ? 'Mettre à jour' : 'Créer')}
        </button>
        <button type="button" onClick={onCancel}>
          Annuler
        </button>
      </div>
    </form>
  );
};
```

## 🔧 Configuration du Frontend

### Variables d'environnement
```bash
# .env.local
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_VERSION=v1
```

### Client API
```javascript
// src/api/client.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}/api/${process.env.REACT_APP_API_VERSION || 'v1'}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    // Ajouter le token d'authentification si disponible
    const token = localStorage.getItem('access_token');
    if (token) {
      defaultOptions.headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, { ...defaultOptions, ...options });
    
    // Gérer le refresh token automatiquement
    if (response.status === 401) {
      await this.refreshToken();
      // Réessayer la requête avec le nouveau token
      const newToken = localStorage.getItem('access_token');
      defaultOptions.headers.Authorization = `Bearer ${newToken}`;
      return fetch(url, { ...defaultOptions, ...options });
    }

    return response;
  }

  async refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) throw new Error('No refresh token');

    const response = await fetch(`${this.baseURL}/api/v1/foundation/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    });

    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    return data.access;
  }

  // Méthodes pratiques
  get(endpoint) {
    return this.request(endpoint);
  }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
```

## 🚨 Gestion des Erreurs

### Intercepteur d'erreurs
```javascript
// src/utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.response) {
    // Erreur HTTP
    switch (error.response.status) {
      case 401:
        // Rediriger vers login
        window.location.href = '/login';
        break;
      case 403:
        // Permissions insuffisantes
        alert('Vous n\'avez pas les permissions pour cette action');
        break;
      case 404:
        // Ressource non trouvée
        alert('La ressource demandée n\'existe pas');
        break;
      case 500:
        // Erreur serveur
        alert('Erreur serveur, veuillez réessayer plus tard');
        break;
      default:
        alert(`Erreur: ${error.response.data.message || 'Erreur inconnue'}`);
    }
  } else if (error.request) {
    // Erreur réseau
    alert('Erreur de connexion, vérifiez votre internet');
  } else {
    // Erreur inattendue
    alert(`Erreur: ${error.message}`);
  }
};
```

## 📱 Exemple d'Application Complète

```jsx
// src/App.js
import React, { useState, useEffect } from 'react';
import { apiClient } from './api/client';
import { handleApiError } from './utils/errorHandler';

const App = () => {
  const [user, setUser] = useState(null);
  const [currentProject, setCurrentProject] = useState(null);

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté
    const token = localStorage.getItem('access_token');
    if (token) {
      loadUserProfile();
    }
  }, []);

  const loadUserProfile = async () => {
    try {
      const response = await apiClient.get('/foundation/auth/profile/');
      const userData = await response.json();
      setUser(userData);
    } catch (error) {
      handleApiError(error);
    }
  };

  const handleLogin = async (email, password) => {
    try {
      const response = await apiClient.post('/foundation/auth/login/', {
        email,
        password
      });
      const data = await response.json();
      
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      setUser(data.user);
    } catch (error) {
      handleApiError(error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setCurrentProject(null);
  };

  if (!user) {
    return <LoginForm onLogin={handleLogin} />;
  }

  if (currentProject) {
    return (
      <ProjectInterface 
        project={currentProject}
        onBack={() => setCurrentProject(null)}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <ProjectDashboard 
      user={user}
      onProjectSelect={setCurrentProject}
      onLogout={handleLogout}
    />
  );
};

export default App;
```

## 🎯 Bonnes Pratiques

1. **Gestion d'état**: Utiliser Redux/Zustand pour les applications complexes
2. **Validation**: Valider les données côté frontend avant envoi
3. **Loading states**: Afficher des indicateurs de chargement
4. **Error boundaries**: Capturer les erreurs React
5. **Pagination**: Implémenter la pagination pour les grandes tables
6. **Caching**: Mettre en cache les schémas de données
7. **Optimistic updates**: Mettre à jour l'UI immédiatement puis synchroniser

## 🔄 Workflow Complet

1. **Login** → Obtenir tokens JWT
2. **Charger projets** → Lister les projets de l'utilisateur
3. **Sélectionner projet** → Charger le schéma du projet
4. **Naviguer entre tables** → Charger les schémas et données dynamiquement
5. **CRUD operations** → Créer/lire/mettre à jour/supprimer des données
6. **Déployer** → Lancer le déploiement du frontend (voir section déploiement)

---

🚀 **Votre frontend est maintenant prêt à s'intégrer avec l'API NoCode Platform !**
