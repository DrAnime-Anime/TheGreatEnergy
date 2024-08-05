from flask import Flask, render_template, flash, request, redirect, url_for , session
from datetime import datetime 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash 
from datetime import date
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange
from wtforms.widgets import TextArea
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField
from flask_msearch import Search
import uuid as uuid
import os
import json
import secrets
from secrets import token_hex



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SECRET_KEY'] = "my super secret key that no one is supposed to know"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
search = Search()

search.init_app(app)

db.create_all()
db.init_app(app)

# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'Login'

@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))

# Create Model
class Users(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), nullable=False, unique=True)
	name = db.Column(db.String(200), nullable=False)
	email = db.Column(db.String(120), nullable=False, unique=True)
	date_added = db.Column(db.DateTime, default=datetime.utcnow)
	city = db.Column(db.String(50), unique= False)
	contact = db.Column(db.String(50), unique= False)
	address = db.Column(db.String(500), unique= False)
	zipcode = db.Column(db.Integer, unique= False)
	password_hash = db.Column(db.String(128))

	@property
	def password(self):
		raise AttributeError('password is not a readable attribute!')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def __init__(self, name, username, email,password_hash,city,contact,address,zipcode):
		self.name = name
		self.username = username
		self.email = email
		self.password_hash = password_hash
		self.city = city
		self.contact = contact
		self.address = address
		self.zipcode = zipcode

	# Create A String
	def __repr__(self):
		return '<Name %r>' % self.name


# Create Custom Error Pages

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
	return render_template("500.html"), 500



# Create a Blog Post model
class Posts(db.Model):
	__seachbale__ = ['name']
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	content = db.Column(db.Text)
	price = db.Column(db.Integer, nullable=False)
	image = db.Column(db.String(5000), nullable=False)
	date_posted = db.Column(db.DateTime, default=datetime.utcnow)
	# Foreign Key To Link Users (refer to primary key of the user)
	poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	


# Create a Posts Form
class PostForm(FlaskForm):
	name = StringField("Product Name", validators=[DataRequired()])
	price = IntegerField("Price",  validators=[DataRequired()])
	content = CKEditorField('Content', validators=[DataRequired()])
	image = StringField("Image", validators=[DataRequired()])
	submit = SubmitField("Submit")



# Create Login Form
class LoginForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Submit")
 
# Create a Form Class
class UserForm(FlaskForm):
	id = db.Column(db.Integer, primary_key=True)
	name = StringField("Name", validators=[DataRequired()])
	username = StringField("Username", validators=[DataRequired()])
	email = StringField("Email", validators=[DataRequired()])
	password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message='Passwords Must Match!')])
	password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()] )
	city = StringField('City: ',validators=[DataRequired()] )
	contact = StringField('Contact', validators=[DataRequired(),])
	address = StringField('Address: ', validators=[DataRequired()] )
	zipcode = IntegerField('Zip code: ', validators=[DataRequired()])
	submit = SubmitField("Submit")


class JsonEcodedDict(db.TypeDecorator):
    impl = db.Text
    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        else:
            return json.dumps(value)
    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        else:
            return json.loads(value)


class CustomerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False)
    customer_id = db.Column(db.Integer, unique=False, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    orders = db.Column(JsonEcodedDict)

    def __repr__(self):
        return'<CustomerOrder %r>' % self.invoice



@app.route('/SignUp', methods=['GET', 'POST'])
def add_user():
	name = None
	form = UserForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(email=form.email.data).first()
		if user is None:
			# Hash the password!!!
			hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
			user = Users(username=form.username.data, name=form.name.data, email=form.email.data, password_hash=hashed_pw,  city=form.city.data, contact=form.contact.data, address=form.address.data, zipcode=form.zipcode.data)
			db.session.add(user)
			db.session.commit()
		name = form.name.data
		form.name.data = ''
		form.username.data = ''
		form.email.data = ''
		form.password_hash.data = ''
		form.city.data = ''
		form.contact.data = ''
		form.address.data = ''
		form.zipcode.data = ''    

		flash("User Added Successfully!")
		return redirect(url_for('Login'))
	our_users = Users.query.order_by(Users.date_added)
	return render_template("add_user.html", 
		form=form,
		name=name,
		our_users=our_users)



@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
	post_to_delete = Posts.query.get_or_404(id)
	id = current_user.id
	if id == id:
		try:
			db.session.delete(post_to_delete)
			db.session.commit()

			# Return a message
			flash("Blog Post Was Deleted!")

			# Grab all the posts from the database
			posts = Posts.query.order_by(Posts.date_posted)
			return render_template("posts.html", posts=posts)


		except:
			# Return an error message
			flash("Whoops! There was a problem deleting post, try again...")

			# Grab all the posts from the database
			posts = Posts.query.order_by(Posts.date_posted)
			return render_template("posts.html", posts=posts)
	else:
		# Return a message
		flash("You Aren't Authorized To Delete That Post!")

		# Grab all the posts from the database
		posts = Posts.query.order_by(Posts.date_posted)
		return render_template("posts.html", posts=posts)




# Create Logout Page
@app.route('/Logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	flash("You Have Been Logged Out!  Thanks For Stopping By...")
	return redirect(url_for('Login'))


@app.route('/Login', methods=['GET', 'POST'])
def Login():
	form = LoginForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(username=form.username.data).first()
		if user:
			# Check the hash
			if check_password_hash(user.password_hash, form.password.data):
				login_user(user)
				return redirect(url_for('OurStore'))
			else:
				flash("Wrong Password - Try Again!")
		else:
			flash("That User Doesn't Exist! Try Again...")

	return render_template('Login.html', form=form)


# Update Database Record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
	form = UserForm()
	name_to_update = Users.query.get_or_404(id)
	if request.method == "POST":
		name_to_update.name = request.form['name']
		name_to_update.email = request.form['email']
		name_to_update.username = request.form['username']
		name_to_update.city = request.form['city']
		name_to_update.contact = request.form['contact']
		name_to_update.address = request.form['address']
		name_to_update.zipcode = request.form['zipcode']
		try:
			db.session.commit()
			flash("User Updated Successfully!")
			return render_template("update.html", 
				form=form,
				name_to_update = name_to_update, id=id)
		except:
			flash("Error!  Looks like there was a problem...try again!")
			return render_template("update.html", 
				form=form,
				name_to_update = name_to_update,
				id=id)
	else:
		return render_template("update.html", 
				form=form,
				name_to_update = name_to_update,
				id = id)



# Create Admin Page
@app.route('/admin')
@login_required
def admin():
	id = current_user.id
	if id == 1:
		products = Posts.query.all()
        
		our_users = Users.query.order_by(Users.date_added)
		return render_template("admin.html", products=products,our_users=our_users)
	else:
		flash("Sorry you must be the Admin to access the Admin Page...")
		return redirect(url_for('Login'))

################################  add to cart   #########################################################
	
def MagerDicts(dict1,dict2):
    if isinstance(dict1, list) and isinstance(dict2,list):
        return dict1  + dict2
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))

@app.route('/addcart', methods=['POST'])
def AddCart():
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        product = Posts.query.filter_by(id=product_id).first()

        if request.method =="POST":
            DictItems = {product_id:{'name':product.name,'price':float(product.price),'quantity':quantity,'image':product.image,}}
            if 'Shoppingcart' in session:
                print(session['Shoppingcart'])
                if product_id in session['Shoppingcart']:
                    for key, item in session['Shoppingcart'].items():
                        if int(key) == int(product_id):
                            session.modified = True
                            item['quantity'] += 1
                else:
                    session['Shoppingcart'] = MagerDicts(session['Shoppingcart'], DictItems)
                    return redirect(request.referrer)
            else:
                session['Shoppingcart'] = DictItems
                return redirect(request.referrer)
              
    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)



@app.route('/carts')
def getCart():
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('OurStore'))
    subtotal = 0
    grandtotal = 0
    for key,product in session['Shoppingcart'].items():
        subtotal += float(product['price']) * int(product['quantity'])
        tax =("%.2f" %(.12 * float(subtotal)))
        grandtotal = float("%.2f" % (1.12 * subtotal))
    return render_template('carts.html',tax=tax, grandtotal=grandtotal, subtotal=subtotal , key=key)



@app.route('/updatecart/<int:code>', methods=['POST'])
def updatecart(code):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('OurStore'))
    if request.method =="POST":
        quantity = request.form.get('quantity')
        try:
            session.modified = True
            for key , item in session['Shoppingcart'].items():
                if int(key) == code:
                    item['quantity'] = quantity
                    return redirect(url_for('getCart'))
        except Exception as e:
            print(e)
            return redirect(url_for('getCart', key=key))

