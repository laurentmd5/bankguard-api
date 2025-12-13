#!/usr/bin/env python3
"""
Chaos Monkey pour BankGuard
Supprime aléatoirement un pod toutes les 30 secondes
"""

import kubernetes.client
from kubernetes.client.rest import ApiException
import random
import time
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def delete_random_pod(namespace="bankguard-prod", label_selector="app=bankguard-api"):
    """Supprime un pod aléatoire du déploiement BankGuard"""
    try:
        config = kubernetes.config.load_kube_config()
        v1 = kubernetes.client.CoreV1Api()
        
        pods = v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector
        )
        
        if pods.items:
            pod = random.choice(pods.items)
            pod_name = pod.metadata.name
            
            logger.info(f"🔪 Chaos Monkey targeting pod: {pod_name}")
            
            v1.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace,
                body=kubernetes.client.V1DeleteOptions()
            )
            
            logger.info(f"✅ Pod {pod_name} deleted successfully")
            return True
        else:
            logger.warning("No pods found to delete")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting pod: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Chaos Monkey for BankGuard")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            delete_random_pod()
            logger.info("⏳ Waiting 30 seconds...")
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("👋 Chaos Monkey stopped by user")
        sys.exit(0)
