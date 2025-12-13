# terraform/main.tf
# SEULEMENT l'infrastructure de BASE (non gérée par GitOps)

# 1. Storage Class pour Minikube (infra de base)
resource "kubernetes_storage_class" "local_storage" {
  metadata {
    name = "local-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }
  
  storage_provisioner = "kubernetes.io/no-provisioner"
  reclaim_policy      = "Retain"
  volume_binding_mode = "WaitForFirstConsumer"
}

# 2. Rien d'autre - GitOps gère le reste
