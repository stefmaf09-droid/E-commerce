
import asyncio
from playwright.async_api import async_playwright
import json
import sys

async def get_tracking_playwright(tracking_number):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"Navigating to La Poste for {tracking_number}...")
            url = f"https://www.laposte.fr/outils/suivre-vos-envois?code={tracking_number}"
            await page.goto(url, timeout=30000)
            
            # Wait for content or cookie banner
            await asyncio.sleep(2)
            
            # Check if redirected to Chronopost or contains Chronopost info
            content = await page.content()
            content_lower = content.lower()
            
            status_text = "Unknown"
            if "mis à disposition" in content_lower or "retrait" in content_lower:
                status_text = "Mis à disposition en point de retrait"
            elif "livré" in content_lower:
                status_text = "Livré"
            elif "en cours" in content_lower:
                status_text = "En cours de livraison"
            
            print(f"Status found: {status_text}")
            return {"status": status_text, "success": True}
            
        except Exception as e:
            print(f"Error: {e}")
            return {"status": "Error", "success": False, "error": str(e)}
        finally:
            await browser.close()

if __name__ == "__main__":
    num = sys.argv[1] if len(sys.argv) > 1 else "XS419416933FR"
    result = asyncio.run(get_tracking_playwright(num))
    print(json.dumps(result))
