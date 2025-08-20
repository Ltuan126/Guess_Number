#!/usr/bin/env python3
"""
Script khởi động Guess Number Game Server
Hỗ trợ các options: development, production, testing
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_environment(env_type):
    """Thiết lập môi trường"""
    if env_type == 'development':
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = 'True'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    elif env_type == 'production':
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_DEBUG'] = 'False'
        os.environ['LOG_LEVEL'] = 'WARNING'
    elif env_type == 'testing':
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['FLASK_DEBUG'] = 'False'
        os.environ['LOG_LEVEL'] = 'INFO'
    
    # Thiết lập SECRET_KEY nếu chưa có
    if 'SECRET_KEY' not in os.environ:
        os.environ['SECRET_KEY'] = 'dev_secret_key_change_in_production'

def setup_logging(env_type):
    """Thiết lập logging"""
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    log_file = os.environ.get('LOG_FILE', 'game_server.log')
    
    # Tạo thư mục logs nếu chưa có
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file_path = log_dir / log_file
    
    # Cấu hình logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {env_type} environment")
    logger.info(f"Log file: {log_file_path}")
    
    return logger

def check_dependencies():
    """Kiểm tra dependencies"""
    required_packages = [
        'flask',
        'flask_socketio',
        'flask_cors',
        'eventlet'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'eventlet':
                import eventlet
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    return True

def start_server(env_type, host, port, workers):
    """Khởi động server"""
    try:
        # Thiết lập môi trường
        setup_environment(env_type)
        
        # Thiết lập logging
        logger = setup_logging(env_type)
        
        # Kiểm tra dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Import server sau khi đã thiết lập môi trường
        try:
            from server import app, socketio, GAME_CONFIG
        except ImportError as e:
            logger.error(f"Failed to import server: {e}")
            print(f"❌ Import error: {e}")
            print("Make sure you're running from the correct directory")
            sys.exit(1)
        
        logger.info("🚀 Starting Guess Number Game Server...")
        logger.info(f"Environment: {env_type}")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Game config: {GAME_CONFIG}")
        
        if env_type == 'production':
            # Production mode với multiple workers
            logger.info(f"Production mode with {workers} workers")
            socketio.run(
                app,
                host=host,
                port=port,
                debug=False,
                use_reloader=False,
                log_output=True
            )
        else:
            # Development/Testing mode
            logger.info("Development mode with auto-reload")
            socketio.run(
                app,
                host=host,
                port=port,
                debug=True,
                use_reloader=True,
                log_output=True
            )
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Guess Number Game Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Development mode
  python start_server.py --env development
  
  # Production mode
  python start_server.py --env production --host 0.0.0.0 --port 5000 --workers 4
  
  # Testing mode
  python start_server.py --env testing --port 5001
        """
    )
    
    parser.add_argument(
        '--env', '-e',
        choices=['development', 'production', 'testing'],
        default='development',
        help='Environment type (default: development)'
    )
    
    parser.add_argument(
        '--host', '-H',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=1,
        help='Number of workers for production mode (default: 1)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Guess Number Game Server v2.0.0'
    )
    
    args = parser.parse_args()
    
    # Validation
    if args.env == 'production' and args.workers < 1:
        print("❌ Production mode requires at least 1 worker")
        sys.exit(1)
    
    if args.port < 1 or args.port > 65535:
        print("❌ Port must be between 1 and 65535")
        sys.exit(1)
    
    # Khởi động server
    start_server(args.env, args.host, args.port, args.workers)

if __name__ == '__main__':
    main()
