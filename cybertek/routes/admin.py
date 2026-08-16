"""Admin routes blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from cybertek.models import db, User, Product, Category, Order, OrderItem
from cybertek.utils.decorators import admin_required
from cybertek.utils.helpers import format_specs_for_db, parse_specs
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard - redirects to products."""
    return redirect(url_for('admin.products'))


@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    """Admin statistics page."""
    user_count = User.query.count()
    product_count = Product.query.count()
    category_count = Category.query.count()
    order_count = Order.query.count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    processing_orders = Order.query.filter_by(status='Processing').count()
    completed_orders = Order.query.filter_by(status='Completed').count()
    cancelled_orders = Order.query.filter_by(status='Cancelled').count()

    # Total revenue from completed orders
    total_revenue = (
        db.session.query(
            db.func.coalesce(db.func.sum(OrderItem.quantity * Product.price), 0.0)
        )
        .select_from(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(Order.status == 'Completed')
        .scalar()
        or 0.0
    )

    return render_template(
        'admin/stats.html',
        metrics={
            'users': user_count,
            'products': product_count,
            'categories': category_count,
            'orders': order_count,
            'orders_pending': pending_orders,
            'orders_processing': processing_orders,
            'orders_completed': completed_orders,
            'orders_cancelled': cancelled_orders,
            'revenue': total_revenue,
        }
    )


# ==================== USER MANAGEMENT ====================

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user."""
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''
        is_admin = True if request.form.get('is_admin') == 'on' else False

        if not username or not email or not password:
            flash('Username, email and password are required', 'error')
            return redirect(url_for('admin.add_user'))
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('admin.add_user'))
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('admin.add_user'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('admin.add_user'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('admin.add_user'))

        u = User(username=username, email=email, is_admin=is_admin)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('User created successfully', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_add.html')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit existing user."""
    u = User.query.get(user_id)
    if not u:
        flash('User not found', 'error')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''
        is_admin_req = True if request.form.get('is_admin') == 'on' else False

        if not username or not email:
            flash('Username and email are required', 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Check uniqueness
        existing = User.query.filter(User.username == username, User.id != u.id).first()
        if existing:
            flash('Username already in use', 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        existing = User.query.filter(User.email == email, User.id != u.id).first()
        if existing:
            flash('Email already in use', 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        if password:
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('admin.edit_user', user_id=user_id))
            if len(password) < 6:
                flash('Password must be at least 6 characters', 'error')
                return redirect(url_for('admin.edit_user', user_id=user_id))
            u.set_password(password)
        
        # Prevent self-demote
        if u.id == current_user.id and not is_admin_req:
            flash("You can't remove your own admin role", 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        u.username = username
        u.email = email
        u.is_admin = is_admin_req
        db.session.commit()
        flash('User updated', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_edit.html', user=u)


@admin_bp.route('/users/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user_page(user_id):
    """Delete user confirmation page."""
    u = User.query.get(user_id)
    if not u:
        flash('User not found', 'error')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        if u.id == current_user.id:
            flash("You can't delete your own account", 'error')
            return redirect(url_for('admin.users'))
        db.session.delete(u)
        db.session.commit()
        flash('User deleted', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_delete.html', user=u)


@admin_bp.route('/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle user admin status."""
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin.users'))
    if user.id == current_user.id:
        flash("You can't change your own admin status", 'error')
        return redirect(url_for('admin.users'))
    user.is_admin = not user.is_admin
    db.session.commit()
    flash('User role updated', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user (direct action)."""
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin.users'))
    if user.id == current_user.id:
        flash("You can't delete your own account", 'error')
        return redirect(url_for('admin.users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted', 'success')
    return redirect(url_for('admin.users'))


# ==================== CATEGORY MANAGEMENT ====================

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """List all categories."""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category_page():
    """Add new category."""
    if request.method == 'POST':
        return add_category()
    return render_template('admin/category_add.html')


@admin_bp.route('/add-category', methods=['POST'])
@login_required
@admin_required
def add_category():
    """Add category (form handler)."""
    name = request.form.get('name', '').strip()
    if not name:
        flash('Category name is required', 'error')
    elif Category.query.filter_by(name=name).first():
        flash('Category already exists', 'error')
    else:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{name}" added successfully', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category_page(category_id):
    """Edit category."""
    c = Category.query.get(category_id)
    if not c:
        flash('Category not found', 'error')
        return redirect(url_for('admin.categories'))
    
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if not name:
            flash('Category name is required', 'error')
            return redirect(url_for('admin.edit_category_page', category_id=category_id))
        existing = Category.query.filter(Category.name == name, Category.id != c.id).first()
        if existing:
            flash('Category name already exists', 'error')
            return redirect(url_for('admin.edit_category_page', category_id=category_id))
        c.name = name
        db.session.commit()
        flash('Category updated', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_edit.html', category=c)


@admin_bp.route('/delete-category/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete category."""
    category = Category.query.get(category_id)
    if category:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully', 'success')
    return redirect(url_for('admin.categories'))


# ==================== PRODUCT MANAGEMENT ====================

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    """List all products."""
    products = Product.query.order_by(Product.created_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/products.html', products=products, categories=categories)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product_page():
    """Add new product."""
    if request.method == 'POST':
        return add_product()
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/product_add.html', categories=categories)


@admin_bp.route('/add-product', methods=['POST'])
@login_required
@admin_required
def add_product():
    """Add product (form handler)."""
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '0').strip()
    category_id = request.form.get('category_id')
    image = request.form.get('image')
    stock = request.form.get('stock', '0')
    specs = request.form.get('specs', '')
    description = request.form.get('description', '')

    if not name or not price or not category_id:
        flash('Name, price, and category are required', 'error')
        return redirect(url_for('admin.products'))

    try:
        price_val = float(price)
        stock_val = int(stock)
    except ValueError:
        flash('Invalid price or stock value', 'error')
        return redirect(url_for('admin.products'))

    cat = Category.query.get(int(category_id))
    if not cat:
        flash('Invalid category', 'error')
        return redirect(url_for('admin.products'))

    specs_json = format_specs_for_db(specs)

    prod = Product(
        name=name,
        price=price_val,
        category_id=cat.id,
        image=image,
        stock=stock_val,
        specs=specs_json,
        description=description
    )
    db.session.add(prod)
    db.session.commit()
    flash('Product added successfully', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product_page(product_id):
    """Edit product."""
    p = Product.query.get(product_id)
    if not p:
        flash('Product not found', 'error')
        return redirect(url_for('admin.products'))
    
    if request.method == 'POST':
        return edit_product(product_id)
    
    categories = Category.query.order_by(Category.name).all()
    specs_str = ''
    try:
        if p.specs:
            specs_list = json.loads(p.specs)
            specs_str = ', '.join(specs_list)
    except Exception:
        specs_str = p.specs or ''
    
    return render_template('admin/product_edit.html', product=p, categories=categories, specs_str=specs_str)


@admin_bp.route('/edit-product/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Edit product (form handler)."""
    p = Product.query.get(product_id)
    if not p:
        flash('Product not found', 'error')
        return redirect(url_for('admin.products'))

    name = request.form.get('name', '').strip()
    price = request.form.get('price', '0').strip()
    category_id = request.form.get('category_id')
    image = request.form.get('image')
    stock = request.form.get('stock', '0')
    specs = request.form.get('specs', '')
    description = request.form.get('description', '')

    if not name or not price or not category_id:
        flash('Name, price, and category are required', 'error')
        return redirect(url_for('admin.products'))

    try:
        p.price = float(price)
        p.stock = int(stock)
    except ValueError:
        flash('Invalid price or stock value', 'error')
        return redirect(url_for('admin.products'))

    cat = Category.query.get(int(category_id))
    if not cat:
        flash('Invalid category', 'error')
        return redirect(url_for('admin.products'))

    p.name = name
    p.category_id = cat.id
    p.image = image
    p.description = description
    p.specs = format_specs_for_db(specs)

    db.session.commit()
    flash('Product updated successfully', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/delete-product/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """Delete product."""
    p = Product.query.get(product_id)
    if not p:
        flash('Product not found', 'error')
        return redirect(url_for('admin.products'))
    db.session.delete(p)
    db.session.commit()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('admin.products'))


# ==================== ORDER MANAGEMENT ====================

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """List all orders."""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@admin_bp.route('/update-order-status/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    """Update order status."""
    order = Order.query.get(order_id)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('admin.orders'))
    status = request.form.get('status', '').strip() or 'Pending'
    order.status = status
    db.session.commit()
    flash('Order status updated', 'success')
    return redirect(url_for('admin.orders'))
