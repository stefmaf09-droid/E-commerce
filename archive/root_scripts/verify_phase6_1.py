
import os
import sys
import time

# Add root to path
sys.path.append(os.getcwd())

from src.utils.resilience import CircuitBreaker, CircuitBreakerOpenException

def verify_phase6_1():
    print("=== 🧪 VÉRIFICATION PHASE 6.1 : RESILIENCE (CIRCUIT BREAKER) ===")
    
    # 1. Test Circuit Breaker Logic
    print("\n--- 🛡️ Testing Circuit Breaker Pattern ---")
    
    class TestAPI:
        fail = True
        
        @CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        def call_external_service(self):
            if self.fail:
                raise Exception("API Down")
            return "Success"
            
    api = TestAPI()
    
    # Fail 1, 2, 3
    for _ in range(3):
        try: api.call_external_service()
        except Exception as e: 
            if "API Down" in str(e): pass
    
    # 4th call should be blocked immediately
    try:
        api.call_external_service()
        print("❌ Error: Call was NOT blocked by open circuit.")
    except CircuitBreakerOpenException:
        print("✅ Circuit Breaker correctly BLOCKED call (OPEN state)")
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")

    # Wait for recovery
    print("Waiting for recovery timeout (1.1s)...")
    time.sleep(1.2)
    
    # Try again -> should pass if fail is False
    api.fail = False
    try:
        result = api.call_external_service()
        print(f"✅ Recovery successful: {result}")
    except Exception as e:
        print(f"❌ Failed to recover: {e}")

    # 2. Check Dockerfile
    print("\n--- 🐳 Docker Readiness Check ---")
    with open('Dockerfile', 'r', encoding='utf-8') as f:
        if 'HEALTHCHECK' in f.read():
            print("✅ Docker: HEALTHCHECK found.")

    print("\n=== ✨ VÉRIFICATION PHASE 6.1 TERMINÉE ===")

if __name__ == "__main__":
    verify_phase6_1()
