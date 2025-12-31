from flask import Flask, render_template
from utils import load_trainings, get_training_by_problem, get_next_problem, load_problem

app = Flask(__name__)


@app.route("/")
def index():
    trainings = load_trainings()
    return render_template("index.html", trainings=trainings)

@app.route("/problem/<problem_name>")
def show_problem(problem_name):
    problem_data = load_problem(problem_name)
    return render_template("problem.html", problem_name=problem_name, problem_data=problem_data)

@app.route("/problem/<problem_name>/next")
def next_problem(problem_name):
    # 查找当前问题所属的训练
    training = get_training_by_problem(problem_name)
    if training:
        next_problem_name = get_next_problem(problem_name, training["problems"])
        if next_problem_name:
            return render_template("problem.html", problem_name=next_problem_name, problem_data=load_problem(next_problem_name))
    
    # 如果没有下一道题，返回首页
    return render_template("problem.html", problem_name="没有更多题目", problem_data=None)

if __name__ == "__main__":
    app.run(port=80, debug=True)
