terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      managed-by  = "terraform"
      environment = "dev"
    }
  }
}

resource "kubernetes_config_map" "monitor_config" {
  metadata {
    name      = "monitor-config"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
  }
  data = {
    URLS_TO_MONITOR = "https://google.com,https://github.com,https://python.org"
    CHECK_INTERVAL  = "30"
  }
}
