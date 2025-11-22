#!/usr/bin/env python3
"""
Script de test simple pour vérifier que les APIs fonctionnent.
Utilise requests pour tester les endpoints Foundation.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/foundation"

def test_api_endpoints():
    """Test les endpoints Foundation API."""
    
    print("🧪 Test des APIs Foundation...")
    
    # Test 1: Vérifier si le serveur répond
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ GET {BASE_URL}/ - Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}...")
    except Exception as e:
        print(f"❌ GET {BASE_URL}/ - Erreur: {e}")
        return False
    
    # Test 2: Inscription
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
        response = requests.post(f"{BASE_URL}/auth/register/client/", 
                               json=register_data,
                               headers={"Content-Type": "application/json"})
        print(f"✅ POST {BASE_URL}/auth/register/client/ - Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            print("🎉 Inscription réussie!")
            return True
        else:
            print(f"⚠️  Erreur d'inscription: {response.text}")
            
    except Exception as e:
        print(f"❌ POST {BASE_URL}/auth/register/client/ - Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Démarrage du test des APIs Foundation...")
    test_api_endpoints()
