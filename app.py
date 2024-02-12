from flask import Flask, render_template
import sys

app = Flask(__name__)
version = "0.0.1"


@app.route("/")
def index():
    return render_template('index.html', version=version, username="RawBin")


if __name__ == '__main__':
    print('Please run OMEN using flask run.')
    sys.exit(1)
