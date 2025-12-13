.PHONY: help setup deploy test chaos monitor clean

help:
@echo "BankGuard SRE Platform - Commandes disponibles:"
@echo ""
@echo " make setup - Configuration initiale"
@echo " make deploy - Déploiement via Git (ArgoCD)"
@echo " make test - Exécution des tests locaux"
@echo " make chaos - Lancer les tests de chaos"
@echo " make monitor - Ouvrir les dashboards"
@echo " make clean - Nettoyage des ressources"
@echo ""

setup:
@echo "🚀 Configuration initiale de BankGuard..."
@echo "1. Assure-toi d'avoir kubectl configuré"
@echo "2. Vérifie qu'ArgoCD est installé: kubectl get pods -n argocd"
@echo "3. Configure les secrets dans ArgoCD pour DB_PASSWORD"
@echo "✅ Setup terminé"

deploy:
@echo "📦 Pushing changes to Git - ArgoCD déploiera automatiquement..."
git add .
git commit -m "Deploy: $(shell date +'%Y-%m-%d %H:%M')" || true
git push
@echo "✅ Déploiement initié. Vérifie ArgoCD: http://localhost:8080"

test:
@echo "🧪 Exécution des tests..."
cd app && python -m pytest tests/ -v

chaos:
@echo "💥 Lancement du Chaos Monkey..."
@echo "Ouvre un nouveau terminal et exécute:"
@echo " python chaos/chaos-monkey.py"
@echo ""
@echo "Pour les tests de charge avec k6:"
@echo " k6 run chaos/load-test.k6.js"

monitor:
@echo "📊 Ouverture des dashboards de monitoring..."
@echo "Grafana: minikube service grafana -n monitoring --url"
@echo "Prometheus: minikube service prometheus -n monitoring --url"
@echo "ArgoCD: minikube service argocd-server -n argocd --url"

clean:
@echo "🧹 Nettoyage des ressources..."
kubectl delete -f gitops-manifests/ --ignore-not-found=true
@echo "✅ Nettoyage terminé"
