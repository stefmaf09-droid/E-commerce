# 🧪 Tests - Guide d'Utilisation

## Installation des Dépendances de Test

```bash
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

## Lancer Tous les Tests

```bash
# Tous les tests avec couverture
pytest

# Tests avec output verbeux
pytest -v

# Tests avec couverture détaillée
pytest --cov=src --cov-report=html
```

## Lancer des Tests Spécifiques

```bash
# Tests de base de données uniquement
pytest tests/test_database.py

# Tests d'emails uniquement
pytest tests/test_email_notifications.py

# Tests E2E uniquement
pytest tests/test_e2e_workflows.py -m e2e

# Tests de sécurité uniquement
pytest tests/test_security.py

# Tests de paiement uniquement
pytest tests/test_payment_processing.py
```

## Lancer par Markers

```bash
# Exclure les tests lents
pytest -m "not slow"

# Seulement tests d'intégration
pytest -m integration

# Tests E2E
pytest -m e2e

# Tests nécessitant API externe (skip)
pytest -m "not requires_api"
```

## Couverture de Code

```bash
# Générer rapport HTML
pytest --cov=src --cov-report=html

# Ouvrir le rapport
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

## Tests par Fonctionnalité

### Database Tests (18 tests)

- ✅ Initialisation BDD
- ✅ CRUD clients
- ✅ CRUD claims
- ✅ CRUD disputes
- ✅ Paiements
- ✅ Notifications
- ✅ Statistiques

```bash
pytest tests/test_database.py -v
```

### Email Tests (11 tests)

- ✅ Templates HTML
- ✅ Envoi SMTP (mock)
- ✅ Disputes detected
- ✅ Claim submitted
- ✅ Claim accepted
- ✅ Claim rejected

```bash
pytest tests/test_email_notifications.py -v
```

### E2E Workflow Tests (4 tests)

- ✅ Onboarding complet
- ✅ Soumission réclamation
- ✅ Traitement paiement
- ✅ Worker sync

```bash
pytest tests/test_e2e_workflows.py -v
```

### Payment Tests

- ✅ Paiements manuels
- ✅ Calcul 80/20
- ✅ Stripe integration (mock)
- ✅ Multi-claims

```bash
pytest tests/test_payment_processing.py -v
```

### Security Tests

- ✅ Bcrypt hashing
- ✅ Fernet encryption
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ Input validation
- ✅ Access control

```bash
pytest tests/test_security.py -v
```

## Tests Async

Les tests async utilisent `pytest-asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

## Fixtures Disponibles

### Base de Données

- `temp_db` - Base SQLite temporaire
- `db_manager` - Instance DatabaseManager
- `sample_client` - Client de test
- `sample_claim` - Réclamation de test
- `sample_disputes` - Liste de disputes

### Email

- `mock_smtp_server` - Serveur SMTP mocké
- `mock_env_vars` - Variables d'environnement mockées

### Données

- `sample_orders` - Commandes de test
- `sample_dispute_data` - Données dispute
- `sample_credentials` - Credentials plateformes

## Bonnes Pratiques

### 1. Isoler les Tests

Chaque test doit être indépendant et ne pas dépendre de l'ordre d'exécution.

### 2. Utiliser les Fixtures

```python
def test_with_fixtures(db_manager, sample_client):
    # Données déjà créées automatiquement
    assert sample_client is not None
```

### 3. Tests Async

```python
@pytest.mark.asyncio
async def test_async():
    result = await async_function()
    assert result
```

### 4. Marquer les Tests

```python
@pytest.mark.slow
def test_long_running():
    # Test qui prend du temps
    pass

@pytest.mark.e2e
def test_complete_flow():
    # Test end-to-end
    pass
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov pytest-asyncio

Note: The test suite includes PDF compliance checks that require `PyPDF2` for robust text extraction. The project's CI explicitly installs `PyPDF2>=3.0.0` to ensure PDF parsing works reliably during GitHub Actions runs.      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Statistiques de Couverture Attendues

| Module | Couverture Cible |
| :--- | :--- |
| database_manager.py | 90%+ |
| email_sender.py | 85%+ |
| orchestrator.py | 75%+ |
| order_sync_worker.py | 80%+ |
| Overall | 80%+ |

## Troubleshooting

### Tests Échouent avec "Module not found"

```bash
# Vérifier PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Tests Async Ne Marchent Pas

```bash
# Installer pytest-asyncio
pip install pytest-asyncio
```

### Couverture Incomplète

```bash
# Vérifier les fichiers omis dans pytest.ini
pytest --cov=src --cov-report=term-missing
```

## Prochaines Étapes

- [ ] Ajouter tests pour connecteurs e-commerce
- [ ] Ajouter tests pour Antigravity skills
- [ ] Augmenter couverture à 90%+
- [ ] Ajouter tests de performance
- [ ] Configurer CI/CD
