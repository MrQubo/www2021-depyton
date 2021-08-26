#!/usr/bin/env python3
import os
from flask import Flask, render_template_string

app = Flask(__name__)

FLAG = os.environ.pop('FLAG')

@app.route('/')
def home():
    return render_template_string(
    '''
        <form id=form action='#'>
            <label for=name_>Gib your name</label>
            <input id=name_ />
            <input type=submit style=display:none />
        </form>
        <script>
            function submit(event) {
                event.preventDefault();
                location.assign('/' + name_.value);
            }
            form.onsubmit = submit;
        </script>
    ''')

@app.route('/<name>')
def hello(name):
    return render_template_string('Hello ' + name + '!')


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 8000, debug = False)
