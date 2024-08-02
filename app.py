from flask import Flask
from flask_restx import Api, Resource, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_cors import CORS
import os
from ai.analyze import Model

app = Flask(__name__)
api = Api(app)
CORS(app)  # CORS 설정

# 업로드된 파일을 저장할 디렉토리 설정
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 허용할 파일 확장자 설정
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API 파서 설정
upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)

# AI 모델 불러오기
model = Model()

@api.route('/upload')
class Upload(Resource):
    @api.expect(upload_parser)
    def post(self):
        args = upload_parser.parse_args()
        file = args['file']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # AI 모델로 이미지 분석
            analysis_result = model.detect_single_image(filepath)

            # 결과를 JSON으로 반환
            return {"result": analysis_result}, 200

        return {"error": "Invalid file type"}, 400
    
if __name__ == '__main__':
    app.run(debug=True)