from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = "password" 

test_value = os.environ.get("TEST_KEY")

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/home")
def home():
    return render_template("landing.html", test_value=test_value)

@app.route("/reminders")
def reminder():
    return render_template("reminders.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/symptomTracker")
def symptom():
    return render_template("symptomReport.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

print("TEST_KEY is:", os.environ.get("TEST_KEY"))