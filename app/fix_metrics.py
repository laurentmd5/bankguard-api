import sys

# Lire le fichier app.py
with open('app.py', 'r') as f:
    content = f.read()

# Remplacer la fonction metrics_endpoint
old_code = '''@app.route('/metrics', methods=['GET'])
@metrics.do_not_track()
def metrics_endpoint():
    """Endpoint pour Prometheus (géré automatiquement par prometheus-flask-exporter)"""
    return metrics.export()'''

new_code = '''@app.route('/metrics', methods=['GET'])
@metrics.do_not_track()
def metrics_endpoint():
    """Endpoint pour Prometheus"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}'''

# Faire le remplacement
if old_code in content:
    content = content.replace(old_code, new_code)
    with open('app.py', 'w') as f:
        f.write(content)
    print("✅ Correction appliquée")
else:
    print("❌ Code non trouvé, vérifier manuellement")
