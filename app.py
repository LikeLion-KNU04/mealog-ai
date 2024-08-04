from flask import Flask
from flask_restx import Api, Resource, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_cors import CORS
import os
from ai.analyze import Model
from nutrition.nutrition_info import NutritionInfo

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
nut = NutritionInfo()


# body 검증 함수
def validate_request(req, required_keys):
    missing_keys = []
    for key in required_keys:
        if key not in req:
            missing_keys.append(key)
    if len(missing_keys) > 0:
        return missing_keys
    return False

# require_Keys
user_key = ("gender", "age", "height", "weight", "activity")
daily_key = ("kcal", "carbohydrate","sugar","fat", "protein","calcium","phosphorus","natrium","kalium","magnesium","iron","zinc","cholesterol","transfat")

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

@api.route('/score')
class Score(Resource):
    def post(self):
        
        # 요청 JSON 파싱
        req = api.payload

        if miss := validate_request(req, ['user_info', 'daily_nutrient']):
            return {"error": f"Invalid request, {miss} not exist"}, 400
                
        user_info = req['user_info']
        daily_nutrient = req['daily_nutrient']

        if miss := validate_request(user_info,user_key):
            return {"error": f"Invalid request, {miss} not exist"}, 400
    
        if miss := validate_request(daily_nutrient,daily_key):
            return {"error": f"Invalid request, {miss} not exist"}, 400
        
        # 영양소 점수 계산
        daily_score = nut.calc_daily_score(user_info, daily_nutrient)

        # 결과를 JSON으로 반환
        return daily_score, 200

@api.route('/EER')
class EER(Resource):
    def post(self):
        # 요청 JSON 파싱
        req = api.payload
        if miss := validate_request(req, ('user_info',)):
            return {"error": f"Invalid request, {miss} not exist"}, 400
        user_info = req['user_info']

        if miss := validate_request(user_info,user_key):
            return {"error": f"Invalid request, {miss} not exist"}, 400
        # 에너지 필요 추정량(EER) 계산
        EER = nut.calc_EER(user_info)

        # 결과를 JSON으로 반환
        return {"EER": EER}, 200

@api.route('/standard')
class Standard(Resource):
    def post(self):
        # 요청 JSON 파싱
        req = api.payload
        if miss := validate_request(req, ('gender','age')):
            return {"error": f"Invalid request, {miss} not exist"}, 400

        gender = req["gender"]
        age = req["age"] 

        # 영양소 기준값 조회
        standard = nut.get_nutrition_standard(gender, age)

        # 결과를 JSON으로 반환
        return standard, 200

if __name__ == '__main__':
    app.run(debug=True)