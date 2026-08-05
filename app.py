from flask import Flask, render_template
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', year=datetime.datetime.now().year)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
