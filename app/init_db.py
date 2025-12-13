#!/usr/bin/env python3
"""
Script d'initialisation de la base de données
À exécuter manuellement ou comme initContainer dans Kubernetes
"""
import os
import sys
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialise la base de données avec la table et des données de test"""
    
    # Récupérer les paramètres de connexion
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'bankdb')
    db_user = os.getenv('DB_USER', 'bankguard')
    db_password = os.getenv('DB_PASSWORD', '')
    
    logger.info(f"Initialisation DB: {db_user}@{db_host}:{db_port}/{db_name}")
    
    try:
        # Connexion à la DB template pour créer la base si elle n'existe pas
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database='postgres',  # Se connecter à la DB template
            user=db_user,
            password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Vérifier si la base existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cursor.fetchone():
            logger.info(f"Création de la base de données: {db_name}")
            cursor.execute(f"CREATE DATABASE {db_name}")
        else:
            logger.info(f"Base de données {db_name} existe déjà")
        
        cursor.close()
        conn.close()
        
        # Maintenant se connecter à la nouvelle base
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        
        # Créer la table accounts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id VARCHAR(50) PRIMARY KEY,
                balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                currency VARCHAR(3) DEFAULT 'EUR',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Créer un trigger pour updated_at
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_accounts_updated_at ON accounts
        """)
        
        cursor.execute("""
            CREATE TRIGGER update_accounts_updated_at
            BEFORE UPDATE ON accounts
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        """)
        
        # Insérer des données de test
        test_accounts = [
            ('123', 1000.00, 'EUR'),
            ('456', 2500.50, 'EUR'),
            ('789', 500.75, 'EUR'),
            ('corp-001', 100000.00, 'EUR'),
            ('savings-123', 5000.00, 'EUR')
        ]
        
        for account_id, balance, currency in test_accounts:
            cursor.execute("""
                INSERT INTO accounts (account_id, balance, currency)
                VALUES (%s, %s, %s)
                ON CONFLICT (account_id) 
                DO UPDATE SET 
                    balance = EXCLUDED.balance,
                    currency = EXCLUDED.currency
            """, (account_id, balance, currency))
        
        conn.commit()
        
        # Vérifier les données insérées
        cursor.execute("SELECT COUNT(*) FROM accounts")
        count = cursor.fetchone()[0]
        logger.info(f"{count} comptes créés/mis à jour")
        
        cursor.execute("SELECT account_id, balance FROM accounts LIMIT 5")
        logger.info("Données de test:")
        for row in cursor.fetchall():
            logger.info(f"  - {row[0]}: {row[1]} EUR")
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Base de données initialisée avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_database()
