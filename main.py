from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = "password"  

@app.route("/")
def home():
    return render_template("landing.html")
    test_value = os.getenv("TEST_KEY", "Not set")
    return render_template("landing.html", test_value=test_value)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
