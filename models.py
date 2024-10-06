from datetime import datetime
from unwrap import db, login_manager
from flask_login import UserMixin
from flask import flash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(20), unique=False, nullable=False)
    lastname = db.Column(db.String(20), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    # Define relationship with Cart
    cart_items = db.relationship('Cart', backref='buyer', lazy=True)

    def add_to_cart(self, product_id):
        # Check if the item is already in the cart
        existing_item = Cart.query.filter_by(product_id=product_id, user_id=self.id).first()
        if existing_item:
            existing_item.quantity += 1  # Increment quantity
            flash('Quantity updated in your cart!', 'info')
        else:
            new_item = Cart(product_id=product_id, user_id=self.id)
            db.session.add(new_item)
            flash('Your item has been added to your cart!', 'success')
        db.session.commit()

    def __repr__(self):
        return f"User('{self.firstname}', '{self.lastname}', '{self.email}', '{self.id}')"

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Use Float for prices
    image_url = db.Column(db.String(120), nullable=False)  # Check this line

    # Optional: Relationship to Cart
    cart_items = db.relationship('Cart', backref='product', lazy=True)

    def __repr__(self):
        return f"Products('{self.name}', '{self.price}')"

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


    def __repr__(self):
        return f"Cart('Product id: {self.product_id}', 'Cart id: {self.id}', 'User id: {self.user_id}', 'Quantity: {self.quantity}')"
