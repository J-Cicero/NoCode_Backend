# 🌍 Architecture de Déploiement Frontend Dynamique

## 🎯 Objectif

Créer un système de déploiement automatique du frontend comme Vercel, intégré dans la plateforme NoCode. Quand un utilisateur crée un projet → déploiement automatique → URL live immédiatement.

## 🏗️ Architecture Choisie : Self-Hosted Nginx

### **Pourquoi pas Vercel API ?**
- ❌ Dépendance externe (tokens, rate limits, coûts)
- ❌ Complexité de gestion multi-tenant
- ❌ Pas de contrôle total sur l'infrastructure
- ❌ Limites de personnalisation

### **Avantages Self-Hosted :**
- ✅ Contrôle total de l'infrastructure
- ✅ Scalabilité infinie avec sous-domaines
- ✅ Pas de coûts par déploiement
- ✅ Intégration parfaite avec le backend
- ✅ Personnalisation complète

## 🏛️ Architecture Technique

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Django API    │───▶│  Frontend Build  │───▶│  Nginx Static   │
│   (Runtime)     │    │   (React/Vue)    │    │   Deployment    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ PostgreSQL DB   │    │   Build Cache    │    │   SSL Auto      │
│                 │    │                  │    │   (Let's Encrypt)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Workflow de Déploiement

### **1. Création du Projet**
```python
# POST /api/v1/runtime/projects/
{
  "name": "Mon App NoCode",
  "schema_name": "mon_app_12345"
}
```

### **2. Génération Automatique**
```python
# Signal post_save sur Project
@receiver(post_save, sender=Project)
def auto_deploy_frontend(sender, instance, created, **kwargs):
    if created:
        deploy_app_task.delay(
            project_id=instance.id,
            deployment_type='frontend_full'
        )
```

### **3. Build du Frontend**
```python
# apps/runtime/services/frontend_builder.py
class FrontendBuilder:
    def build_from_schema(self, project):
        # 1. Générer le code React/Vue depuis le schéma
        # 2. Installer les dépendances (npm install)
        # 3. Build production (npm run build)
        # 4. Optimiser et minifier
        return build_path
```

### **4. Déploiement Nginx**
```python
# apps/runtime/services/nginx_deployer.py
class NginxDeployer:
    def deploy_static_site(self, project, build_path):
        # 1. Copier les fichiers dans /var/www/apps/{project_id}
        # 2. Générer la configuration Nginx
        # 3. Recharger Nginx
        # 4. Configurer SSL automatique
        return deployment_url
```

## 🌐 URLs des Applications Déployées

### **Format 1 : Sous-domaines**
```
https://mon-app-12345.votredomaine.com
https://client-project.votredomaine.com
https://shop-abcde.votredomaine.com
```

### **Format 2 : Sous-répertoires**
```
https://votredomaine.com/apps/mon-app-12345
https://votredomaine.com/apps/client-project
https://votredomaine.com/apps/shop-abcde
```

### **Format 3 : Domaines personnalisés**
```
https://www.mon-app-client.com  (via CNAME)
https://app.mon-entreprise.fr     (via CNAME)
```

## 💻 Code Technique

### **Extension du Runtime Module**
```python
# apps/runtime/tasks.py (étendu)
@shared_task(bind=True, max_retries=3)
def deploy_full_app_task(self, project_id, deployment_type='frontend_full'):
    """
    Déploie le backend + frontend complet pour un projet NoCode.
    """
    try:
        with transaction.atomic():
            project = Project.objects.get(id=project_id)
            
            # 1. Créer le log de déploiement
            deployment_log = DeploymentLog.objects.create(
                app=None,  # Pas d'app GeneratedApp pour le frontend pur
                project=project,
                deployment_type=deployment_type,
                status='in_progress'
            )
            
            # 2. Builder le frontend
            frontend_builder = FrontendBuilder(project)
            build_result = frontend_builder.build_from_schema()
            
            if not build_result.success:
                raise Exception(f"Build failed: {build_result.error}")
            
            # 3. Déployer sur Nginx
            nginx_deployer = NginxDeployer()
            deployment_result = nginx_deployer.deploy_static_site(
                project, 
                build_result.build_path
            )
            
            # 4. Mettre à jour le projet avec l'URL
            project.frontend_url = deployment_result.url
            project.deployment_status = 'deployed'
            project.save()
            
            # 5. Finaliser le log
            deployment_log.status = 'completed'
            deployment_log.deployment_url = deployment_result.url
            deployment_log.save()
            
            logger.info(f"App deployed successfully: {deployment_result.url}")
            
            return {
                'project_id': project_id,
                'deployment_url': deployment_result.url,
                'status': 'completed'
            }
            
    except Exception as exc:
        logger.error(f"Deployment failed for project {project_id}: {exc}")
        deployment_log.status = 'failed'
        deployment_log.error_message = str(exc)
        deployment_log.save()
        raise self.retry(exc=exc, countdown=60)
```

### **Service de Build Frontend**
```python
# apps/runtime/services/frontend_builder.py
import subprocess
import tempfile
import shutil
from pathlib import Path
from django.conf import settings
import json

class FrontendBuilder:
    def __init__(self, project):
        self.project = project
        self.build_dir = Path(settings.FRONTEND_BUILD_ROOT) / f"project_{project.id}"
        
    def build_from_schema(self):
        """
        Génère et build le frontend React depuis le schéma du projet.
        """
        try:
            # 1. Créer le répertoire de build
            self.build_dir.mkdir(parents=True, exist_ok=True)
            
            # 2. Générer le code React
            self._generate_react_app()
            
            # 3. Installer les dépendances
            self._install_dependencies()
            
            # 4. Build production
            build_path = self._build_production()
            
            return BuildResult(
                success=True,
                build_path=build_path,
                url=f"https://{self.project.schema_name}.{settings.FRONTEND_DOMAIN}"
            )
            
        except Exception as e:
            logger.error(f"Frontend build failed: {e}")
            return BuildResult(success=False, error=str(e))
    
    def _generate_react_app(self):
        """
        Génère le code de l'application React depuis le schéma.
        """
        # Récupérer le schéma du projet
        schema_response = requests.get(
            f"http://localhost:8000/api/v1/runtime/projects/{self.project.id}/schema/"
        )
        schema = schema_response.json()
        
        # Générer les composants React
        generator = ReactCodeGenerator(schema, self.build_dir)
        generator.generate_app()
    
    def _install_dependencies(self):
        """
        Installe les dépendances npm.
        """
        result = subprocess.run(
            ['npm', 'install'],
            cwd=self.build_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            raise Exception(f"npm install failed: {result.stderr}")
    
    def _build_production(self):
        """
        Build l'application pour la production.
        """
        result = subprocess.run(
            ['npm', 'run', 'build'],
            cwd=self.build_dir,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            raise Exception(f"npm build failed: {result.stderr}")
        
        return self.build_dir / 'build'

class ReactCodeGenerator:
    def __init__(self, schema, output_dir):
        self.schema = schema
        self.output_dir = output_dir
        
    def generate_app(self):
        """
        Génère l'application React complète.
        """
        # 1. Créer la structure de base
        self._create_base_structure()
        
        # 2. Générer package.json
        self._generate_package_json()
        
        # 3. Générer les composants dynamiques
        self._generate_components()
        
        # 4. Générer les routes
        self._generate_routes()
        
        # 5. Générer App.js
        self._generate_app_js()
        
        # 6. Générer index.html
        self._generate_index_html()
    
    def _create_base_structure(self):
        """Crée la structure de dossiers React."""
        dirs = ['src', 'src/components', 'src/pages', 'src/services', 'public']
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _generate_package_json(self):
        """Génère package.json avec les dépendances nécessaires."""
        package_json = {
            "name": self.schema['project']['schema_name'],
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.8.0",
                "axios": "^1.3.0"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "devDependencies": {
                "react-scripts": "5.0.1"
            },
            "browserslist": {
                "production": [
                    ">0.2%",
                    "not dead",
                    "not op_mini all"
                ],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version"
                ]
            }
        }
        
        with open(self.output_dir / 'package.json', 'w') as f:
            json.dump(package_json, f, indent=2)
    
    def _generate_components(self):
        """Génère les composants dynamiques depuis le schéma."""
        for table_name, table_config in self.schema['tables'].items():
            self._generate_table_component(table_name, table_config)
    
    def _generate_table_component(self, table_name, table_config):
        """Génère un composant pour une table spécifique."""
        component_name = self._to_pascal_case(table_name)
        
        component_code = f'''
import React, {{ useState, useEffect }} from 'react';
import {{ apiClient }} from '../services/api';

const {component_name} = () => {{
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    loadData();
  }}, []);

  const loadData = async () => {{
    try {{
      const response = await apiClient.get('/runtime/projects/{self.schema['project']['id']}/tables/{table_name}/');
      const result = await response.json();
      setData(result.results || result);
    }} catch (error) {{
      console.error('Error loading data:', error);
    }} finally {{
      setLoading(false);
    }}
  }};

  if (loading) return <div>Loading...</div>;

  return (
    <div className="{table_name}-component">
      <h2>{table_config['display_name']}</h2>
      <div className="data-grid">
        {{data.map(item => (
          <div key={{item.id}} className="data-item">
            {self._generate_item_display(table_config['fields'])}
          </div>
        ))}}
      </div>
    </div>
  );
}};

export default {component_name};
'''
        
        component_file = self.output_dir / 'src' / 'components' / f'{component_name}.js'
        with open(component_file, 'w') as f:
            f.write(component_code)
```

### **Déploiement Nginx Automatique**
```python
# apps/runtime/services/nginx_deployer.py
import os
import subprocess
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class NginxDeployer:
    def __init__(self):
        self.sites_dir = Path('/etc/nginx/sites-available')
        self.enabled_dir = Path('/etc/nginx/sites-enabled')
        self.www_root = Path('/var/www/apps')
        
    def deploy_static_site(self, project, build_path):
        """
        Déploie un site statique sur Nginx avec SSL automatique.
        """
        try:
            # 1. Copier les fichiers build
            self._copy_static_files(project, build_path)
            
            # 2. Générer la configuration Nginx
            self._generate_nginx_config(project)
            
            # 3. Activer le site
            self._enable_site(project)
            
            # 4. Configurer SSL avec Let's Encrypt
            ssl_url = self._setup_ssl(project)
            
            # 5. Recharger Nginx
            self._reload_nginx()
            
            return DeploymentResult(
                success=True,
                url=ssl_url,
                status='deployed'
            )
            
        except Exception as e:
            logger.error(f"Nginx deployment failed: {e}")
            return DeploymentResult(success=False, error=str(e))
    
    def _copy_static_files(self, project, build_path):
        """Copie les fichiers build dans le répertoire web."""
        target_dir = self.www_root / project.schema_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copier tous les fichiers du build
        subprocess.run([
            'cp', '-r', f'{build_path}/.', str(target_dir)
        ], check=True)
        
        # Configurer les permissions
        subprocess.run([
            'chown', '-R', 'www-data:www-data', str(target_dir)
        ], check=True)
        subprocess.run([
            'chmod', '-R', '755', str(target_dir)
        ], check=True)
    
    def _generate_nginx_config(self, project):
        """Génère la configuration Nginx pour le site."""
        domain = f"{project.schema_name}.{settings.FRONTEND_DOMAIN}"
        
        config_template = f'''
server {{
    listen 80;
    server_name {domain};
    
    # Redirection vers HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {domain};
    
    # Configuration SSL
    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Racine des fichiers statiques
    root /var/www/apps/{project.schema_name}/build;
    index index.html;
    
    # Gestion du routing React
    location / {{
        try_files $uri $uri/ /index.html;
    }}
    
    # Cache des assets statiques
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
    
    # API proxy vers backend
    location /api/ {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
'''
        
        config_file = self.sites_dir / project.schema_name
        with open(config_file, 'w') as f:
            f.write(config_template)
    
    def _setup_ssl(self, project):
        """Configure SSL avec Let's Encrypt."""
        domain = f"{project.schema_name}.{settings.FRONTEND_DOMAIN}"
        
        # Générer le certificat SSL
        subprocess.run([
            'certbot', '--nginx',
            '-d', domain,
            '--non-interactive',
            '--agree-tos',
            '--email', f'admin@{settings.FRONTEND_DOMAIN}'
        ], check=True)
        
        return f"https://{domain}"
    
    def _enable_site(self, project):
        """Active le site Nginx."""
        # Créer le lien symbolique
        available = self.sites_dir / project.schema_name
        enabled = self.enabled_dir / project.schema_name
        
        if enabled.exists():
            enabled.unlink()
        
        enabled.symlink_to(available)
    
    def _reload_nginx(self):
        """Recharge la configuration Nginx."""
        subprocess.run(['nginx', '-t'], check=True)
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
```

## 📊 Monitoring et Gestion

### **API de Monitoring**
```python
# GET /api/v1/runtime/projects/{id}/deployment-status
{
    "project_id": "uuid",
    "status": "deployed",
    "frontend_url": "https://mon-app.votredomaine.com",
    "deployment_logs": [
        {
            "timestamp": "2025-01-15T10:30:00Z",
            "step": "build",
            "status": "completed",
            "message": "React build completed successfully"
        },
        {
            "timestamp": "2025-01-15T10:31:00Z", 
            "step": "deploy",
            "status": "completed",
            "message": "Nginx deployment completed"
        }
    ]
}
```

### **Redéploiement**
```python
# POST /api/v1/runtime/projects/{id}/redeploy
{
    "force_rebuild": true,
    "clear_cache": false
}
```

## 🔧 Configuration Requise

### **Variables d'environnement**
```bash
# .env
FRONTEND_DOMAIN=votredomaine.com
FRONTEND_BUILD_ROOT=/tmp/nocode_builds
NGINX_SITES_DIR=/etc/nginx/sites-available
NGINX_WWW_ROOT=/var/www/apps
SSL_EMAIL=admin@votredomaine.com
```

### **Configuration Nginx principale**
```nginx
# /etc/nginx/nginx.conf
http {
    include /etc/nginx/sites-enabled/*;
    
    # Configuration générale
    client_max_body_size 100M;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
}
```

### **Services système requis**
```bash
# Installation des dépendances
sudo apt install nginx certbot python3-certbot-nginx

# Configuration du firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow 8000  # Django API

# Configuration des permissions
sudo usermod -a -G www-data $USER
```

## 🚀 Déploiement Initial

### **1. Configuration du domaine**
```bash
# Configurer le DNS wildcart
*.votredomaine.com   A   VOTRE_IP_PUBLIQUE
```

### **2. Installation des services**
```bash
# Script d'installation
#!/bin/bash
# install_frontend_deployment.sh

# Installer Nginx
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Configurer les répertoires
sudo mkdir -p /var/www/apps
sudo chown -R www-data:www-data /var/www/apps

# Configurer les permissions
sudo usermod -a -G www-data $USER

# Tester la configuration
sudo nginx -t
sudo systemctl restart nginx
```

### **3. Test du système**
```python
# Test de déploiement
from apps.runtime.services import FrontendBuilder, NginxDeployer

project = Project.objects.first()
builder = FrontendBuilder(project)
build_result = builder.build_from_schema()

if build_result.success:
    deployer = NginxDeployer()
    deployment = deployer.deploy_static_site(project, build_result.build_path)
    print(f"App deployed at: {deployment.url}")
```

## 📈 Performance et Scalabilité

### **Optimisations**
- **Build cache** : Réutiliser les builds précédents
- **CDN integration** : Cloudflare pour la distribution mondiale
- **Auto-scaling** : Ajout de serveurs Nginx automatiquement
- **Monitoring** : Métriques de performance en temps réel

### **Limites gérées**
- **Build timeout** : 10 minutes maximum par build
- **Storage limits** : Quotas par projet
- **Rate limiting** : Limites de requêtes par utilisateur
- **Resource monitoring** : CPU/RAM par déploiement

---

🚀 **Avec cette architecture, chaque utilisateur dispose de son propre URL live comme Vercel, mais avec un contrôle total et sans coûts par déploiement !**
