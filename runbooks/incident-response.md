# Runbook: Réponse aux incidents BankGuard

## Détection
1. Alertes Prometheus (HighErrorRate, HighLatency, PodCrashLoop)
2. Dashboards Grafana (Golden Signals)
3. Logs d'application

## Classification
- **SEV-1**: Service complètement inaccessible
- **SEV-2**: Performances dégradées (> 10% d'erreurs)
- **SEV-3**: Problème mineur, service fonctionnel

## Actions immédiates
1. Identifier le scope de l'incident
2. Consulter les dashboards Grafana
3. Vérifier l'état des pods: `kubectl get pods -n bankguard-prod`
4. Examiner les logs: `kubectl logs -f <pod-name> -n bankguard-prod`

## Escalation
- SEV-1: Contact immédiat de l'équipe on-call
- SEV-2: Résolution dans les 2 heures
- SEV-3: Résolution dans les 24 heures
