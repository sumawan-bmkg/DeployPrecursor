"""
Healthcheck Service - Monitor service health and system status

Purpose: Provide HTTP endpoint for health monitoring and system status
"""

import psutil
import logging
from datetime import datetime
from flask import Flask, jsonify
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'scalogramv3-v8-healthcheck'
    }), 200


@app.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with system metrics
    
    Returns:
        JSON response with detailed health information
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Process information
        current_process = psutil.Process()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'scalogramv3-v8-healthcheck',
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                }
            },
            'process': {
                'pid': current_process.pid,
                'memory_percent': current_process.memory_percent(),
                'cpu_percent': current_process.cpu_percent(),
                'num_threads': current_process.num_threads(),
                'create_time': current_process.create_time()
            }
        }), 200
    except Exception as e:
        logger.error(f"Error in detailed health check: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500


@app.route('/health/services', methods=['GET'])
def services_health_check():
    """
    Check health of all production services
    
    Returns:
        JSON response with service status
    """
    services = {
        'collector': check_service('collector'),
        'preprocessing': check_service('preprocessing'),
        'inference': check_service('inference'),
        'database': check_database(),
        'scheduler': check_service('scheduler')
    }
    
    overall_status = 'healthy' if all(s['status'] == 'healthy' for s in services.values()) else 'degraded'
    
    return jsonify({
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'services': services
    }), 200 if overall_status == 'healthy' else 503


def check_service(service_name: str) -> dict:
    """
    Check if a service is running
    
    Args:
        service_name: Name of service to check
        
    Returns:
        Dictionary with service status
    """
    # Placeholder - implement actual service checking logic
    # This could check systemd services, process names, or HTTP endpoints
    return {
        'name': service_name,
        'status': 'healthy',  # Placeholder
        'last_check': datetime.now().isoformat()
    }


def check_database() -> dict:
    """
    Check database connectivity
    
    Returns:
        Dictionary with database status
    """
    # Placeholder - implement actual database check
    return {
        'name': 'database',
        'status': 'healthy',  # Placeholder
        'last_check': datetime.now().isoformat()
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Healthcheck Service")
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    
    args = parser.parse_args()
    
    logger.info(f"Starting healthcheck service on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port)
