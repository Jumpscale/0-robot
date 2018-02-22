import os
import sys

from flask import Flask, jsonify, send_file, send_from_directory
from js9 import j

from .blueprints_api import blueprints_api
from .services_api import services_api
from .templates_api import templates_api

dir_path = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

app.register_blueprint(blueprints_api)
app.register_blueprint(services_api)
app.register_blueprint(templates_api)


@app.route('/apidocs/<path:path>')
def send_js(path):
    return send_from_directory(dir_path + '/' + 'apidocs', path)


@app.route('/', methods=['GET'])
def home():
    return send_file(dir_path + '/index.html')


@app.errorhandler(500)
def internal_error(err):
    _, _, exc_traceback = sys.exc_info()
    eco = j.core.errorhandler.parsePythonExceptionObject(err, tb=exc_traceback)
    return jsonify(code=500, message=eco.errormessage, stack_trace=eco.traceback), 500


if __name__ == "__main__":
    app.run(debug=True)
