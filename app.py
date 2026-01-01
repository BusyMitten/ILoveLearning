from flask import Flask, render_template, session, redirect, url_for, jsonify
from utils import (load_trainings, get_training_by_problem, get_next_problem,
                   load_problem, get_hitokoto, get_project_size, get_question_count, get_last_update_time)
from wsgiref.simple_server import make_server
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = 'BusySheng'  # 用于会话管理


@app.route("/")
def index():
    trainings = load_trainings()
    completed_trainings = session.get('completed_trainings', [])
    return render_template("index.html", 
                           trainings=trainings, 
                           completed_trainings=completed_trainings, 
                           hitokoto=get_hitokoto(),
                           version="26.1.1",
                           author="BusySheng",
                           project_size=get_project_size(),
                           question_count=get_question_count(),
                           last_update=get_last_update_time())

@app.route("/api/hitokoto")
def api_hitokoto():
    from flask import jsonify
    return jsonify({'hitokoto': get_hitokoto()})

@app.route("/problem/<problem_name>")
def show_problem(problem_name):
    problem_data = load_problem(problem_name)
    
    # 检查用户是否已经回答过这个问题
    user_answers = session.get('user_answers', {})
    training = get_training_by_problem(problem_name)
    training_key = f"{training['name']}_answers" if training else None
    user_answer = None
    if training_key and training_key in user_answers:
        user_answer = user_answers[training_key].get(problem_name)
    
    # 如果用户已经回答过问题，检查答案并提供反馈
    if user_answer is not None and problem_data and 'answer' in problem_data:
        if problem_data['type'] == 'choice':
            # 选择题
            correct_indices = problem_data['answer']
            if user_answer in correct_indices:
                feedback_message = '✔ 恭喜你答对了！'
                result = 'correct'
            else:
                correct_letters = [problem_data['options'][i]['choice'] for i in correct_indices]
                feedback_message = f'❌ 错误！正确答案是：{", ".join(correct_letters)}'
                result = 'incorrect'
            
            return render_template("problem.html", 
                                   problem_name=problem_name, 
                                   problem_data=problem_data,
                                   result=result,
                                   message=feedback_message,
                                   selected_option=user_answer)
        elif problem_data['type'] == 'input':
            # 填空题
            correct_indices = problem_data['answer']
            is_correct = False
            
            # 检查用户输入是否与正确答案匹配
            import json
            try:
                user_answer_list = json.loads(user_answer) if isinstance(user_answer, str) else user_answer
            except (json.JSONDecodeError, TypeError):
                # 如果不是JSON格式或不是列表，转换为列表
                user_answer_list = [user_answer] if user_answer is not None else []
            
            # 比较用户答案和正确答案（按顺序比较）
            if isinstance(correct_indices, list) and isinstance(user_answer_list, list):
                # 如果两者都是列表，按顺序比较每个元素
                if user_answer_list == correct_indices:
                    is_correct = True
                elif len(user_answer_list) == len(correct_indices):
                    # 检查每个位置的值是否相等（忽略大小写和空格）
                    is_correct = all(
                        str(user_val).strip().lower() == str(correct_val).strip().lower()
                        for user_val, correct_val in zip(user_answer_list, correct_indices)
                    )
            elif isinstance(correct_indices, list):
                # 如果正确答案是列表但用户答案不是
                if len(correct_indices) == 1:
                    is_correct = str(user_answer).strip().lower() == str(correct_indices[0]).strip().lower()
            else:
                # 如果都不是列表
                is_correct = str(user_answer).strip().lower() == str(correct_indices).strip().lower()
            
            if is_correct:
                feedback_message = '✔ 恭喜你答对了！'
                result = 'correct'
            else:
                # 获取正确答案的文本
                if isinstance(correct_indices, list):
                    correct_text_display = ', '.join(map(str, correct_indices))
                else:
                    correct_text_display = str(correct_indices)
                
                feedback_message = f'❌ 错误！正确答案是：{correct_text_display}'
                result = 'incorrect'
            
            return render_template("problem.html", 
                                   problem_name=problem_name, 
                                   problem_data=problem_data,
                                   result=result,
                                   message=feedback_message)
    
    return render_template("problem.html", problem_name=problem_name, problem_data=problem_data)

