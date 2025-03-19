from flask import Flask, render_template, request, url_for, redirect , flash , session , abort

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')