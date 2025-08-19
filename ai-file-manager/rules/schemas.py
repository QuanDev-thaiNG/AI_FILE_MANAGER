from marshmallow import Schema, fields, validate, ValidationError

class RuleConditionSchema(Schema):
    """Schema cho phần điều kiện (if) của quy tắc"""
    mimetype = fields.String()
    ext = fields.Raw()  # Có thể là string hoặc list
    language = fields.String()
    
    # Điều kiện về nội dung
    text_contains_any = fields.Raw(data_key='text.contains_any')
    text_contains_all = fields.Raw(data_key='text.contains_all')
    
    # Điều kiện về tên file
    filename_contains = fields.Raw(data_key='filename.contains')
    
    # Điều kiện về kích thước
    size_gt = fields.Integer(data_key='size.gt')
    size_lt = fields.Integer(data_key='size.lt')
    
    # Điều kiện về thời gian
    created_after = fields.String()
    created_before = fields.String()
    
    # Điều kiện về EXIF (cho ảnh)
    exif_camera_model = fields.Raw(data_key='exif.camera_model')
    exif_datetime = fields.String(data_key='exif.datetime')
    exif_gps_lat = fields.Float(data_key='exif.gps_lat')
    exif_gps_lon = fields.Float(data_key='exif.gps_lon')

class RuleActionSchema(Schema):
    """Schema cho phần hành động (then) của quy tắc"""
    move_to = fields.String()
    copy_to = fields.String()
    link_to = fields.String()
    rename = fields.String()
    rename_to = fields.String()
    tags_add = fields.List(fields.String())

class RuleSchema(Schema):
    """Schema cho một quy tắc hoàn chỉnh"""
    name = fields.String(required=True)
    if_condition = fields.Nested(RuleConditionSchema, data_key='if', required=True)
    then_action = fields.Nested(RuleActionSchema, data_key='then', required=True)

class RulesFileSchema(Schema):
    """Schema cho toàn bộ file quy tắc"""
    version = fields.Integer(required=True)
    rules = fields.List(fields.Nested(RuleSchema), required=True)

def validate_rules_file(file_content):
    """Kiểm tra tính hợp lệ của file quy tắc YAML"""
    try:
        schema = RulesFileSchema()
        result = schema.loads(file_content)
        return True, result
    except ValidationError as err:
        return False, err.messages

def get_rule_template():
    """Tạo mẫu quy tắc YAML"""
    template = '''
# File quy tắc sắp xếp file
version: 1
rules:
  - name: Ảnh chụp điện thoại
    if:
      mimetype: image/*
      exif.camera_model: ["iPhone", "Pixel", "Samsung"]
    then:
      move_to: "Photos/{year}/{month}"
      rename: "{datetime}_{camera_model}_{hash8}.{ext}"

  - name: Tài liệu học tập tiếng Việt
    if:
      mimetype: application/pdf
      language: vi
      text.contains_any: ["bài giảng", "đề cương", "bài tập"]
    then:
      move_to: "Docs/HocTap/{year}"
      tags_add: ["hoc_tap", "pdf"]

  - name: Video màn hình
    if:
      mimetype: video/*
      filename.contains: ["Screen Recording", "screen", "capture"]
    then:
      move_to: "Videos/ScreenCaptures/{year}/{month}"
      rename: "{created_ts}_{hash8}.{ext}"
'''
    return template