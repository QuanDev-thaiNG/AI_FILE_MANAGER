from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sys
import json

# Thêm thư mục gốc vào đường dẫn để import các module từ dự án
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import các module cần thiết từ dự án
try:
    from core.database import Database
    from core.ingest import FileIngestor
    from core.search import Searcher
    from core.organize import Organizer
    from core.tag import TagManager
except ImportError as e:
    print(f"Lỗi khi import module: {e}")

app = Flask(__name__, static_folder=os.path.abspath('.'), template_folder='.')

# Khởi tạo các đối tượng
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'database.db')
db = None
ingestor = None
searcher = None
organizer = None
tag_manager = None

# Đảm bảo thư mục data tồn tại
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
os.makedirs(data_dir, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/init', methods=['POST'])
def init_database():
    global db, ingestor, searcher, organizer, tag_manager
    try:
        db = Database(db_path)
        db.init_database()
        ingestor = FileIngestor(db)
        searcher = Searcher(db)
        organizer = Organizer(db)
        tag_manager = TagManager(db)
        return jsonify({"status": "success", "message": "Cơ sở dữ liệu đã được khởi tạo thành công"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi khởi tạo cơ sở dữ liệu: {str(e)}"}), 500

@app.route('/api/ingest', methods=['POST'])
def ingest_files():
    if not db:
        return jsonify({"status": "error", "message": "Cơ sở dữ liệu chưa được khởi tạo"}), 400
    
    data = request.json
    directory = data.get('directory')
    recursive = data.get('recursive', False)
    dry_run = data.get('dry_run', False)
    
    if not directory or not os.path.isdir(directory):
        return jsonify({"status": "error", "message": "Đường dẫn thư mục không hợp lệ"}), 400
    
    try:
        results = ingestor.ingest_directory(directory, recursive=recursive, dry_run=dry_run)
        return jsonify({
            "status": "success", 
            "message": f"Đã quét {results} file", 
            "files_count": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi quét file: {str(e)}"}), 500

@app.route('/api/search', methods=['POST'])
def search_files():
    if not db:
        return jsonify({"status": "error", "message": "Cơ sở dữ liệu chưa được khởi tạo"}), 400
    
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({"status": "error", "message": "Truy vấn tìm kiếm không được để trống"}), 400
    
    try:
        results = searcher.search(query)
        return jsonify({
            "status": "success", 
            "message": f"Tìm thấy {len(results)} kết quả", 
            "results": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi tìm kiếm: {str(e)}"}), 500

@app.route('/api/organize', methods=['POST'])
def organize_files():
    if not db:
        return jsonify({"status": "error", "message": "Cơ sở dữ liệu chưa được khởi tạo"}), 400
    
    data = request.json
    directory = data.get('directory')
    rule_name = data.get('rule_name')
    dry_run = data.get('dry_run', False)
    
    if not directory or not os.path.isdir(directory):
        return jsonify({"status": "error", "message": "Đường dẫn thư mục không hợp lệ"}), 400
    
    if not rule_name:
        return jsonify({"status": "error", "message": "Tên quy tắc không được để trống"}), 400
    
    try:
        results = organizer.organize(directory, rule_name, dry_run=dry_run)
        return jsonify({
            "status": "success", 
            "message": f"Đã tổ chức {len(results)} file", 
            "results": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi tổ chức file: {str(e)}"}), 500

@app.route('/api/tags', methods=['GET'])
def get_all_tags():
    if not db:
        return jsonify({"status": "error", "message": "Cơ sở dữ liệu chưa được khởi tạo"}), 400
    
    try:
        tags = tag_manager.list_all_tags()
        return jsonify({
            "status": "success", 
            "tags": tags
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi lấy danh sách thẻ: {str(e)}"}), 500

@app.route('/api/tags/file', methods=['POST'])
def get_file_tags():
    if not db:
        return jsonify({"status": "error", "message": "Cơ sở dữ liệu chưa được khởi tạo"}), 400
    
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path or not os.path.isfile(file_path):
        return jsonify({"status": "error", "message": "Đường dẫn file không hợp lệ"}), 400
    
    try:
        tags = tag_manager.list_tags(file_path)
        return jsonify({
            "status": "success", 
            "file": file_path,
            "tags": tags
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi lấy thẻ của file: {str(e)}"}), 500

@app.route('/api/tags/add', methods=['POST'])
def add_tag():
    if not db:
        return jsonify({"status": "error", "message": "Cơ sở dữ liệu chưa được khởi tạo"}), 400
    
    data = request.json
    file_path = data.get('file_path')
    tag = data.get('tag')
    
    if not file_path or not os.path.isfile(file_path):
        return jsonify({"status": "error", "message": "Đường dẫn file không hợp lệ"}), 400
    
    if not tag:
        return jsonify({"status": "error", "message": "Thẻ không được để trống"}), 400
    
    try:
        tag_manager.add_tag(file_path, tag)
        return jsonify({
            "status": "success", 
            "message": f"Đã thêm thẻ '{tag}' cho file"
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi thêm thẻ: {str(e)}"}), 500

@app.route('/api/tags/remove', methods=['POST'])
def remove_tag():
    if not db:
        return jsonify({"status": "error", "message": "Cơ sở dữ liệu chưa được khởi tạo"}), 400
    
    data = request.json
    file_path = data.get('file_path')
    tag = data.get('tag')
    
    if not file_path or not os.path.isfile(file_path):
        return jsonify({"status": "error", "message": "Đường dẫn file không hợp lệ"}), 400
    
    if not tag:
        return jsonify({"status": "error", "message": "Thẻ không được để trống"}), 400
    
    try:
        tag_manager.remove_tag(file_path, tag)
        return jsonify({
            "status": "success", 
            "message": f"Đã xóa thẻ '{tag}' khỏi file"
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi xóa thẻ: {str(e)}"}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    status = {
        "database_initialized": db is not None,
        "version": "1.0.0",
        "data_path": data_dir
    }
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)