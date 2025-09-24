from flask import Flask, render_template, request, redirect, url_for, flash

@app.route("/")
def home():
    return render_template("landing.html")
