from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = "password"  

@app.route("/")
def home():
    return render_template("landing.html")
    test_value = os.environ.get("TEST_KEY")
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
