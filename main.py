import wtforms.fields.html5
from flask import Flask, render_template, request, redirect, url_for, flash, abort
import datetime
import calendar
import smtplib
import os
from dotenv import load_dotenv
from flask_ckeditor import CKEditor, CKEditorField
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SECRET KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog-db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = "secret"

db = SQLAlchemy(app)
ckeditor = CKEditor(app)
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    posts = db.relationship('BlogPost', back_populates='author')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = relationship("User", back_populates='posts')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(255), unique=True, nullable=False)
    subtitle = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(100), nullable=True, default=datetime.datetime.utcnow)
    body = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(2083), nullable=False)


# with app.app_context():
#     db.create_all()


class PostForm(FlaskForm):
    # title, subtitle, author, img_url, body, submit
    title = StringField("Post title", validators=[DataRequired()])
    subtitle = StringField("Post subtitle", validators=[DataRequired()])
    author = StringField("Author name", validators=[DataRequired()])
    img_url = StringField("Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Post text", validators=[DataRequired()])
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=7)])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=7)])
    submit = SubmitField("Submit")


class BlogService:
    @staticmethod
    def get_current_date():
        today = datetime.date.today()
        day = today.day
        month = calendar.month_name[today.month]
        year = today.year
        formatted_date = f"{month} {day}, {year}"

        return formatted_date

    @staticmethod
    def get_posts():
        posts = db.session.query(BlogPost).all()
        return posts


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.id != 1:
                return abort(403)
            return f(*args, **kwargs)
        except AttributeError:
            return redirect(url_for("home"))
    return decorated_function


@app.route("/")
def home():
    return render_template("index.html", all_posts=BlogService.get_posts(), date=BlogService.get_current_date())


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            register_data = request.form

            # Check if user exists.
            check_user = db.session.query(User).filter_by(email=register_data['email']).first()
            if check_user:
                flash("Email already exists.")
                return redirect(url_for("login"))
            else:
                # If email is unique, add to db.
                hashed_pw = generate_password_hash(password=register_data['password'], method="pbkdf2:sha256", salt_length=8)
                new_user = User(name=register_data['name'], email=register_data['email'], password=hashed_pw)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for("home"))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        # Check if the email is on db.
        user = db.session.query(User).filter_by(email=request.form['email']).first()
        if not user:
            flash("Invalid email address.")
            return redirect(url_for("login"))
        else:
            if check_password_hash(user.password, request.form['password']):
                login_user(user)
                flash("User logged in successfully!")
                return redirect(url_for("home"))
            else:
                flash("Invalid password.")
                return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        if request.form["name"] and request.form["email"] and request.form["phone"] and request.form["message"]:
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(
                    user=os.getenv("MY_EMAIL"),
                    password=os.getenv("MY_PASSWORD")
                )
                connection.sendmail(
                    from_addr=os.getenv("MY_EMAIL"),
                    to_addrs="juliadealencarb@gmail.com",
                    msg=f"Subject:New blog message\n\nName: {request.form['name']}\nEmail: {request.form['email']}\n"
                        f"Phone: {request.form['phone']}\nMessage: {request.form['message']}"
                )

            return render_template("contact.html", sent=True)
    elif request.method == 'GET':
        return render_template("contact.html", sent=False)


@app.route("/posts", methods=['POST', 'GET'])
@admin_only
def create_new_post():
    form = PostForm()

    if request.method == 'POST':
        data = request.form.get('body')

        if form.validate_on_submit():
            new_post = BlogPost(title=form.title.data,
                                subtitle=form.subtitle.data,
                                body=data,
                                author=current_user,
                                img_url=form.img_url.data)
            db.session.add(new_post)
            db.session.commit()

            # TODO: check how to pass status code.
            return redirect(url_for("home"))

    return render_template("make-post.html", form=form, title="Create new post")


@app.route("/posts/<int:post_id>")
def load_post(post_id):
    user = current_user
    posts = BlogService.get_posts()
    for post in posts:
        if post.id == post_id:
            return render_template("post.html", post=post, date=BlogService.get_current_date())


@app.route("/edit-post/<int:post_id>", methods=['POST', 'GET'])
@admin_only
def edit_post(post_id):
    post_to_update = BlogPost.query.get(post_id)
    edit_form = PostForm(
        title=post_to_update.title,
        subtitle=post_to_update.subtitle,
        author=post_to_update.author,
        img_url=post_to_update.img_url,
        body=post_to_update.body
    )

    if edit_form.validate_on_submit():
        post_to_update.title = edit_form.title.data
        post_to_update.subtitle = edit_form.subtitle.data
        post_to_update.body = request.form.get('body')
        post_to_update.author = edit_form.author.data
        post_to_update.img_url = edit_form.img_url.data
        db.session.commit()
        return redirect(url_for("load_post", post_id=post_id))
    return render_template("make-post.html", form=edit_form, title="Update post")


@app.route('/delete-post/<int:post_id>')
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
