
import os

def verify_devops_gdpr():
    print("=== 🧪 VÉRIFICATION PHASE 4.4 : DÉVOPS & RGPD ===")
    
    # Check if admin dashboard contains the new keywords
    with open('admin_control_tower.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    keywords = [
        'Tech Monitoring',
        'Infrastructure (DevOps)',
        'RGPD',
        'Purger les logs'
    ]
    
    for kw in keywords:
        if kw in content:
            print(f"✅ Élément Admin trouvé : {kw}")
        else:
            print(f"❌ Élément Admin manquant : {kw}")

    print("\n=== ✨ TOUTES LES VÉRIFICATIONS SONT TERMINÉES ===")

if __name__ == "__main__":
    verify_devops_gdpr()