@app.route("/problem/<problem_name>/next")
def next_problem(problem_name):
    # 查找当前问题所属的训练
    training = get_training_by_problem(problem_name)
    
    if training:
        next_problem_name = get_next_problem(problem_name, training["problems"])
        
        # 检查是否是最后一个题目
        current_index = training["problems"].index(problem_name)
        is_last_problem = (current_index == len(training["problems"]) - 1)
        
        if next_problem_name:
            # 如果不是最后一个题目，跳转到下一个题目
            return render_template("problem.html", problem_name=next_problem_name, problem_data=load_problem(next_problem_name))
        elif is_last_problem:
            # 如果是最后一个题目，跳转到完成页面
            return redirect(url_for('training_completion', training_name=training["name"]))
    
    # 如果没有下一题，返回首页
    return render_template("problem.html", problem_name="没有更多题目", problem_data=None)

@app.route("/training/<training_name>/completion")
def training_completion(training_name):
    from utils import load_trainings
    
    # 获取训练信息以计算题目总数
    trainings = load_trainings()
    training = None
    for t in trainings:
        if t["name"] == training_name:
            training = t
            break
    
    if training:
        total_problems = len(training["problems"])
        
        # 从会话中获取用户的答题情况
        user_answers = session.get('user_answers', {})
        training_key = f"{training_name}_answers"
        training_answers = user_answers.get(training_key, {})
        
        # 计算正确答案数量
        correct_answers = 0
        for problem_name, user_answer in training_answers.items():
            problem_data = load_problem(problem_name)
            if problem_data and 'answer' in problem_data:
                # 根据题目类型判断答案
                if problem_data['type'] == 'choice':
                    correct_indices = problem_data['answer']
                    user_answer_index = user_answer  # 用户提交的是选项索引
                    if user_answer_index in correct_indices:
                        correct_answers += 1
                elif problem_data['type'] == 'input':
                    correct_indices = problem_data['answer']
                    is_correct = False
                    
                    # 检查用户输入是否与正确答案匹配
                    import json
                    try:
                        user_answer_list = json.loads(user_answer) if isinstance(user_answer, str) else user_answer
                    except (json.JSONDecodeError, TypeError):
                        # 如果不是JSON格式或不是列表，转换为列表
                        user_answer_list = [user_answer] if user_answer is not None else []
                    
                    # 比较用户答案和正确答案（按顺序比较）
                    if isinstance(correct_indices, list) and isinstance(user_answer_list, list):
                        # 如果两者都是列表，按顺序比较每个元素
                        if user_answer_list == correct_indices:
                            is_correct = True
                        elif len(user_answer_list) == len(correct_indices):
                            # 检查每个位置的值是否相等（忽略大小写和空格）
                            is_correct = all(
                                str(user_val).strip().lower() == str(correct_val).strip().lower()
                                for user_val, correct_val in zip(user_answer_list, correct_indices)
                            )
                    elif isinstance(correct_indices, list):
                        # 如果正确答案是列表但用户答案不是
                        if len(correct_indices) == 1:
                            is_correct = str(user_answer).strip().lower() == str(correct_indices[0]).strip().lower()
                    else:
                        # 如果都不是列表
                        is_correct = str(user_answer).strip().lower() == str(correct_indices).strip().lower()
                    
                    if is_correct:
                        correct_answers += 1
        
        accuracy = round((correct_answers / total_problems) * 100, 2) if total_problems > 0 else 0
        passed = accuracy >= 50
        
        # 记录已完成的训练
        completed_trainings = session.get('completed_trainings', [])
        if training_name not in completed_trainings:
            completed_trainings.append(training_name)
            session['completed_trainings'] = completed_trainings
        
        return render_template("completion.html", 
                               training_name=training_name,
                               total_problems=total_problems,
                               correct_answers=correct_answers,
                               accuracy=accuracy,
                               passed=passed)
    
    # 如果找不到训练，返回首页
    return redirect(url_for('index'))


