
Runbook: Rollback de déploiement
Quand effectuer un rollback?
Taux d'erreurs > 10% après un déploiement

Régressions de performance significatives

Bugs critiques découverts en production

Méthode 1: Via Git (Recommandé pour GitOps)
bash
# Revenir à la version précédente
git revert HEAD
git push origin main

# ArgoCD synchronisera automatiquement
Méthode 2: Manuel (Urgence uniquement)
bash
# Identifier la version précédente
kubectl rollout history deployment/bankguard-api -n bankguard-prod

# Rollback
kubectl rollout undo deployment/bankguard-api -n bankguard-prod

# Vérifier
kubectl rollout status deployment/bankguard-api -n bankguard-prod
Vérification post-rollback
Vérifier les métriques dans Grafana

Confirmer la résolution des erreurs

Notifier l'équipe de développement
