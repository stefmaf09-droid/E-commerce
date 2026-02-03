# 🚀 Guide de Déploiement Production

## Vue d'Ensemble

Ce guide couvre 3 options de déploiement :

1. **Docker Compose** (local/serveur dédié)
2. **Heroku** (PaaS simple)
3. **AWS ECS** (production scalable)

---

## Option 1 : Docker Compose (Recommandé pour Démo)

### Prérequis Option 1

```bash
# Docker & Docker Compose installés
docker --version  # >= 20.10
docker-compose --version  # >= 1.29
```

### Configuration Environnement

```bash
# 1. Copier template environnement
cp .env.example .env

# 2. Éditer .env
nano .env
```

```env
# .env
DATABASE_URL=postgresql://recours_user:recours_pass@db:5432/recours_db
REDIS_URL=redis://redis:6379/0
SENTRY_DSN=https://your@sentry.io/project
OPENAI_API_KEY=sk-your-openai-key
ANTIGRAVITY_URL=http://antigravity:8080
CAPTCHA_API_KEY=your-2captcha-key
ENVIRONMENT=production
SECRET_KEY=generate-with-openssl-rand-hex-32
```

### Déploiement

```bash
# 1. Build images
docker-compose build

# 2. Lancer services
docker-compose up -d

# 3. Vérifier statut
docker-compose ps
docker-compose logs web

# 4. Run migrations
docker-compose exec web python scripts/migrate.py
```

### URLs Option 1

- Marketing Dashboard: <http://localhost:8501>
- Client Dashboard: <http://localhost:8503>
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Arrêt & Cleanup

```bash
docker-compose down
docker-compose down -v  # Supprime aussi les volumes (données)
```

---

## Option 2 : Heroku

### Prérequis Option 2

```bash
# Heroku CLI installé
heroku login
```

### Étape 1 : Créer App

```bash
# Créer application
heroku create agent-ia-recouvrement

# Ou utiliser existante
heroku git:remote -a agent-ia-recouvrement
```

### Étape 2 : Add-ons

```bash
# PostgreSQL (mini = gratuit 10k rows)
heroku addons:create heroku-postgresql:mini

# Redis (mini = gratuit 25MB)
heroku addons:create heroku-redis:mini

# Sentry (f1 = gratuit 5k events)
heroku addons:create sentry:f1
```

### Étape 3 : Config Vars

```bash
# Générer secret key
SECRET_KEY=$(openssl rand -hex 32)

# Set variables
heroku config:set ENVIRONMENT=production
heroku config:set SECRET_KEY=$SECRET_KEY
heroku config:set OPENAI_API_KEY=sk-your-key
heroku config:set CAPTCHA_API_KEY=your-2captcha-key
heroku config:set ANTIGRAVITY_URL=https://your-antigravity-service.com

# Heroku définit DATABASE_URL et REDIS_URL automatiquement
```

### Étape 4 : Deploy

```bash
# Push code
git push heroku main

# Run migrations
heroku run python scripts/migrate.py

# Scale processes
heroku ps:scale web=1 worker=1 client=1
```

### Étape 5 : Monitoring

```bash
# Logs temps réel
heroku logs --tail

# Status
heroku ps

# Redémarrer
heroku restart
```

### URLs Option 2

```bash
heroku open  # Ouvre marketing dashboard
heroku open -a agent-ia-recouvrement  # Ou URL explicite
```

Client dashboard: `https://your-app.herokuapp.com:8503` (nécessite configuration)

### Coûts Heroku

| Ressource | Plan | Coût/mois |
| :--- | :--- | :--- |
| Dyno web | Hobby | $7 |
| Dyno worker | Hobby | $7 |
| PostgreSQL | Mini | Gratuit |
| Redis | Mini | Gratuit |
| Sentry | F1 | Gratuit |
| **Total** | | **~$14/mois** |

---

## Option 3 : AWS ECS (Production Scalable)

### Architecture

```text
ALB (Load Balancer)
    │
    ├─ ECS Service (Web) - Port 8501
    ├─ ECS Service (Client) - Port 8503
    └─ ECS Service (Worker)
    
RDS PostgreSQL
ElastiCache Redis
CloudWatch Logs (monitoring)
```

### Étape 1 : ECR (Container Registry)

