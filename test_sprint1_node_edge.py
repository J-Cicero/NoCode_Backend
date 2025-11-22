#!/usr/bin/env python3

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_foundation_auth():
    """Test l'authentification Foundation d'abord."""
    print("🧪 Test Authentification Foundation...")
    
    # Inscription
    register_data = {
        "email": "test@example.com",
        "password": "TestPass123@",
        "password_confirm": "TestPass123@", 
        "nom": "Test",
        "prenom": "User",
        "pays": "France",
        "numero_telephone": "0123456789"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/foundation/auth/register/client/", 
                               json=register_data,
                               headers={"Content-Type": "application/json"})
        print(f"✅ Inscription: {response.status_code}")
        if response.status_code == 201:
            print(f"   Token: {response.json().get('access', 'N/A')}")
        else:
            print(f"   Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Inscription échouée: {e}")
        return None
    
    # Connexion
    login_data = {
        "email": "test@example.com",
        "password": "TestPass123@"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/foundation/auth/login/", 
                               json=login_data,
                               headers={"Content-Type": "application/json"})
        print(f"✅ Connexion: {response.status_code}")
        if response.status_code == 200:
            token = response.json().get('access')
            print(f"   Token obtenu: {token[:20]}...")
            return token
        else:
            print(f"   Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Connexion échouée: {e}")
    
    return None

def test_automation_workflows(token):
    """Test les workflows Automation."""
    print("\n🧪 Test Workflows Automation...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Créer un workflow
    workflow_data = {
        "name": "Test Workflow Node/Edge",
        "description": "Workflow pour tester l'intégration Node/Edge",
        "is_active": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/automation/workflows/", 
                               json=workflow_data,
                               headers=headers)
        print(f"✅ Création workflow: {response.status_code}")
        if response.status_code == 201:
            workflow_id = response.json()['id']
            print(f"   Workflow ID: {workflow_id}")
            return workflow_id, headers
        else:
            print(f"   Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Création workflow échouée: {e}")
    
    return None, headers

def test_node_edge_operations(workflow_id, headers):
    """Test les opérations Node/Edge."""
    print(f"\n🧪 Test Node/Edge pour workflow {workflow_id}...")
    
    # Créer un nœud trigger
    node_data = {
        "node_type": "trigger",
        "label": "Webhook Trigger",
        "position_x": 100,
        "position_y": 100,
        "config": {"trigger_type": "webhook", "url": "/test"}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/automation/workflows/{workflow_id}/nodes/", 
                               json=node_data,
                               headers=headers)
        print(f"✅ Création nœud: {response.status_code}")
        if response.status_code == 201:
            node_id = response.json()['id']
            print(f"   Node ID: {node_id}")
        else:
            print(f"   Erreur: {response.text}")
            return
    except Exception as e:
        print(f"❌ Création nœud échouée: {e}")
        return
    
    # Créer un nœud action
    action_data = {
        "node_type": "action",
        "label": "Send Email",
        "position_x": 300,
        "position_y": 100,
        "config": {"action_type": "email", "to": "test@example.com"}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/automation/workflows/{workflow_id}/nodes/", 
                               json=action_data,
                               headers=headers)
        print(f"✅ Création action: {response.status_code}")
        if response.status_code == 201:
            action_id = response.json()['id']
            print(f"   Action ID: {action_id}")
        else:
            print(f"   Erreur: {response.text}")
            return
    except Exception as e:
        print(f"❌ Création action échouée: {e}")
        return
    
    # Voir le graphe complet
    try:
        response = requests.get(f"{BASE_URL}/automation/workflows/{workflow_id}/graph/", 
                               headers=headers)
        print(f"✅ Graphe complet: {response.status_code}")
        if response.status_code == 200:
            graph = response.json()
            nodes = graph.get('nodes', [])
            edges = graph.get('edges', [])
            print(f"   📊 Nœuds: {len(nodes)}, Arêtes: {len(edges)}")
            for node in nodes:
                print(f"      - {node['label']} ({node['node_type']})")
        else:
            print(f"   Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Lecture graphe échouée: {e}")

def main():
    """Fonction principale de test."""
    print("🚀 Démarrage des tests Sprint 1 - Node/Edge Integration")
    print("=" * 60)
    
    # Attendre que le serveur soit prêt
    print("⏳ Attente du serveur Django...")
    time.sleep(2)
    
    # Test authentification
    token = test_foundation_auth()
    if not token:
        print("\n❌ Échec de l'authentification - arrêt des tests")
        return
    
    # Test workflows
    result = test_automation_workflows(token)
    workflow_id, headers = result
    
    if workflow_id:
        # Test Node/Edge
        test_node_edge_operations(workflow_id, headers)
        print(f"\n✅ Tests terminés avec succès !")
        print(f"🌐 Interface Swagger: http://127.0.0.1:8000/api/schema/swagger-ui/")
        print(f"📊 Workflow créé: {workflow_id}")
    else:
        print("\n❌ Échec de la création du workflow")

if __name__ == "__main__":
    main()
