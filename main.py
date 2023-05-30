from flask import Flask, render_template, request, redirect, url_for
import datetime
import calendar
import smtplib
import os
from dotenv import load_dotenv
from flask_ckeditor import CKEditor, CKEditorField
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL

load_dotenv()

app = Flask(__name__)
app.config['SECRET KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = "secret"

db = SQLAlchemy(app)
ckeditor = CKEditor(app)
Bootstrap(app)


class BlogPost(db.Model):
    # id, title, subtitle, date, body, author, img_url
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True, nullable=False)
    subtitle = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(100), nullable=True, default=datetime.datetime.utcnow)
    body = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(255), nullable=False)
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


@app.route("/")
def home():
    return render_template("index.html", all_posts=BlogService.get_posts(), date=BlogService.get_current_date())


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
def create_new_post():
    form = PostForm()

    if request.method == 'POST':
        data = request.form.get('body')

        if form.validate_on_submit():
            new_post = BlogPost(title=form.title.data,
                                subtitle=form.subtitle.data,
                                body=data,
                                author=form.author.data,
                                img_url=form.img_url.data)
            db.session.add(new_post)
            db.session.commit()

            # TODO: check how to pass status code.
            return redirect(url_for("home"))

    return render_template("make-post.html", form=form)


@app.route("/posts/<int:post_id>")
def load_post(post_id):
    posts = BlogService.get_posts()
    for post in posts:
        if post.id == post_id:
            return render_template("post.html", post=post, date=BlogService.get_current_date())


@app.route("/posts/<int:post_id>", methods=['PATCH'])
def edit_post(post_id):
    pass


if __name__ == "__main__":
    app.run(debug=True)