```bash
# Créer repository
aws ecr create-repository --repository-name agent-ia-recouvrement

# Login
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com

# Build & Push
docker build -t agent-ia-recouvrement .
docker tag agent-ia-recouvrement:latest YOUR_ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/agent-ia-recouvrement:latest
docker push YOUR_ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/agent-ia-recouvrement:latest
```

### Étape 2 : RDS PostgreSQL

```bash
aws rds create-db-instance \
  --db-instance-identifier agent-ia-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username adminuser \
  --master-user-password YourSecurePassword123 \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name your-subnet-group \
  --backup-retention-period 7 \
  --publicly-accessible false
```

### Étape 3 : ElastiCache Redis

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id agent-ia-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxxxx \
  --cache-subnet-group-name your-subnet-group
```

### Étape 4 : ECS Task Definition

### Task Definition JSON

Créer `ecs-task-definition.json` :

```json
{
  "family": "agent-ia-recouvrement",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "web",
      "image": "YOUR_ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/agent-ia-recouvrement:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:db-url"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agent-ia",
          "awslogs-region": "eu-west-1",
          "awslogs-stream-prefix": "web"
        }
      }
    }
  ]
}
```

Enregistrer :

```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

### Étape 5 : ECS Service

```bash
aws ecs create-service \
  --cluster production \
  --service-name agent-ia-web \
  --task-definition agent-ia-recouvrement:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=web,containerPort=8501"
```

### Coûts AWS (estimation)

| Ressource | Config | Coût/mois |
| :--- | :--- | :--- |
| ECS Fargate | 0.5 vCPU, 1GB x2 | ~$30 |
| RDS PostgreSQL | db.t3.micro | ~$15 |
| ElastiCache | cache.t3.micro | ~$12 |
| ALB | 1 instance | ~$16 |
| CloudWatch Logs | 10GB | ~$5 |
| **Total** | | **~$78/mois** |

---

## Vérifications Post-Déploiement

### Health Checks

```bash
# Basic health
curl https://your-app.com/health

# Readiness
curl https://your-app.com/health/ready

# Database
curl https://your-app.com/health/db
```

### Logs

```bash
# Docker Compose
docker-compose logs -f web

# Heroku
heroku logs --tail

# AWS
aws logs tail /ecs/agent-ia --follow
```

### Metrics Sentry

Vérifier dans Sentry dashboard que les events arrivent.

---

## Scaling

### Horizontal

**Heroku** :

```bash
heroku ps:scale web=3 worker=2
```

**AWS ECS** :

```bash
aws ecs update-service \
  --cluster production \
  --service agent-ia-web \
  --desired-count 5
```

### Vertical

**Heroku** : Upgrade dyno type

```bash
heroku ps:resize web=standard-2x
```

**AWS** : Modifier task definition CPU/memory

---

## Rollback

### Heroku

```bash
# Voir releases
heroku releases

# Rollback
heroku rollback v42
```

### AWS ECS

```bash
# Update service à version précédente
aws ecs update-service \
  --cluster production \
  --service agent-ia-web \
  --task-definition agent-ia-recouvrement:previous_version
```

---

## Troubleshooting

### App ne démarre pas

```bash
# Vérifier logs
docker-compose logs web
heroku logs --tail

# Vérifier env vars
heroku config
docker-compose config

# Tester localement
docker-compose up web
```

### Database connection failed

```bash
# Vérifier DATABASE_URL
echo $DATABASE_URL

# Tester connexion
psql $DATABASE_URL

# Run migrations
python scripts/migrate.py
```

### Out of memory

```bash
# Heroku: upgrade dyno
heroku ps:resize web=standard-2x

# Docker: augmenter memory limit
docker-compose.yml: mem_limit: 2g
```

---

## Checklist Pré-Production

- [ ] `.env` configuré avec vraies clés
- [ ] DATABASE_URL pointe vers PostgreSQL production
- [ ] SENTRY_DSN configuré
- [ ] OPENAI_API_KEY valide
- [ ] Migrations exécutées
- [ ] Health checks 200 OK
- [ ] Logs pas d'erreurs critiques
- [ ] Backup base de données configuré
- [ ] Monitoring Sentry actif
- [ ] SSL/HTTPS activé
- [ ] Domaine configuré (si applicable)

---

**⚠️ IMPORTANT** : Ne jamais commit `.env` avec vraies clés !

Utiliser variables d'environnement ou secrets management (AWS Secrets Manager, Heroku Config Vars).
