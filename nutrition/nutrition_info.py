import pandas as pd
import os

class NutritionInfo:
    #gender: 성별(0:남자,1:여자), age: 나이, weight: 몸무게, height: 키, activity: 활동량(0~3)

    def __init__(self,male_path="std/std_male.csv", female_path="std/std_female.csv"):
        base_path = os.path.dirname(__file__)
        male_path = os.path.join(base_path, male_path)
        female_path = os.path.join(base_path, female_path)
        # 기준 로드
        self.male_std = pd.read_csv(male_path, na_values='-')
        self.female_std = pd.read_csv(female_path, na_values='-')
        print("std data loaded")

    #에너지 필요 추정량(EER) 계산
    def calc_EER(self, user_info):
        #유저 데이터 파싱
        gender = user_info["gender"]
        age = user_info["age"]
        weight = user_info["weight"]
        height = user_info["height"]
        activity = user_info["activity"]

        #상수 설정
        if gender == 0:
            if age < 19:
                alpha = 88.5
                beta = -61.9
                gamma = 26.7
                delta = 903
                pa = (1.0,1.13, 1.26,1.42)[activity]
            else:
                alpha = 662
                beta = -9.53
                gamma = 15.91
                delta = 539.6
                pa = (1.0,1.11,1.25,1.48)[activity]
        else:
            if age < 19:
                alpha = 135.3
                beta = 30.8
                gamma = 10
                delta = 934
                pa = (1.0,1.16,1.31,1.56)[activity]
            else:
                alpha = 354
                beta = -6.91
                gamma = 9.36
                delta = 726
                pa = (1.0,1.12,1.27,1.45)[activity]

        #계산
        return alpha + beta*age + pa*(gamma*weight + delta*height/100)
    
    #성별, 나이에 따른 영양소 기준 정보 가져오기
    def get_nutrition_standard(self, gender, age):
        #성별에 따른 기준 정보
        if gender == 0:
            target_std = self.male_std
        else:
            target_std = self.female_std

        #나이별 인덱스
        if age <=2:
            idx = 0
        elif age <=5:
            idx = 1
        elif age <=8:
            idx = 2
        elif age <=11:
            idx = 3
        elif age <=14:
            idx = 4
        elif age <=18:
            idx = 5
        elif age <=29:
            idx = 6
        elif age <=49:
            idx = 7
        elif age <=64:
            idx = 8
        elif age <=74:
            idx = 9
        else:
            idx = 10
        
        return target_std.iloc[idx,1:].to_dict()

    #탄수화물, 단백질, 지방, 트랜스지방의 에너지 비율 계산
    def culc_energy_ratio(self, carbohydrate, protein, fat, transfat):
        total_energy = carbohydrate*4 + protein*4 + fat*9 + transfat*9
        carbohydrate_ratio = carbohydrate*4/total_energy * 100
        protein_ratio = protein*4/total_energy * 100
        fat_ratio = fat*9/total_energy * 100
        transfat_ratio = transfat*9/total_energy * 100
        return carbohydrate_ratio, protein_ratio, fat_ratio, transfat_ratio

    #각각의 비율 점수 계산
    def calc_ratio_score(self, target, range):
        ratio_score = 10
        if target < range[0] or target > range[1]:
            diff = min(abs(target - range[0]), abs(target - range[1]))
            ratio_score -= (diff/100) * 10
        return ratio_score

    # 에너지 비율 점수 계산
    def energy_ratio_score(self, carbohydrate, fat, protein, transfat):
        carb_ratio, protein_ratio, fat_ratio, transfat_ratio = self.culc_energy_ratio(carbohydrate, fat, protein, transfat)
        carb_range = (55, 65)
        protein_range = (7,20)    
        fat_range = (15, 30)

        carb_score = self.calc_ratio_score(carb_ratio, carb_range)
        protein_score = self.calc_ratio_score(protein_ratio, protein_range)
        fat_score = self.calc_ratio_score(fat_ratio, fat_range)
        if transfat_ratio > 1:
            transfat_score = 0
        else:
            transfat_score = 10

        total_score = carb_score + protein_score + fat_score + transfat_score
        return total_score, {"ratio_carb_score": carb_score, "ratio_protein_score": protein_score, "ratio_fat_score": fat_score, "ratio_transfat_score": transfat_score}        
    
    #영양소 섭취 점수 계산
    def calc_nutrition_score(self,standard, nutrient):
        total_score = 0
        detail_score = {}
        for nut in ("carbohydrate", "protein", "calcium", "phosphorus", "magnesium", "iron", "zinc"):
            diff = max(0, (standard[nut+"_RNI"] - nutrient[nut])/standard[nut+"_RNI"])
            score = 5*(1-(diff**2))
            detail_score["nut_"+nut+"_score"] = score
            total_score += score
        return total_score, detail_score

    #penalty 계산
    def calc_penalty(self,standard, nutrient):
        total_penalty = 0
        detail_penalty = {}
        for nut in ("phosphorus","natrium", "iron", "zinc","cholesterol"):
            penalty = 4 if nutrient[nut] > standard[nut+"_UL"] else 0
            total_penalty += penalty
            detail_penalty[nut+"_penalty"] = penalty
        return total_penalty, detail_penalty
    
    #칼로리 점수 계산
    def calc_energy_score(self, EER, nutrient):
        diff = abs(EER - nutrient["kcal"])/EER
        score = 10*max(0,(1-diff))
        return score
    
    #하루 식단 점수 계산
    def calc_daily_score(self, user_info, daily_nutrient):
        EER = self.calc_EER(user_info)
        standard = self.get_nutrition_standard(user_info["gender"],user_info["age"])
        #기본 점수
        daily_score = 20
        detail_score = {}
        #칼로리 점수(10점)
        energy_score = self.calc_energy_score(EER, daily_nutrient)
        daily_score += energy_score
        detail_score["energy_score"] = {"total":energy_score, "EER": EER, "kcal": daily_nutrient["kcal"]}
        #에너지 비율 점수(35점)
        energy_ratio_score, energy_ratio_detail = self.energy_ratio_score(daily_nutrient["carbohydrate"], daily_nutrient["fat"], daily_nutrient["protein"], daily_nutrient["transfat"])
        daily_score += energy_ratio_score
        detail_score["ratio_score"] = {"energy_ratio_score": energy_ratio_score, "detail": energy_ratio_detail}
        #영양소 섭취 점수(35점)
        nutrition_score, nutrition_detail = self.calc_nutrition_score(standard, daily_nutrient)
        daily_score += nutrition_score
        detail_score["nutrition_score"] = {"total": nutrition_score, "detail": nutrition_detail}
        #페널티(-20점)
        penalty, penalty_detail = self.calc_penalty(standard, daily_nutrient)
        daily_score -= penalty
        detail_score["penalty"] = {"total": penalty, "detail": penalty_detail}
        return {"daily_score": daily_score, "detail": detail_score}

if __name__ == '__main__':
    nut = NutritionInfo()
    print(nut.calc_EER(0, 30, 180, 70, 2))
    print(nut.get_nutrition_standard(1, 30)["cholesterol_UL"])
    user_info = {"gender":1, "age":30, "height":180, "weight":70, "activity":2}
    # print(nut.culc_energy_ratio(77.13, 8.84, 17.12, 0))
    # print(nut.energy_ratio_score(101.62, 23.15, 19.75, 0))
    # print(nut.calc_nutrition_score(nut.get_nutrition_standard(0, 30), {"carbohydrate": 77.13, "protein": 8.84, "calcium": 1000, "phosphorus": 700, "magnesium": 350, "iron": 0, "zinc": 11}))
    #print(nut.calc_penalty(nut.get_nutrition_standard(0, 30), {"phosphorus": 100000, "natrium": 2000, "iron": 20, "zinc": 10, "cholesterol": 300}))
    print()
    print(nut.calc_daily_score(user_info, {"carbohydrate": 77.13, "protein": 8.84, "fat": 17.12, "transfat": 0, "kcal": 2500, "calcium": 1000, "phosphorus": 700, "magnesium": 350, "iron": 0, "zinc": 11, "natrium": 2000, "cholesterol": 300}))



