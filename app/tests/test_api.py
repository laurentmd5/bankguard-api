import unittest
import json
from app import app

class TestBankGuardAPI(unittest.TestCase):
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_endpoint(self):
        """Test du endpoint /health"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('database', data)
        self.assertIn('cache', data)
    
    def test_balance_default_account(self):
        """Test du endpoint /balance sans paramètre"""
        response = self.app.get('/balance')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('account', data)
        self.assertIn('balance', data)
        self.assertIn('currency', data)
        self.assertEqual(data['currency'], 'EUR')
    
    def test_balance_specific_account(self):
        """Test du endpoint /balance avec un compte spécifique"""
        response = self.app.get('/balance/123')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['account'], '123')
        self.assertIsInstance(data['balance'], (int, float))
    
    def test_index_endpoint(self):
        """Test du endpoint racine /"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('service', data)
        self.assertIn('endpoints', data)
        self.assertEqual(data['service'], 'BankGuard API')
    
    def test_metrics_endpoint(self):
        """Test du endpoint /metrics"""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        # Les métriques Prometheus sont en texte brut
        self.assertIn('text/plain', response.content_type)

if __name__ == '__main__':
    unittest.main()
