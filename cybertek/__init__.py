"""Flask application factory."""
import os
import json
from flask import Flask, flash, redirect, url_for, request
from flask_login import LoginManager
from cybertek.models import db, User, Category, Product
from cybertek.config import config, Config


def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set secret key. Tests use an isolated non-production key.
    app.secret_key = app.config.get("SECRET_KEY") or Config.get_secret_key()
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @login_manager.unauthorized_handler
    def unauthorized():
        flash('Please sign in to continue', 'error')
        return redirect(url_for('auth.login', next=request.path))
    
    # Make categories available to all templates (for navbar)
    @app.context_processor
    def inject_nav_categories():
        try:
            cats = Category.query.order_by(Category.name).all()
        except Exception:
            cats = []
        return {'nav_categories': cats}
    
    # Register blueprints
    from cybertek.routes import auth_bp, shop_bp, admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500
    
    # Initialize database
    with app.app_context():
        init_db(app)
    
    return app


def init_db(app):
    """Initialize database with tables and seed data."""
    db.create_all()
    
    # Create default categories if empty
    if Category.query.count() == 0:
        categories = ['Laptops', 'Audio', 'Wearables', 'Tablets', 'Gaming', 'Displays', 'Accessories', 'Cameras']
        for cat in categories:
            db.session.add(Category(name=cat))
        db.session.commit()
    
    # Seed products from shop blueprint's PRODUCTS list if DB has none
    if Product.query.count() == 0:
        from cybertek.routes.shop import PRODUCTS
        name_to_category = {c.name: c.id for c in Category.query.all()}
        for p in PRODUCTS:
            cat_id = name_to_category.get(p.get('category'))
            if not cat_id:
                # Create missing category on the fly
                c = Category(name=p.get('category', 'Uncategorized'))
                db.session.add(c)
                db.session.flush()
                cat_id = c.id
                name_to_category[c.name] = c.id
            prod = Product(
                id=p.get('id'),
                name=p.get('name'),
                price=p.get('price', 0.0),
                description=p.get('description'),
                image=p.get('image'),
                category_id=cat_id,
                stock=p.get('stock', 0),
                specs=json.dumps(p.get('specs', []))
            )
            db.session.add(prod)
        db.session.commit()

