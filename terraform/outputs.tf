output "storage_class" {
  value = kubernetes_storage_class.local_storage.metadata[0].name
  description = "StorageClass pour Minikube"
}
