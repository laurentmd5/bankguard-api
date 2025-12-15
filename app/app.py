"""
BankGuard API - Microservice bancaire
Routes: /balance, /health/live, /health/ready, /metrics
Avec cache Redis et base PostgreSQL
Optimisé pour Kubernetes probes
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

# Métriques Prometheus personnalisées
balance_requests = metrics.counter(
    'balance_requests_total',
    'Total balance requests',
    labels={'status': lambda r: r.status_code}
)

cache_hits = metrics.counter(
    'cache_hits_total',
    'Total Redis cache hits'
)

# Variables d'environnement avec valeurs par défaut
DB_HOST = os.getenv('DB_HOST', 'postgres-service')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'bankdb')
DB_USER = os.getenv('DB_USER', 'bankguard')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')


def get_db_connection():
    """Établit une connexion PostgreSQL avec gestion d'erreur"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3  # Réduit pour les probes
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
            socket_connect_timeout=2,  # Réduit pour les probes
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
    Liveness probe pour Kubernetes - TRÈS RAPIDE (<100ms)
    Vérifie seulement que l'application tourne
    Ne fait AUCUNE vérification réseau
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'bankguard-api',
        'check': 'liveness'
    }), 200


@app.route('/health/ready', methods=['GET'])
@metrics.do_not_track()
def readiness_check():
    """
    Readiness probe pour Kubernetes - COMPLET
    Vérifie que tous les services dépendants sont accessibles
    Peut prendre quelques secondes (timeout 15s configuré)
    """
    start_time = datetime.utcnow()
    
    health_data = {
        'status': 'ready',
        'timestamp': start_time.isoformat(),
        'service': 'bankguard-api',
        'check': 'readiness'
    }
    
    # Vérifier PostgreSQL
    db_start = datetime.utcnow()
    db_conn = get_db_connection()
    if db_conn:
        health_data['database'] = {
            'status': 'connected',
            'host': DB_HOST,
            'port': DB_PORT,
            'response_time_ms': int((datetime.utcnow() - db_start).total_seconds() * 1000)
        }
        db_conn.close()
    else:
        health_data['database'] = {'status': 'disconnected'}
        health_data['status'] = 'not_ready'
    
    # Vérifier Redis
    redis_start = datetime.utcnow()
    redis_client = get_redis_client()
    if redis_client:
        health_data['cache'] = {
            'status': 'connected',
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'response_time_ms': int((datetime.utcnow() - redis_start).total_seconds() * 1000)
        }
        redis_client.close()
    else:
        health_data['cache'] = {'status': 'disconnected'}
        health_data['status'] = 'not_ready'
    
    # Temps total
    total_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    health_data['total_response_time_ms'] = total_time_ms
    
    status_code = 200 if health_data['status'] == 'ready' else 503
    return jsonify(health_data), status_code


@app.route('/health', methods=['GET'])
@metrics.do_not_track()
def health_check():
    """Alias vers /health/ready pour compatibilité"""
    return readiness_check()


@app.route('/balance', methods=['GET'])
@app.route('/balance/<account_id>', methods=['GET'])
@balance_requests
def get_balance(account_id=None):
    """
    Retourne le solde d'un compte
    Logique: Redis -> PostgreSQL -> Fallback
    """
    # Utiliser '123' comme compte par défaut si non spécifié
    if account_id is None:
        account_id = request.args.get('account', '123')
    
    logger.info(f"Requête solde pour le compte: {account_id}")
    
    # 1. Essayer Redis d'abord
    redis_client = get_redis_client()
    cache_key = f"balance:{account_id}"
    
    if redis_client:
        try:
            cached_balance = redis_client.get(cache_key)
            if cached_balance is not None:
                cache_hits.inc()
                logger.info(f"Cache hit pour {account_id}")
                return jsonify({
                    'account': account_id,
                    'balance': float(cached_balance),
                    'currency': 'EUR',
                    'source': 'redis_cache',
                    'cache_hit': True,
                    'timestamp': datetime.utcnow().isoformat()
                })
        except Exception as e:
            logger.warning(f"Erreur lecture Redis: {e}")
    
    # 2. Si pas en cache, lire PostgreSQL
    db_conn = get_db_connection()
    if db_conn:
        try:
            cursor = db_conn.cursor()
            cursor.execute("""
                SELECT balance, updated_at 
                FROM accounts 
                WHERE account_id = %s
            """, (account_id,))
            result = cursor.fetchone()
            
            if result:
                balance = result[0]
                updated_at = result[1]
                
                # Mettre en cache Redis (TTL: 5 minutes)
                if redis_client:
                    try:
                        redis_client.setex(cache_key, 300, balance)
                        logger.info(f"Cache mis à jour pour {account_id}")
                    except Exception as e:
                        logger.warning(f"Erreur écriture Redis: {e}")
                
                logger.info(f"Données DB pour {account_id}: {balance} EUR")
                return jsonify({
                    'account': account_id,
                    'balance': float(balance),
                    'currency': 'EUR',
                    'last_updated': updated_at.isoformat() if updated_at else None,
                    'source': 'postgresql',
                    'cache_hit': False,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                # Compte non trouvé
                logger.warning(f"Compte {account_id} non trouvé en DB")
                return jsonify({
                    'account': account_id,
                    'error': 'Account not found',
                    'timestamp': datetime.utcnow().isoformat()
                }), 404
                
        except Exception as e:
            logger.error(f"Erreur requête DB: {e}")
            db_conn.rollback()
        finally:
            cursor.close()
            db_conn.close()
    else:
        logger.warning("Connexion DB échouée, utilisation du fallback")
    
    # 3. Fallback: données fictives
    fallback_balance = 1000.00
    logger.info(f"Fallback pour {account_id}: {fallback_balance} EUR")
    
    return jsonify({
        'account': account_id,
        'balance': fallback_balance,
        'currency': 'EUR',
        'source': 'fallback',
        'warning': 'Database temporarily unavailable',
        'cache_hit': False,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/metrics', methods=['GET'])
@metrics.do_not_track()
def metrics_endpoint():
    """Endpoint pour Prometheus (géré automatiquement par prometheus-flask-exporter)"""
    try:
        return metrics.export()
    except AttributeError:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/', methods=['GET'])
@metrics.do_not_track()
def index():
    """Page d'accueil avec documentation"""
    return jsonify({
        'service': 'BankGuard API',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'Cette page',
            'GET /health/live': 'Liveness probe (rapide)',
            'GET /health/ready': 'Readiness probe (complet)',
            'GET /health': 'Santé complète (alias /health/ready)',
            'GET /balance': 'Solde du compte par défaut (123)',
            'GET /balance/<account_id>': 'Solde d\'un compte spécifique',
            'GET /metrics': 'Métriques Prometheus'
        },
        'timestamp': datetime.utcnow().isoformat()
    })


if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.getenv('PORT', '5000'))
    
    logger.info(f"Démarrage BankGuard API sur le port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )
