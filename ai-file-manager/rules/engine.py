import yaml
import re
import os
from pathlib import Path
from datetime import datetime
import fnmatch

class RulesEngine:
    """Máy luật xử lý các quy tắc sắp xếp file từ file YAML"""
    
    def __init__(self, rules_file=None):
        self.rules = []
        if rules_file:
            self.load_rules(rules_file)
    
    def load_rules(self, rules_file):
        """Tải quy tắc từ file YAML"""
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
                if not data or 'rules' not in data:
                    raise ValueError("File quy tắc không hợp lệ hoặc không có quy tắc nào")
                
                self.rules = data['rules']
                print(f"Đã tải {len(self.rules)} quy tắc từ {rules_file}")
        except Exception as e:
            print(f"Lỗi khi tải quy tắc: {e}")
            self.rules = []
    
    def evaluate_condition(self, condition, file_info):
        """Đánh giá một điều kiện đơn lẻ"""
        # Xử lý các loại điều kiện khác nhau
        for key, value in condition.items():
            # Điều kiện mimetype
            if key == 'mimetype':
                if isinstance(value, str) and value.endswith('/*'):
                    # Kiểm tra loại MIME chính (vd: image/*, video/*)
                    mime_prefix = value[:-2]
                    if not file_info.get('mimetype', '').startswith(mime_prefix):
                        return False
                elif file_info.get('mimetype') != value:
                    return False
            
            # Điều kiện exif
            elif key.startswith('exif.'):
                exif_key = key.split('.', 1)[1]
                if exif_key not in file_info.get('metadata', {}):
                    return False
                
                exif_value = file_info['metadata'][exif_key]
                
                # Kiểm tra giá trị
                if isinstance(value, list):
                    # Nếu value là danh sách, kiểm tra xem exif_value có trong danh sách không
                    if exif_value not in value:
                        return False
                elif exif_value != value:
                    return False
            
            # Điều kiện ngôn ngữ
            elif key == 'language':
                if file_info.get('language') != value:
                    return False
            
            # Điều kiện text.contains_any
            elif key == 'text.contains_any':
                if not file_info.get('text'):
                    return False
                
                text = file_info['text'].lower()
                if isinstance(value, list):
                    # Kiểm tra xem có bất kỳ từ nào trong danh sách xuất hiện trong text không
                    if not any(keyword.lower() in text for keyword in value):
                        return False
                elif value.lower() not in text:
                    return False
            
            # Điều kiện text.contains_all
            elif key == 'text.contains_all':
                if not file_info.get('text'):
                    return False
                
                text = file_info['text'].lower()
                if isinstance(value, list):
                    # Kiểm tra xem tất cả các từ trong danh sách có xuất hiện trong text không
                    if not all(keyword.lower() in text for keyword in value):
                        return False
                elif value.lower() not in text:
                    return False
            
            # Điều kiện filename.contains
            elif key == 'filename.contains':
                filename = file_info.get('filename', '').lower()
                if isinstance(value, list):
                    # Kiểm tra xem có bất kỳ từ nào trong danh sách xuất hiện trong tên file không
                    if not any(keyword.lower() in filename for keyword in value):
                        return False
                elif value.lower() not in filename:
                    return False
            
            # Điều kiện ext
            elif key == 'ext':
                if isinstance(value, list):
                    if file_info.get('ext', '').lower() not in [ext.lower() for ext in value]:
                        return False
                elif file_info.get('ext', '').lower() != value.lower():
                    return False
            
            # Điều kiện size
            elif key == 'size.gt':
                if file_info.get('size', 0) <= value:
                    return False
            elif key == 'size.lt':
                if file_info.get('size', 0) >= value:
                    return False
            
            # Điều kiện created_after
            elif key == 'created_after':
                if not file_info.get('created_ts'):
                    return False
                
                if isinstance(value, str):
                    try:
                        value_date = datetime.strptime(value, '%Y-%m-%d')
                        if file_info['created_ts'] < value_date:
                            return False
                    except ValueError:
                        return False
            
            # Điều kiện created_before
            elif key == 'created_before':
                if not file_info.get('created_ts'):
                    return False
                
                if isinstance(value, str):
                    try:
                        value_date = datetime.strptime(value, '%Y-%m-%d')
                        if file_info['created_ts'] > value_date:
                            return False
                    except ValueError:
                        return False
        
        # Nếu tất cả điều kiện đều thoả mãn
        return True
    
    def evaluate_rule(self, rule, file_info):
        """Đánh giá một quy tắc hoàn chỉnh"""
        if 'if' not in rule or 'then' not in rule:
            return False, None
        
        # Kiểm tra điều kiện
        if not self.evaluate_condition(rule['if'], file_info):
            return False, None
        
        # Nếu điều kiện thoả mãn, trả về hành động
        return True, rule['then']
    
    def apply_rules(self, file_info):
        """Áp dụng tất cả quy tắc cho một file"""
        actions = []
        
        for rule in self.rules:
            matched, action = self.evaluate_rule(rule, file_info)
            if matched:
                actions.append({
                    'rule_name': rule.get('name', 'Unnamed Rule'),
                    'action': action
                })
        
        return actions
    
    def format_path(self, path_template, file_info):
        """Định dạng đường dẫn theo template và thông tin file"""
        # Lấy các giá trị cần thiết từ file_info
        year = file_info.get('created_ts', datetime.now()).strftime('%Y')
        month = file_info.get('created_ts', datetime.now()).strftime('%m')
        day = file_info.get('created_ts', datetime.now()).strftime('%d')
        datetime_str = file_info.get('created_ts', datetime.now()).strftime('%Y%m%d_%H%M%S')
        
        # Tạo dictionary các placeholder
        placeholders = {
            'year': year,
            'month': month,
            'day': day,
            'datetime': datetime_str,
            'ext': file_info.get('ext', ''),
            'hash8': file_info.get('hash_sha256', '')[:8],
            'camera_model': file_info.get('metadata', {}).get('camera_model', 'unknown'),
            'created_ts': datetime_str,
            'title': self._slugify(file_info.get('metadata', {}).get('title', file_info.get('filename', 'untitled'))),
        }
        
        # Thay thế các placeholder trong template
        result = path_template
        for key, value in placeholders.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        return result
    
    def _slugify(self, text):
        """Chuyển đổi text thành slug an toàn cho tên file"""
        # Loại bỏ các ký tự đặc biệt và thay thế khoảng trắng bằng gạch dưới
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[\s]+', '_', text)
        return text[:50]  # Giới hạn độ dài
    
    def get_action_plan(self, file_info):
        """Tạo kế hoạch hành động cho một file"""
        actions = self.apply_rules(file_info)
        
        if not actions:
            return None
        
        # Lấy hành động đầu tiên phù hợp
        action = actions[0]['action']
        plan = {
            'rule_name': actions[0]['rule_name'],
            'source': file_info['abs_path'],
            'action_type': None,
            'target': None
        }
        
        # Xử lý hành động move_to
        if 'move_to' in action:
            plan['action_type'] = 'move'
            target_dir = self.format_path(action['move_to'], file_info)
            
            # Xử lý hành động rename nếu có
            if 'rename' in action:
                new_name = self.format_path(action['rename'], file_info)
                plan['target'] = os.path.join(target_dir, new_name)
            else:
                plan['target'] = os.path.join(target_dir, file_info['filename'])
        
        # Xử lý hành động copy_to
        elif 'copy_to' in action:
            plan['action_type'] = 'copy'
            target_dir = self.format_path(action['copy_to'], file_info)
            
            # Xử lý hành động rename nếu có
            if 'rename' in action:
                new_name = self.format_path(action['rename'], file_info)
                plan['target'] = os.path.join(target_dir, new_name)
            else:
                plan['target'] = os.path.join(target_dir, file_info['filename'])
        
        # Xử lý hành động link_to
        elif 'link_to' in action:
            plan['action_type'] = 'link'
            target_dir = self.format_path(action['link_to'], file_info)
            
            # Xử lý hành động rename nếu có
            if 'rename' in action:
                new_name = self.format_path(action['rename'], file_info)
                plan['target'] = os.path.join(target_dir, new_name)
            else:
                plan['target'] = os.path.join(target_dir, file_info['filename'])
        
        # Xử lý hành động rename_to
        elif 'rename_to' in action:
            plan['action_type'] = 'rename'
            new_name = self.format_path(action['rename_to'], file_info)
            plan['target'] = os.path.join(os.path.dirname(file_info['abs_path']), new_name)
        
        # Thêm tags nếu có
        if 'tags_add' in action:
            plan['tags'] = action['tags_add']
        
        return plan