@app.route('/deleteitem/<int:id>')
def deleteitem(id):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('OurStore'))
    try:
        session.modified = True
        for key , item in session['Shoppingcart'].items():
            if int(key) == id:
                session['Shoppingcart'].pop(key, None)
                return redirect(url_for('getCart'))
    except Exception as e:
        print(e)
        return redirect(url_for('getCart'))


@app.route('/clearcart')
def clearcart():
    try:
        session.pop('Shoppingcart', None)
        return redirect(url_for('home'))
    except Exception as e:
        print(e)


#############################################################################################################


@app.route('/Checkout')
@login_required
def Checkout():
	return render_template("Checkout.html")

@app.route('/OurStore')
@login_required
def OurStore():
	posts = Posts.query.order_by(Posts.date_posted)
	return render_template("OurStore.html", posts=posts)

@app.route('/New')
def NewProduct():
	return render_template("NewProduct.html")

@app.route('/')
def Index():
	return render_template("Index.html")

@app.route('/cart1')
def cart1():
	return render_template("OurStore1.html")

@app.route('/result')
def result():
    searchword = request.args.get('q')
    products = Posts.query.msearch(searchword, fields=['name'] , limit=6)
    return render_template('search.html',products=products)


@app.route('/posts')
def posts():
	# Grab all the posts from the database
	posts = Posts.query.order_by(Posts.date_posted)
	return render_template("posts.html", posts=posts)

@app.route('/posts/<int:id>')
def post(id):
	post = Posts.query.get_or_404(id)
	return render_template('post.html', post=post)


@app.route('/add_product', methods=['GET', 'POST'])
#@login_required
def add_post():
	form = PostForm()

	if form.validate_on_submit():
		poster = current_user.id
		post = Posts(name=form.name.data, content=form.content.data, poster_id=poster, image=form.image.data, price=form.price.data)
		# Clear The Form
		form.name.data = ''
		form.content.data = ''
		form.price.data = ''
		form.image.data = ''

		# Add post data to database
		db.session.add(post)
		db.session.commit()

		# Return a Message
		flash("Blog Post Submitted Successfully!")

	# Redirect to the webpage
	return render_template("add_product.html", form=form)


@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
	post = Posts.query.get_or_404(id)
	form = PostForm()
	if form.validate_on_submit():
		post.name = form.name.data
		post.image = form.image.data
		post.price = form.price.data
		post.content = form.content.data
		# Update Database
		db.session.add(post)
		db.session.commit()
		flash("Post Has Been Updated!")
		return redirect(url_for('posts', id=post.id))
	
	if current_user.id == post.poster_id or current_user.id == 14:
		form.name.data = post.name
		form.image.data = post.image
		form.price.data = post.price
		form.content.data = post.content
		return render_template('edit_post.html', form=form)
	else:
		flash("You Aren't Authorized To Edit This Post...")
		posts = Posts.query.order_by(Posts.date_posted)
		return render_template("posts.html", posts=posts)


@app.route('/product/<int:id>')
def details(id):
	post = Posts.query.get_or_404(id)
	return render_template('details.html', post=post)

@app.route('/getorder')
@login_required
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        try:
            Order = CustomerOrder(invoice=invoice,customer_id=customer_id,orders=session['Shoppingcart'])
            db.session.add(Order)
            db.session.commit()
            session.pop('Shoppingcart')
            flash('Your order has been sent successfully','success')
            return redirect(url_for('orders'))
        except Exception as e:
            print(e)
            flash('Some thing went wrong while get order', 'danger')
            return redirect(url_for('getCart'))

@app.route('/orders')
@login_required
def orders():
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        customer = Users.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id).order_by(CustomerOrder.id.desc()).first()
        for _key, product in orders.orders.items():
            subTotal += float(product['price']) * int(product['quantity'])
            tax = ("%.2f" % (.12 * float(subTotal)))
            grandTotal = ("%.2f" % (1.12 * float(subTotal)))

    else:
        return redirect(url_for('Login'))
    return render_template('order.html', tax=tax,subTotal=subTotal,grandTotal=grandTotal,customer=customer,orders=orders)


@app.route('/Manage_Account')
@login_required
def Profile():
    return render_template('Profile.html')

@app.route('/web')
def wen():
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template('wentest.html',posts=posts)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True,)

