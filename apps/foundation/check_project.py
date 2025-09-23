#!/usr/bin/env python3
"""
Script de vérification du projet Foundation.
Vérifie la syntaxe, les imports et la cohérence du code.
"""
import os
import sys
import py_compile
import importlib.util
from pathlib import Path

def check_syntax_errors():
    """Vérifie les erreurs de syntaxe Python."""
    print("🔍 Vérification de la syntaxe Python...")
    foundation_path = Path(__file__).parent
    python_files = list(foundation_path.rglob("*.py"))
    
    errors = []
    for file_path in python_files:
        if "__pycache__" in str(file_path):
            continue
            
        try:
            py_compile.compile(str(file_path), doraise=True)
            print(f"✅ {file_path.relative_to(foundation_path)}")
        except py_compile.PyCompileError as e:
            errors.append(f"❌ {file_path.relative_to(foundation_path)}: {e}")
            print(f"❌ {file_path.relative_to(foundation_path)}: {e}")
    
    return errors

def check_import_consistency():
    """Vérifie la cohérence des imports."""
    print("\n🔍 Vérification de la cohérence des imports...")
    
    # Vérifier les imports des modèles
    models_init = Path(__file__).parent / "models" / "__init__.py"
    if models_init.exists():
        with open(models_init, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Vérifier que tous les modèles importés existent
        import_issues = []
        
        # Liste des modèles qui devraient exister
        expected_models = [
            'BaseModel', 'TimestampedModel', 'SoftDeleteModel', 'UUIDModel',
            'User', 'Client', 'Entreprise',
            'Organization', 'OrganizationMember', 'OrganizationInvitation', 'OrganizationSettings',
            'TypeAbonnement', 'Abonnement',
            'MoyenDePaiement', 'Paiement', 'Facture', 'HistoriqueTarification',
            'DocumentVerification', 'DocumentUpload'
        ]
        
        for model in expected_models:
            if model in content:
                print(f"✅ Modèle {model} importé")
            else:
                import_issues.append(f"❌ Modèle {model} manquant dans __init__.py")
        
        return import_issues
    
    return ["❌ Fichier models/__init__.py non trouvé"]

def check_file_structure():
    """Vérifie la structure des fichiers."""
    print("\n🔍 Vérification de la structure des fichiers...")
    
    foundation_path = Path(__file__).parent
    required_dirs = [
        "models", "services", "serializers", "views", "permissions",
        "middleware", "integrations", "tasks", "utils", "tests"
    ]
    
    structure_issues = []
    for dir_name in required_dirs:
        dir_path = foundation_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"✅ Répertoire {dir_name}")
            
            # Vérifier que le répertoire contient un __init__.py
            init_file = dir_path / "__init__.py"
            if init_file.exists():
                print(f"✅ {dir_name}/__init__.py")
            else:
                structure_issues.append(f"❌ {dir_name}/__init__.py manquant")
        else:
            structure_issues.append(f"❌ Répertoire {dir_name} manquant")
    
    return structure_issues

def check_test_files():
    """Vérifie les fichiers de test."""
    print("\n🔍 Vérification des fichiers de test...")
    
    tests_path = Path(__file__).parent / "tests"
    required_test_files = [
        "test_models.py", "test_services.py", "test_views.py", "test_utils.py"
    ]
    
    test_issues = []
    for test_file in required_test_files:
        file_path = tests_path / test_file
        if file_path.exists():
            print(f"✅ {test_file}")
            
            # Vérifier que le fichier contient des tests
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "class" in content and "TestCase" in content:
                    print(f"✅ {test_file} contient des classes de test")
                else:
                    test_issues.append(f"❌ {test_file} ne contient pas de classes de test valides")
        else:
            test_issues.append(f"❌ {test_file} manquant")
    
    return test_issues

def main():
    """Fonction principale de vérification."""
    print("🚀 Vérification du projet Foundation\n")
    
    all_issues = []
    
    # Vérification de la syntaxe
    syntax_errors = check_syntax_errors()
    all_issues.extend(syntax_errors)
    
    # Vérification des imports
    import_issues = check_import_consistency()
    all_issues.extend(import_issues)
    
    # Vérification de la structure
    structure_issues = check_file_structure()
    all_issues.extend(structure_issues)
    
    # Vérification des tests
    test_issues = check_test_files()
    all_issues.extend(test_issues)
    
    # Résumé
    print(f"\n📊 Résumé de la vérification:")
    print(f"Total des problèmes détectés: {len(all_issues)}")
    
    if all_issues:
        print("\n❌ Problèmes détectés:")
        for issue in all_issues:
            print(f"  {issue}")
        return 1
    else:
        print("\n✅ Aucun problème détecté! Le projet Foundation est prêt.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
