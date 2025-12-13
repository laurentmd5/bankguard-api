import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Métrique custom pour le taux d'erreur
const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Montée en charge
    { duration: '1m', target: 50 },    // Charge normale
    { duration: '30s', target: 100 },  // Pic de charge
    { duration: '30s', target: 0 },    // Descente
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% des requêtes < 500ms
    errors: ['rate<0.05'],             // Moins de 5% d'erreurs
  },
};

export default function() {
  const res = http.get('http://bankguard.local/balance/123');
  
  const checkRes = check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  errorRate.add(!checkRes);
  sleep(1);
}
