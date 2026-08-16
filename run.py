"""Application entry point."""
import os
from cybertek import create_app

# Get environment from environment variable, default to production
env = os.getenv('FLASK_ENV', 'production')

# Create application
app = create_app(env)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
