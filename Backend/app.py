from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)

@app.route('/load', methods=['GET'])
def load_file():
    filename = request.args.get('filename')
    path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(path):
        return jsonify({"content": ""})

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    return jsonify({"content": content})


@app.route('/save', methods=['POST'])
def save_file():
    data = request.json
    filename = data.get('filename')
    content = data.get('content')

    path = os.path.join(BASE_DIR, filename)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    return jsonify({"message": "File saved successfully"})


if __name__ == '__main__':
    app.run(debug=True)