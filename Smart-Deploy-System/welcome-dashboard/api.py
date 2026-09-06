import os
import sys
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from pathlib import Path

# Add bridge to path
sys.path.append(str(Path(__file__).parent.parent / "bridge"))
from sync_engine import SyncEngine

app = Flask(__name__)
CORS(app)
engine = SyncEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        status = engine.check_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/diff/<path:filename>', methods=['GET'])
def get_diff(filename):
    try:
        is_hw = filename.startswith("HW:")
        clean_name = filename.replace("HW:", "")
        diff = engine.get_diff(clean_name, is_hw=is_hw)
        return jsonify({"success": True, "diff": diff})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def sync_file():
    data = request.json
    filename = data.get('filename')
    action = data.get('action') # 'pull' or 'push'
    
    if not filename or not action:
        return jsonify({"success": False, "error": "Missing params"}), 400
        
    try:
        is_hw = filename.startswith("HW:")
        clean_name = filename.replace("HW:", "")
        
        if action == 'pull':
            engine.pull(clean_name, is_hw=is_hw)
        elif action == 'push':
            engine.push(clean_name, is_hw=is_hw)
        else:
            return jsonify({"success": False, "error": "Invalid action"}), 400
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/content/<path:filename>', methods=['GET'])
def get_content(filename):
    try:
        is_hw = filename.startswith("HW:")
        clean_name = filename.replace("HW:", "")
        local_path = engine.files_to_sync.get(clean_name) or engine.hw_files.get(clean_name)
        content = engine.get_local_content(local_path)
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/save', methods=['POST'])
def save_content():
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    
    try:
        is_hw = filename.startswith("HW:")
        clean_name = filename.replace("HW:", "")
        local_path = engine.files_to_sync.get(clean_name) or engine.hw_files.get(clean_name)
        
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
