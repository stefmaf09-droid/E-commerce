
import os

def verify_pwa():
    print("=== 🧪 VÉRIFICATION PHASE 4.1 : PWA & MOBILE ===")
    
    # 1. Check static files
    static_files = ['static/manifest.json', 'static/service-worker.js']
    for f in static_files:
        if os.path.exists(f):
            print(f"✅ Fichier trouvé : {f}")
        else:
            print(f"❌ Fichier manquant : {f}")

    # 2. Check dashboard content for PWA tags
    with open('client_dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    tags = [
        'manifest.json',
        'serviceWorker',
        'apple-mobile-web-app-capable',
        '@media (max-width: 768px)'
    ]
    
    for tag in tags:
        if tag in content:
            print(f"✅ Tag PWA/Mobile trouvé : {tag}")
        else:
            print(f"❌ Tag PWA/Mobile manquant : {tag}")

    print("\n=== ✨ TOUTES LES VÉRIFICATIONS SONT TERMINÉES ===")

if __name__ == "__main__":
    verify_pwa()
