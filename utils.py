import os
import json

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
