import os
import sys
import pytest

# Ensure cybertek package is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybertek.models import User, Category, Product, Order, OrderItem
from cybertek import create_app


@pytest.fixture
def app():
    """Create and configure a test app."""
    import tempfile
    import os
    
    db_fd, db_path = tempfile.mkstemp()
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's CLI."""
    return app.test_cli_runner()


def test_user_creation(app):
    """Test User model creation and password hashing."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('securepass')
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('securepass')
        assert not user.check_password('wrongpass')


def test_category_creation(app):
    """Test Category model creation."""
    with app.app_context():
        cat = Category(name='Laptops')
        
        assert cat.name == 'Laptops'


def test_product_creation(app):
    """Test Product model creation."""
    with app.app_context():
        prod = Product(
            name='Test Laptop',
            price=999.99,
            description='A test product',
            stock=10
        )
        
        assert prod.name == 'Test Laptop'
        assert prod.price == 999.99
        assert prod.stock == 10


def test_order_creation(app):
    """Test Order model creation."""
    with app.app_context():
        order = Order(user_id=1, total=100.00, status='Completed')
        
        assert order.user_id == 1
        assert order.total == 100.00
        assert order.status == 'Completed'
