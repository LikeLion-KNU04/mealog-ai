import torch
from .models import Darknet
from .utils.datasets import LoadImages
from .utils.utils import non_max_suppression, scale_coords, load_classes
import pandas as pd
import os
class Model:
    def __init__(self, cfg = 'cfg/yolov3-spp-403cls.cfg', weights = 'weights/best_403food_e200b150v2.pt', names = "data/403food.names",csv="data/food.csv", img_size=320, conf_thres = 0.3, iou_thres = 0.5, device = 'cuda'):
        # 기본 설정
        base_path = os.path.dirname(__file__)
        self.cfg = os.path.join(base_path, cfg)
        self.weights = os.path.join(base_path, weights)
        self.names = os.path.join(base_path, names)
        self.csv = os.path.join(base_path, csv)
        self.img_size = img_size
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.device = device

        # 디바이스 및 모델 로드
        self.device = torch.device(self.device if torch.cuda.is_available() else 'cpu')
        print("device: ", self.device)
        self.model = Darknet(self.cfg, self.img_size).to(self.device)
        self.model.load_state_dict(torch.load(self.weights, map_location=self.device)['model'], strict=False)
        self.model.eval()
        print("model loaded")

        # 영양정보 로드
        self.nut = pd.read_csv(self.csv,dtype={'food_name':'str'},na_values='-',encoding='utf-8')
        print("food data loaded")

        # 클래스 이름 로드
        # self.class_names = load_classes(self.names)
        self.class_names = self.nut.iloc[:,0].tolist()
        print("class names loaded")

    def detect_single_image(self,image_path):
        
        # 이미지 로드
        dataset = LoadImages(image_path, img_size=self.img_size)

        # 이미지 처리
        path, img, im0s, _ = next(iter(dataset))
        img = torch.from_numpy(img).to(self.device)
        img = img.float() / 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # 예측
        with torch.no_grad():
            pred = self.model(img)[0]

        # NMS
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, multi_label=False, classes=None, agnostic=False)

        # 결과 처리
        count = 0
        res = []
        for det in pred:
            if det is not None and len(det):
                    # 좌표 복원
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0s.shape).round()

                    # 결과 출력
                    for *xyxy, conf, cls in det:
                        if cls != 0:
                            bnd = {"min_x": int(xyxy[0]),
                                         "min_y": int(xyxy[1]),
                                         "max_x": int(xyxy[2]),
                                         "max_y": int(xyxy[3])}
                            food_info = {"cls":int(cls),
                                         "class": self.class_names[int(cls)-1], 
                                         "confidence": float(conf),
                                         "bnd": bnd,
                                         "nut": self.nut.iloc[int(cls)-1,1:].to_dict()}
                            count += 1
                            res.append(food_info)

        #이미지 삭제
        upload_folder = os.path.abspath('upload')
        file_path = os.path.abspath(path)

        if os.path.commonpath([upload_folder, file_path]) == upload_folder:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")

        return {"path":path, "result":res}

if __name__ == '__main__':
    model = Model(cfg = './cfg/yolov3-spp-403cls.cfg', weights = './weights/best_403food_e200b150v2.pt', names = "./data/403food.names",csv="./data/food.csv", img_size=320, conf_thres = 0.3, iou_thres = 0.5, device = 'cuda')
    model.detect_single_image('test/test.jpg')