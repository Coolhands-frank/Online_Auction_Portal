import json, requests
from urllib.parse import urlencode
from flask import Flask, render_template, url_for, request, redirect, flash, session, abort
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
from datetime import datetime
from flask_migrate import Migrate 
import datetime as dt
import math
from models import *

app = Flask(__name__)
app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:coolhands@localhost:5432/testauction'
bcrypt = Bcrypt(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db.init_app(app)
migrate = Migrate(app, db)
DEBUG = True

cors = CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response

@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('user'):
        return redirect(url_for('signin'))

    if request.method == 'POST':
        search_term = request.form['searchbar']

        if search_term: 
            products = Product.query.filter(Product.name.ilike('%{}%'.format(search_term))).all()
    else:
        products = Product.query.filter_by(live=True).all()

    if not products:
        return render_template('no_listing.html')

    for product in products:
        if product.end_date < datetime.now():
            product.live = False
            product.winner = product.bid_by
            db.session.commit()

        time_left = product.end_date - datetime.now()
        time = math.ceil(time_left / dt.timedelta(hours=1))
        product = product.__dict__
        product['time_left'] = time

    return render_template('home.html', products=products)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                session["user"] = user.email
                return redirect(url_for('home'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Password does not match')
            return redirect(url_for('signup'))

        if len(password) < 8:
            flash('Password must be at least 8 characters')
            return redirect(url_for('signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(name=name, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        session["user"] = user.email
        return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/listings', methods=['GET', 'POST'])
def create_listing():
    if not session.get('user'):
        return redirect(url_for('signin'))
    if request.method == 'POST':
        # Get the data from the form
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        image = request.form['image']
        seller = session.get('user')
        live = True
        price = request.form['price']
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        # Create a new product
        new_product = Product(name=name, description=description, image=image, category=category, start_date=start_date_obj, end_date=end_date_obj, live=live, price=price, owner=seller)
        # Add the product to the database
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully', 'success')
        return redirect(url_for('home'))
    return render_template('add_product.html')

@app.route('/bids')
def my_bid():
    if not session.get('user'):
        return redirect(url_for('signin'))
    products = Product.query.filter_by(bid_by=session.get('user')).all()
    if not products:
        return render_template('no_bid.html')
    return render_template('my_bidding.html', products=products)

@app.route('/profile')
def profile():
    if not session.get('user'):
        return redirect(url_for('signin'))
    user = User.query.filter_by(email=session.get('user')).first()
    products = Product.query.filter_by(owner=session.get('user')).all()
    return render_template('profile.html', user=user, products=products)

@app.route('/product/<int:id>', methods=['GET', 'POST'])
def product(id):
    if not session.get('user'):
        return redirect(url_for('signin'))
    product = Product.query.filter_by(id=id).first()
    if request.method == 'POST':
        bid = request.form['bid']
        bid = float(bid)

        if session.get('user') == product.owner:
            flash('You cannot bid on your own product')
            return redirect(url_for('product', id=id))

        if session.get('user') == product.winner:
            flash('Auction ended')
            return redirect(url_for('product', id=id))

        if bid < product.price:
            flash('Bid must be greater than current price')
            return redirect(url_for('product', id=id))
        else:
            product.price = bid
            product.bid_by = session.get('user')
            db.session.commit()
            flash('Bid placed successfully', 'success')
            return redirect(url_for('home'))

    if session.get('user') == product.owner:
        return render_template('product.html', product=product, owner=True)

    if product.end_date < datetime.now():
        return render_template('product.html', product=product, auction_ended=True)    

    return render_template('product.html', product=product, owner=False, auction_ended=False)

@app.route('/update', methods=['GET', 'POST'])
def update():
    if not session.get('user'):
        return redirect(url_for('signin'))
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        user = User.query.filter_by(email=session.get('user')).update(dict(name=name, phone=phone, address=address))
        db.session.commit()
        return redirect(url_for('profile'))

@app.route('/product/delete/<int:id>', methods=['GET', 'DELETE', 'POST'])
#@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(id):
    if not session.get('user'):
        return redirect(url_for('signin'))
    product = Product.query.filter_by(id=id).first()
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('profile'))

# order
@app.route('/order/<int:id>', methods=['POST'])
def order(id):
    product = Product.query.filter_by(id=id).first()

    auth_headers ={
        "Authorization": "Bearer sk_test_ff01cd2ca009f62609bbbc79087cbb06eb92fdaa",
        "Content-Type": "application/json"
    }
    order_price = product.price
    auth_data = { "email": "{}".format(product.winner), "amount": "{}".format(order_price) }
    auth_data = json.dumps(auth_data)
    req = requests.post('https://api.paystack.co/transaction/initialize', headers=auth_headers, data=auth_data)
    response_data = json.loads(req.text)
    paystack_uri = response_data['data']['authorization_url']
    return redirect(paystack_uri)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)