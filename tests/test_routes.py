import os
import sys
import pytest

# Ensure cybertek package is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybertek import create_app
from cybertek.models import db, User


@pytest.fixture
def app():
    """Create and configure a test app."""
    import tempfile
    import os
    
    db_fd, db_path = tempfile.mkstemp()
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    with app.app_context():
        db.create_all()
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com', is_admin=False)
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user


def test_home_route(client):
    """Test home route returns 200."""
    resp = client.get('/')
    assert resp.status_code == 200


def test_signup_get(client):
    """Test GET /signup returns form."""
    resp = client.get('/signup')
    assert resp.status_code == 200


def test_login_get(client):
    """Test GET /login returns form."""
    resp = client.get('/login')
    assert resp.status_code == 200


def test_cart_route(client):
    """Test /cart route returns 200."""
    resp = client.get('/cart')
    assert resp.status_code == 200


def test_product_detail_redirect(client):
    """Test product detail redirects for missing product."""
    resp = client.get('/product/99999')
    # App redirects missing products to home (302 Found)
    assert resp.status_code == 302
