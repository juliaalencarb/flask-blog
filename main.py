from flask import Flask, render_template, request
import requests
import datetime
import calendar
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


response = requests.get("https://api.npoint.io/56bcff06a50803bc404b")
data = response.json()

today = datetime.date.today()
day = today.day
month = calendar.month_name[today.month]
year = today.year
formatted_date = f"{month} {day}, {year}"


@app.route("/")
def home():
    return render_template("index.html", data=data, date=formatted_date)


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


@app.route("/posts/<int:post_id>")
def load_post(post_id):
    for post in data:
        if post["id"] == post_id:
            return render_template("post.html", post=post, date=formatted_date)


if __name__ == "__main__":
    app.run(debug=True)
