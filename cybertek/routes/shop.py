"""Shop routes blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from cybertek.models import db, Product, Category, Order, OrderItem
from cybertek.utils.helpers import parse_specs, calculate_cart_total
import json

shop_bp = Blueprint('shop', __name__)

# Sample products for fallback
PRODUCTS = [
    {
        'id': 1,
        'name': 'CyberBook Pro X1',
        'category': 'Laptops',
        'price': 1299.99,
        'image': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&h=500&fit=crop',
        'description': 'Ultra-thin laptop with 16GB RAM, 512GB SSD, and stunning 4K display',
        'specs': ['Intel i7 Processor', '16GB RAM', '512GB SSD', '14-inch 4K Display'],
        'stock': 15
    },
    {
        'id': 2,
        'name': 'Quantum Wireless Headphones',
        'category': 'Audio',
        'price': 249.99,
        'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&h=500&fit=crop',
        'description': 'Premium noise-cancelling headphones with 40-hour battery life',
        'specs': ['Active Noise Cancellation', '40-Hour Battery', 'Bluetooth 5.3', 'Premium Sound'],
        'stock': 28
    },
    {
        'id': 3,
        'name': 'NeoWatch Ultra',
        'category': 'Wearables',
        'price': 399.99,
        'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&h=500&fit=crop',
        'description': 'Advanced smartwatch with health tracking and AMOLED display',
        'specs': ['AMOLED Display', 'Heart Rate Monitor', 'GPS Tracking', 'Water Resistant'],
        'stock': 22
    },
    {
        'id': 4,
        'name': 'TechPad Mini',
        'category': 'Tablets',
        'price': 599.99,
        'image': 'https://images.unsplash.com/photo-1561154464-82e9adf32764?w=500&h=500&fit=crop',
        'description': 'Compact tablet perfect for work and entertainment on the go',
        'specs': ['10.5-inch Display', '128GB Storage', '12MP Camera', 'All-Day Battery'],
        'stock': 18
    },
    {
        'id': 5,
        'name': 'ProGaming Mouse RGB',
        'category': 'Gaming',
        'price': 79.99,
        'image': 'https://images.unsplash.com/photo-1527814050087-3793815479db?w=500&h=500&fit=crop',
        'description': 'High-precision gaming mouse with customizable RGB lighting',
        'specs': ['16000 DPI', 'RGB Lighting', 'Programmable Buttons', 'Ergonomic Design'],
        'stock': 45
    },
    {
        'id': 6,
        'name': 'UltraView 4K Monitor',
        'category': 'Displays',
        'price': 449.99,
        'image': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&h=500&fit=crop',
        'description': '27-inch 4K HDR monitor with stunning color accuracy',
        'specs': ['27-inch 4K', 'HDR Support', '144Hz Refresh', 'USB-C Connectivity'],
        'stock': 12
    },
    {
        'id': 7,
        'name': 'PowerBank Infinite',
        'category': 'Accessories',
        'price': 89.99,
        'image': 'https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=500&h=500&fit=crop',
        'description': '30000mAh portable charger with fast charging technology',
        'specs': ['30000mAh Capacity', 'Fast Charging', 'Multiple Ports', 'LED Display'],
        'stock': 35
    },
    {
        'id': 8,
        'name': 'CyberCam 4K Pro',
        'category': 'Cameras',
        'price': 899.99,
        'image': 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500&h=500&fit=crop',
        'description': 'Professional 4K webcam for streaming and video calls',
        'specs': ['4K Resolution', 'Auto-Focus', 'Low-Light Performance', 'Wide Angle Lens'],
        'stock': 20
    }
]


@shop_bp.route('/')
def home():
    """Home page with product listing."""
    category_filter = request.args.get('category')
    q = (request.args.get('q') or '').strip()
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    items = []
    
    # Prefer DB products; fallback to in-memory PRODUCTS
    if Product.query.count() > 0:
        query = Product.query
        if category_filter:
            cat = Category.query.filter_by(name=category_filter).first()
            if cat:
                query = query.filter_by(category_id=cat.id)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Product.name.ilike(like), Product.description.ilike(like)))
        try:
            if min_price:
                mn = float(min_price)
                query = query.filter(Product.price >= mn)
            if max_price:
                mx = float(max_price)
                query = query.filter(Product.price <= mx)
        except ValueError:
            pass
        for p in query.all():
            items.append({
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'image': p.image,
                'description': (p.description or ''),
                'category': p.category.name if p.category else 'Uncategorized'
            })
    else:
        filtered = PRODUCTS
        if category_filter:
            filtered = [p for p in filtered if p.get('category') == category_filter]
        if q:
            ql = q.lower()
            def match(p):
                return ql in p.get('name', '').lower() or ql in p.get('description', '').lower()
            filtered = [p for p in filtered if match(p)]
        try:
            if min_price:
                mn = float(min_price)
                filtered = [p for p in filtered if p.get('price', 0) >= mn]
            if max_price:
                mx = float(max_price)
                filtered = [p for p in filtered if p.get('price', 0) <= mx]
        except ValueError:
            pass
        items = filtered
    
    return render_template('shop/home.html', products=items, active_category=category_filter, 
                         q=q, min_price=min_price, max_price=max_price)


@shop_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page."""
    prod = Product.query.get(product_id)
    if prod:
        specs_list = parse_specs(prod.specs)
        product = {
            'id': prod.id,
            'name': prod.name,
            'price': prod.price,
            'image': prod.image,
            'description': prod.description,
            'category': prod.category.name if prod.category else 'Uncategorized',
            'specs': specs_list,
            'stock': prod.stock,
        }
    else:
        product = next((p for p in PRODUCTS if p['id'] == product_id), None)
        if product is None:
            return redirect(url_for('shop.home'))
    
    return render_template('shop/product_detail.html', product=product)


