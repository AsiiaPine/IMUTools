import json

data = {"imu_1": [{"angle": 360, "forward": 1, "speed": 360}, {"angle": 360, "forward": -1, "speed": 360}]}

string = json.dumps(data)
with open("motor_speeds.json", 'w+', encoding='utf-8') as f:
        json.dump(string, f, ensure_ascii=False, indent=4)