@app.route("/submit_answer/<problem_name>", methods=['POST'])
def submit_answer(problem_name):
    from flask import request
    
    # 获取用户提交的答案
    user_answer = request.form.get('answer')
    training = get_training_by_problem(problem_name)
    problem_data = load_problem(problem_name)
    
    if training and user_answer is not None and problem_data and 'answer' in problem_data:
        # 保存用户的答案到会话中
        user_answers = session.get('user_answers', {})
        training_key = f"{training['name']}_answers"
        
        if training_key not in user_answers:
            user_answers[training_key] = {}
        
        # 根据题目类型处理答案存储
        if problem_data['type'] == 'choice':
            user_answer_value = int(user_answer)
        elif problem_data['type'] == 'input':
            # 对于填空题，解析JSON格式的答案
            import json
            try:
                user_answer_value = json.loads(user_answer)
                # 如果只有一项，直接保存为字符串
                if isinstance(user_answer_value, list) and len(user_answer_value) == 1:
                    user_answer_value = user_answer_value[0]
            except json.JSONDecodeError:
                # 如果不是JSON格式，直接保存原始答案
                user_answer_value = user_answer
        else:
            user_answer_value = user_answer  # 其他类型默认保存文本
        
        user_answers[training_key][problem_name] = user_answer_value
        session['user_answers'] = user_answers
        
        # 检查答案是否正确
        correct_indices = problem_data['answer']
        
        if problem_data['type'] == 'choice':
            # 选择题：检查索引是否正确
            user_answer_index = int(user_answer)
            is_correct = user_answer_index in correct_indices
            
            if is_correct:
                result = 'correct'
                message = '✔ 恭喜你答对了！'
            else:
                # 获取正确答案的字母
                correct_letters = [problem_data['options'][i]['choice'] for i in correct_indices]
                result = 'incorrect'
                message = f'❌ 错误！正确答案是：{", ".join(correct_letters)}'
            
            # 返回JSON格式的响应
            return jsonify({
                'result': result,
                'message': message,
                'selected_option': user_answer_index,
                'correct_indices': correct_indices
            })
        elif problem_data['type'] == 'input':
            # 填空题：检查用户输入是否匹配正确答案
            is_correct = False
            
            # 解析用户提交的JSON格式答案（多个填空的答案数组）
            import json
            try:
                user_answer_list = json.loads(user_answer)
            except json.JSONDecodeError:
                # 如果不是JSON格式，说明是单个答案
                user_answer_list = [user_answer]
            
            # 检查用户输入是否与正确答案匹配
            # 对于填空题，correct_indices 包含正确答案的列表
            correct_answer_list = correct_indices  # 根据P1004.json，正确答案是 ['1949', '1']
            
            # 比较用户答案和正确答案（按顺序比较）
            if isinstance(correct_answer_list, list) and isinstance(user_answer_list, list):
                # 如果两者都是列表，按顺序比较每个元素
                if user_answer_list == correct_answer_list:
                    is_correct = True
                elif len(user_answer_list) == len(correct_answer_list):
                    # 检查每个位置的值是否相等
                    is_correct = all(
                        str(user_val).strip().lower() == str(correct_val).strip().lower()
                        for user_val, correct_val in zip(user_answer_list, correct_answer_list)
                    )
            elif isinstance(correct_answer_list, list):
                # 如果正确答案是列表但用户答案不是
                if len(correct_answer_list) == 1:
                    is_correct = str(user_answer_list[0]).strip().lower() == str(correct_answer_list[0]).strip().lower()
            else:
                # 如果都不是列表
                is_correct = str(user_answer_list[0]).strip().lower() == str(correct_answer_list).strip().lower()
            
            if is_correct:
                result = 'correct'
                message = '✔ 恭喜你答对了！'
            else:
                # 获取正确答案的文本
                if isinstance(correct_answer_list, list):
                    correct_text_display = ', '.join(map(str, correct_answer_list))
                else:
                    correct_text_display = str(correct_answer_list)
                
                result = 'incorrect'
                message = f'❌ 错误！正确答案是：{correct_text_display}'
            
            # 返回JSON格式的响应
            return jsonify({
                'result': result,
                'message': message
            })
        
        # 如果是其他类型题目
        result = 'incorrect'
        message = '❌ 答案不正确'
        return jsonify({
            'result': result,
            'message': message
        })
    
    # 如果出现错误，返回错误信息
    return jsonify({'error': '提交答案失败'}), 400


class LoginForm(FlaskForm):
    name = StringField("用户名", validators=[DataRequired("用户名不能为空！")])
    password = PasswordField("密码", validators=[DataRequired("密码不能为空！")])
    submit = SubmitField(label="登录")

@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm()
    data = {}
    if form.validate_on_submit():
        data["name"] = form.name.data
        data["password"] = form.password.data
    return render_template("login.html", form=form, data=data)


if __name__ == "__main__":
    httpd = make_server('0.0.0.0', 5000, app)
    httpd.serve_forever()