# Runbook: Récupération de base de données

## Symptômes
- Erreurs de connexion à PostgreSQL
- Timeout sur les requêtes /balance
- Métriques de base de données anormales

## Diagnostic
1. Vérifier l'état du pod PostgreSQL:
   ```bash
   kubectl get pods -n bankguard-prod -l app=postgres
Examiner les logs:

bash
kubectl logs -f <postgres-pod> -n bankguard-prod
Tester la connexion:

bash
kubectl exec -it <api-pod> -n bankguard-prod -- \
  psql -h postgres -U appuser -d bankguard -c "SELECT 1;"
Actions de récupération
1. Redémarrer le pod
bash
kubectl delete pod <postgres-pod> -n bankguard-prod
2. Restaurer depuis backup (si configuré)
bash
kubectl exec -it <postgres-pod> -n bankguard-prod -- \
  pg_restore -h localhost -U appuser -d bankguard /backups/latest.dump