@shop_bp.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart."""
    if 'cart' not in session:
        session['cart'] = []
    
    prod = Product.query.get(product_id)
    if prod:
        product = {
            'id': prod.id,
            'name': prod.name,
            'price': prod.price,
            'image': prod.image or '',
        }
    else:
        product = next((p for p in PRODUCTS if p['id'] == product_id), None)

    if product:
        cart = session['cart']
        existing_item = next((item for item in cart if item['id'] == product_id), None)
        
        if existing_item:
            existing_item['quantity'] += 1
        else:
            cart.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image'],
                'quantity': 1
            })
        
        session['cart'] = cart
        session.modified = True
    
    return jsonify({'success': True, 'cart_count': len(session.get('cart', []))})


@shop_bp.route('/cart')
def cart():
    """Shopping cart page."""
    cart_items = session.get('cart', [])
    total = calculate_cart_total(cart_items)
    return render_template('shop/cart.html', cart_items=cart_items, total=total)


@shop_bp.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update cart item quantity."""
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', [])
    
    for item in cart:
        if item['id'] == product_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
            break
    
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('shop.cart'))


@shop_bp.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart."""
    cart = session.get('cart', [])
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('shop.cart'))


@shop_bp.route('/checkout')
@login_required
def checkout():
    """Checkout page."""
    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('shop.cart'))
    total = calculate_cart_total(cart_items)
    return render_template('shop/checkout.html', cart_items=cart_items, total=total)


@shop_bp.route('/process-order', methods=['POST'])
@login_required
def process_order():
    """Process order from cart."""
    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('shop.cart'))

    total = calculate_cart_total(cart_items)
    order = Order(user_id=current_user.id, total=total, status='Completed')
    
    for item in cart_items:
        order_item = OrderItem(
            product_id=item['id'],
            quantity=item['quantity'],
            price=item['price']
        )
        order.items.append(order_item)
    
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Could not place order. Please try again.', 'error')
        return redirect(url_for('shop.checkout'))
    
    session['cart'] = []
    session.modified = True
    
    return render_template('shop/order_success.html', order=order)
