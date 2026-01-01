# 工具函数打包
import os
import json
import urllib.request
import ssl
import requests

def load_trainings():
    """读取training文件夹中的所有json文件，返回训练列表"""
    trainings = []
    training_dir = os.path.join(os.path.dirname(__file__), "training")

    if os.path.exists(training_dir):
        for filename in os.listdir(training_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(training_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # 版本号25.12.31
                        if data.get("version") == "25.12.31":
                            training_info = {
                                "name": data.get("name", filename.replace(".json", "")),
                                "description": data.get("description", "暂无描述"),
                                "problems": data.get("problems", []),
                                "filename": filename
                            }
                            trainings.append(training_info)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    return trainings


def get_next_problem(current_problem, training_problems):
    """获取训练中当前问题的下一个问题"""
    if current_problem in training_problems:
        current_index = training_problems.index(current_problem)
        if current_index < len(training_problems) - 1:
            return training_problems[current_index + 1]
    return None


def get_training_by_problem(problem_name):
    """根据问题名称查找所属的训练"""
    trainings = load_trainings()
    for training in trainings:
        if problem_name in training["problems"]:
            return training
    return None


def load_problem(problem_name):
    """读取指定题目的JSON文件"""
    problem_file = os.path.join(os.path.dirname(__file__), "problem", problem_name + ".json")

    if os.path.exists(problem_file):
        try:
            with open(problem_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading problem {problem_name}: {e}")
            return None
    return None


def is_training_completed(training, completed_trainings):
    """检查训练是否已完成"""
    training_name = training["name"]
    return training_name in completed_trainings

def get_hitokoto():
    """获取一言API数据"""
    url = "https://v1.hitokoto.cn/?c=a&c=b&c=c&c=d&c=e&c=f"
    try:
        # 禁用 SSL 证书验证
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            data = response.json()
            return data["hitokoto"]
        else:
            return "没有天赋，那就重复。"
    except requests.exceptions.RequestException as e:
        print(f"获取一言时出错: {e}")
        return "今天也要好好学习哦！"


def get_project_size():
    """获取项目大小"""
    project_dir = os.path.dirname(__file__)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(project_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return str(total_size / 1024) + "KB"
