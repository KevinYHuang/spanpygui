import os
import webbrowser
from threading import Thread
from flask import Flask, request, render_template

# Create an instance of Flask
client_path = os.path.join(os.path.dirname(__file__), '../client')
app = Flask(__name__, template_folder=os.path.join(client_path, 'templates'), static_folder=os.path.join(client_path, 'static'))
route = app.route

# Define a route and a function to handle it
@route('/')
def index():
    return render_template('index.html')

@route('/load_widget/<widget_name>', methods=['POST'])
def load_widget(widget_name):
    try:
        data = request.json
        return render_template(f'widgets/{widget_name}.html', data=request.json)
    except:
        return render_template(f'widgets/{widget_name}.html')

def run():
    def open_browser():
        # Specify the URL you want to open in the browser
        url = 'http://127.0.0.1:5000'  # Assuming your Flask app runs on localhost

        # Open the default web browser
        webbrowser.open_new(url)

    # Start a new thread to open the browser alongside the Flask app
    thread = Thread(target=open_browser)
    thread.start()

    app.run()