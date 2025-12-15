"""
BankGuard API - Microservice bancaire
Routes: /balance, /health, /metrics
Avec cache Redis et base PostgreSQL
"""
import os
import logging
from flask import Flask, jsonify, request
import psycopg2
import redis
from prometheus_flask_exporter import PrometheusMetrics
from datetime import datetime

# Initialisation Flask
app = Flask(__name__)
metrics = PrometheusMetrics(app, group_by='endpoint')

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variables d'environnement avec valeurs par défaut
DB_HOST = os.getenv('DB_HOST', 'postgres-service')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'bankdb')
DB_USER = os.getenv('DB_USER', 'bankguard')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# Variables globales pour connexions persistantes (optionnel)
_db_pool = None
_redis_client = None

def init_db_pool():
    """Initialise un pool de connexions PostgreSQL"""
    global _db_pool
    # Pour simplicité, on garde la connexion simple
    # En production, utiliser psycopg2.pool.SimpleConnectionPool
    pass

def get_db_connection():
    """Établit une connexion PostgreSQL avec gestion d'erreur"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3  # ← RÉDUIT de 10 à 3 secondes
        )
        logger.debug(f"Connexion DB réussie à {DB_HOST}:{DB_PORT}")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Erreur connexion DB: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue DB: {e}")
        return None

def get_redis_client():
    """Établit une connexion Redis avec gestion d'erreur"""
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True,
            socket_connect_timeout=2,  # ← RÉDUIT de 5 à 2 secondes
            socket_timeout=2
        )
        # Test de connexion rapide
        client.ping()
        logger.debug(f"Connexion Redis réussie à {REDIS_HOST}:{REDIS_PORT}")
        return client
    except redis.ConnectionError as e:
        logger.error(f"Erreur connexion Redis: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue Redis: {e}")
        return None

@app.route('/health/live', methods=['GET'])
@metrics.do_not_track()
def liveness_check():
    """
    Liveness probe pour Kubernetes - RAPIDE (<1s)
    Vérifie seulement que l'application tourne
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'bankguard-api',
        'check': 'liveness',
        'response_time_ms': 0
    }), 200

@app.route('/health/ready', methods=['GET'])
@metrics.do_not_track()
def readiness_check():
    """
    Readiness probe pour Kubernetes - COMPLET
    Vérifie tous les services dépendants
    """
    start_time = datetime.utcnow()
    
    health_data = {
        'status': 'healthy',
        'timestamp': start_time.isoformat(),
        'service': 'bankguard-api',
        'check': 'readiness'
    }
    
    # Vérifier PostgreSQL (avec timeout court)
    db_start = datetime.utcnow()
    db_conn = get_db_connection()
    if db_conn:
        health_data['database'] = {
            'status': 'connected',
            'host': DB_HOST,
            'port': DB_PORT,
            'connection_time_ms': int((datetime.utcnow() - db_start).total_seconds() * 1000)
        }
        db_conn.close()
    else:
        health_data['database'] = {'status': 'disconnected'}
        health_data['status'] = 'degraded'
    
    # Vérifier Redis (avec timeout court)
    redis_start = datetime.utcnow()
    redis_client = get_redis_client()
    if redis_client:
        health_data['cache'] = {
            'status': 'connected',
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'connection_time_ms': int((datetime.utcnow() - redis_start).total_seconds() * 1000)
        }
        redis_client.close()
    else:
        health_data['cache'] = {'status': 'disconnected'}
        health_data['status'] = 'degraded'
    
    # Temps total de réponse
    total_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    health_data['response_time_ms'] = total_time_ms
    
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return jsonify(health_data), status_code

# Alias pour compatibilité
@app.route('/health', methods=['GET'])
@metrics.do_not_track()
def health_check():
    """Alias vers /health/ready pour compatibilité"""
    return readiness_check()

# ... (le reste de ton code reste inchangé - balance, metrics, index)

if __name__ == '__main__':
    # Variables pour le développement local
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.getenv('PORT', '5000'))
    
    logger.info(f"Démarrage BankGuard API sur le port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )
