import os
import requests
import time
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

BACKEND_REQUEST_COUNT = Counter(
    'backend_requests_total',
    'Total backend requests',
    ['status_code', 'backend_url']
)

BACKEND_REQUEST_DURATION = Histogram(
    'backend_request_duration_seconds',
    'Backend request duration in seconds',
    ['backend_url']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

ERROR_COUNT = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Middleware for request metrics
@app.before_request
def before_request():
    request.start_time = time.time()
    ACTIVE_CONNECTIONS.inc()

@app.after_request
def after_request(response):
    request_duration = time.time() - request.start_time
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status_code=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown'
    ).observe(request_duration)
    
    ACTIVE_CONNECTIONS.dec()
    
    return response

@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Prometheus metrics endpoint
    """
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({'status': 'healthy', 'service': 'simple-rest-python', 'version': '1.0'}), 200

@app.route('/api', methods=['GET'])
def api_proxy():
    """
    Proxy endpoint that forwards GET requests to backend API
    """
    backend_url = None
    try:
        # Get backend URL from environment variable
        backend_url = os.getenv('BACKEND')
        
        if not backend_url:
            ERROR_COUNT.labels(error_type='config_error', endpoint='api').inc()
            logger.error("BACKEND environment variable not set")
            return jsonify({'error': 'Backend URL not configured'}), 500
        
        logger.info(f"Forwarding request to: {backend_url}")
        
        # Forward query parameters if any
        params = request.args.to_dict()
        
        # Time the backend request
        backend_start_time = time.time()
        
        # Make GET request to backend API
        response = requests.get(
            backend_url,
            params=params,
            timeout=30,  # 30 second timeout
            headers={'User-Agent': 'API-Proxy-Service/1.0'}
        )
        
        # Record backend metrics
        backend_duration = time.time() - backend_start_time
        BACKEND_REQUEST_DURATION.labels(backend_url=backend_url).observe(backend_duration)
        BACKEND_REQUEST_COUNT.labels(
            status_code=response.status_code,
            backend_url=backend_url
        ).inc()
        
        # Check if request was successful
        response.raise_for_status()
        
        # Return the response data
        try:
            return jsonify(response.json()), response.status_code
        except ValueError:
            # If response is not JSON, return as text
            return response.text, response.status_code
            
    except requests.exceptions.Timeout:
        ERROR_COUNT.labels(error_type='timeout', endpoint='api').inc()
        if backend_url:
            BACKEND_REQUEST_COUNT.labels(status_code='timeout', backend_url=backend_url).inc()
        logger.error("Request to backend timed out")
        return jsonify({'error': 'Backend request timed out'}), 504
        
    except requests.exceptions.ConnectionError:
        ERROR_COUNT.labels(error_type='connection_error', endpoint='api').inc()
        if backend_url:
            BACKEND_REQUEST_COUNT.labels(status_code='connection_error', backend_url=backend_url).inc()
        logger.error("Could not connect to backend")
        return jsonify({'error': 'Could not connect to backend'}), 502
        
    except requests.exceptions.HTTPError as e:
        ERROR_COUNT.labels(error_type='http_error', endpoint='api').inc()
        if backend_url:
            BACKEND_REQUEST_COUNT.labels(status_code=e.response.status_code, backend_url=backend_url).inc()
        logger.error(f"Backend returned HTTP error: {e}")
        return jsonify({'error': f'Backend error: {e.response.status_code}'}), e.response.status_code
        
    except Exception as e:
        ERROR_COUNT.labels(error_type='unknown', endpoint='api').inc()
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/', methods=['GET'])
def root():
    """
    Root endpoint with API information
    """
    return jsonify({
        'service': 'simple-rest-python',
        'version': '1.0',
        'endpoints': {
            '/api': 'Proxy endpoint - forwards to backend API',
            '/health': 'Health check endpoint',
            '/metrics': 'Prometheus metrics endpoint'
        }
    })

if __name__ == '__main__':
    # Check if BACKEND environment variable is set
    backend_url = os.getenv('BACKEND')
    if not backend_url:
        logger.warning("BACKEND environment variable not set. Set it before starting the service.")
    else:
        logger.info(f"Backend URL configured: {backend_url}")
    
    # Print available routes for debugging
    logger.info("Available routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"  {rule.rule} -> {rule.endpoint}")
    
    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)