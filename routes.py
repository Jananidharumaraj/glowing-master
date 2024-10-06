import os
import secrets
from flask import render_template, url_for, flash, redirect, request
from unwrap import app, db, bcrypt
from unwrap.forms import RegistrationForm, LoginForm, UpdateAccountForm, UpdateCartForm
from unwrap.models import User, Products, Cart
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import func


def getLoginDetails():
    """Check if the user is authenticated and get the number of items in the cart."""
    if current_user.is_authenticated:
        noOfItems = Cart.query.filter_by(buyer=current_user).count()
    else:
        noOfItems = 0
    return noOfItems


@app.route("/")
@app.route("/home")
def home():
    noOfItems = getLoginDetails()
    return render_template('home.html', noOfItems=noOfItems)


@app.route("/register", methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(lastname=form.lastname.data, firstname=form.firstname.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('home'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """Handle account update."""
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.lastname = form.lastname.data
        current_user.firstname = form.firstname.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.lastname.data = current_user.lastname
        form.firstname.data = current_user.firstname
        form.email.data = current_user.email
    return render_template('account.html', title='Account', form=form)


@app.route("/unwrap-project")
def unwrap_project():
    noOfItems = getLoginDetails()
    return render_template("unwrap-project.html", title='The project', noOfItems=noOfItems)


@app.route("/how-it-works")
def how_it_works():
    return render_template("how-it-works.html", title='How it works')


@app.route("/select_products", methods=['GET'])
def select_products():
    """Display all available products."""
    products = Products.query.all()  # Fetch all products from the database
    noOfItems = getLoginDetails()
    return render_template('select_products.html', products=products, noOfItems=noOfItems)


@app.route("/select_products/<int:product_id>")
def select_product(product_id):
    """Display the selected product details."""
    product = Products.query.get_or_404(product_id)  # Fetch the product or 404
    noOfItems = getLoginDetails()
    return render_template('selected_product.html', product=product, noOfItems=noOfItems)


@app.route("/addToCart/<int:product_id>", methods=['POST'])
@login_required
def addToCart(product_id):
    """Add an item to the user's cart, increment quantity if already added."""
    try:
        # Check if the product already exists in the user's cart
        cart_item = Cart.query.filter_by(product_id=product_id, buyer=current_user).first()

        if cart_item:
            # Increment the quantity if the product is already in the cart
            cart_item.quantity += 1
            flash('This item is already in your cart, 1 quantity added!', 'success')
        else:
            # Create a new cart item if it doesn't exist
            cart_item = Cart(buyer=current_user, product_id=product_id, quantity=1)
            db.session.add(cart_item)
            flash('Item added to cart!', 'success')

        db.session.commit()  # Commit changes to the database

    except Exception as e:
        db.session.rollback()  # Rollback if any error occurs
        flash('An error occurred while adding the item to your cart!', 'danger')
        print(e)

    return redirect(url_for('cart'))  # Redirect to the cart page


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    """Display the cart and allow quantity updates."""
    noOfItems = getLoginDetails()

    # Create a form for updating quantities (or use an existing form if applicable)
    form = UpdateCartForm()  # Make sure to define UpdateCartForm in your forms module

    # Retrieve items from the cart for the current user
    cart_items = db.session.query(Cart, Products).join(Products).filter(Cart.buyer == current_user).all()

    subtotal = sum(float(item[1].price) * int(item[0].quantity) for item in cart_items)

    if request.method == "POST":
        qty = request.form.get("qty")
        idpd = request.form.get("idpd")

        # Check that the product ID exists before updating
        cart_item = Cart.query.filter_by(product_id=idpd, buyer=current_user).first()
        if cart_item:
            cart_item.quantity = int(qty)
            db.session.commit()
            flash('Cart updated!', 'success')
        else:
            flash('Cart item not found!', 'danger')

    return render_template('cart.html', cart=cart_items, noOfItems=noOfItems, subtotal=subtotal, form=form)


@app.route("/update_cart", methods=["POST"])
@login_required
def update_cart():
    """Update the quantity of a product in the cart."""
    qty = request.form.get("qty")
    idpd = request.form.get("idpd")

    cart_item = Cart.query.filter_by(product_id=idpd, buyer=current_user).first()
    if cart_item:
        cart_item.quantity = int(qty)
        db.session.commit()
        flash('Cart updated!', 'success')
    else:
        flash('Cart item not found!', 'danger')

    return redirect(url_for('cart'))  # Redirect back to the cart page


@app.route("/removeFromCart/<int:product_id>")
@login_required
def removeFromCart(product_id):
    """Remove an item from the cart."""
    item_to_remove = Cart.query.filter_by(product_id=product_id, buyer=current_user).first()
    if item_to_remove:
        db.session.delete(item_to_remove)
        db.session.commit()
        flash('Your item has been removed from your cart!', 'success')
    else:
        flash('Item not found in cart!', 'danger')

    return redirect(url_for('cart'))


# ... [Your existing imports and code above]

@app.route("/checkout")
@login_required
def checkout():
    """Handle the checkout process."""
    noOfItems = getLoginDetails()
    # Logic for handling the checkout (e.g., fetching payment details, delivery options)
    cart_items = db.session.query(Cart, Products).join(Products).filter(Cart.buyer == current_user).all()
    subtotal = sum(float(item[1].price) * int(item[0].quantity) for item in cart_items)
    
    return render_template('checkout.html', cart=cart_items, subtotal=subtotal, noOfItems=noOfItems)

@app.route("/add_sample_products")
def add_sample_products():
    """Add sample products to the database (for testing purposes)."""
    existing_products = Products.query.all()
    if existing_products:
        return "Sample products already exist in the database!"

    # Sample products with associated images
    products = [
        Products(name="Glow Serum", price=29.99, description="A lightweight serum for a radiant glow.", image_url="static/glow_serum.JPG"),
        Products(name="Hydrating Face Mask", price=19.99, description="A nourishing mask that hydrates and revitalizes skin.", image_url="static/hydrating_mask.JPG"),
        Products(name="Moisturizing Cream", price=34.99, description="Deeply moisturizing cream for soft and supple skin.", image_url="static/moisturizing_cream.JPG"),
        Products(name="Lip Gloss Set", price=24.99, description="A set of lip glosses in various shades for a perfect pout.", image_url="static/lip_gloss_set.JPG"),
    ]

    db.session.bulk_save_objects(products)
    db.session.commit()
    return "Sample products added!"

if __name__ == "__main__":
    app.run(debug=True)  # Adjust as needed
