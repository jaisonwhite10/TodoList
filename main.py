from flask import Flask, render_template,redirect,url_for,flash,request,abort
from forms import RegisterForm,LoginForm
from flask_bootstrap import Bootstrap
from datetime import date
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.orm.session import make_transient
from flask_login import UserMixin,AnonymousUserMixin,login_user,LoginManager,current_user,logout_user,login_required
from functools import wraps
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TodoListProject'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# session_options {'expire_on_commit': False}
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return (User.query.filter_by(id=user_id).first())

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250))
    name = db.Column(db.String(1000))

class TodoList(db.Model):
    __tablename__ = 'td_lists'
    id = db.Column(db.Integer, primary_key=True)
    char_id = db.Column(db.String(8),unique=True)
    list_owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    list_owner = db.relationship('User', backref='td_lists')
    name = db.Column(db.String(250), unique=False, nullable=False)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    task_owner = db.relationship('User', backref='tasks')
    td_list_id = db.Column(db.Integer, db.ForeignKey('td_lists.char_id'))
    td_list = db.relationship('TodoList', backref='tasks')
    task_name = db.Column(db.String(250))
    task_completed = db.Column(db.Boolean,nullable=False)



with app.app_context():
    db.create_all()

# today = None
# first_task = None
# task_list = None
def admin_only(function):
    @wraps(function)
    def check_user_id(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return function(*args, **kwargs)
        else:
            return abort(403)

    return check_user_id()

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))




@app.route('/register',methods=['GET','POST'])
def register():
    email = request.form.get('email')

    form = RegisterForm()
    user = User.query.filter_by(email=email).first()
    if request.method == 'POST':
        if user:
            flash('User already exists, please login instead!')
            return redirect(url_for('login'))
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        with app.app_context():
            new_user = User(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            user = User.query.filter_by(password=hashed_password).first()
            login_user(user)
            return redirect(url_for('show_lists'))
    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if request.method == 'POST':
        if not user:
            flash('This email does not exist. Please try again!')
        elif not check_password_hash(user.password,password):
            flash('Password incorrect. Please try again!')
        else:
            login_user(user)
            return redirect(url_for('show_lists'))
    return render_template('login.html',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('show_lists'))

@app.route('/',methods=['GET','POST'])
def show_lists():
    user_id = None
    first_task = request.form.get('first_task')
    today = date.today().strftime('%m/%d/%Y')

    if request.method == 'POST':
        with app.app_context():
            # Set expire_on_commit=False on the session
            db.session.expire_on_commit = False

            todo_list = TodoList(name=today,char_id=generate_key())
            db.session.add(todo_list)
            db.session.commit()

            list_first_task = Task(td_list_id=todo_list.char_id,task_name=first_task,task_completed=False)
            db.session.merge(list_first_task)

            # db.session.add(list_first_task)
            db.session.commit()

            # Reset expire_on_commit to default value
            # db.session.expire_on_commit = True
            db.session.refresh(todo_list)

        return redirect(url_for('todo_list',char_id=todo_list.char_id))
    # if current_user.is_authenticated:
    #     user_id = current_user.id

    return render_template('index.html',logged_in=current_user.is_authenticated)

@app.route('/new_list',methods=['GET','POST'])
def new_list():
    today = date.today().strftime('%m/%d/%Y')
    if current_user.is_authenticated:
        flash('Enter your first task and press enter to save')
        todo_list = TodoList(name=today, char_id=generate_key(),list_owner_id=current_user.id)
        db.session.add(todo_list)
        db.session.commit()
        return redirect(url_for('todo_list', char_id=todo_list.char_id))

    else:
        return redirect(url_for('login'))



@app.route('/todo_list/<char_id>',methods=['GET','POST'])
def todo_list(char_id):
    completed_task_list = []

    today = date.today().strftime('%m/%d/%Y')
    first_task = request.form.get('first_task')
    new_task = request.form.get('new_task')
    # char = request.args.get('char_id')
    # task_list.append(first_task)
    todo_list = TodoList.query.filter_by(char_id=char_id).first()
    tasks_in_list = Task.query.filter_by(td_list_id=char_id).all()

    new_date = None  # Assign a default value to the variable
    the_new_date = None
    change_date = None
    # todolist = TodoList.query.all()

    if current_user.is_authenticated:
        print('authenticated')
        task_in_db = Task.query.filter_by(td_list_id=char_id).all()
        for tasks in task_in_db:
            print(tasks.owner_id)
            if tasks.owner_id != current_user.id:
                print(tasks)
                tasks.owner_id = current_user.id
                db.session.commit()
        # user = User.query.filter_by(email=current_user.email).first()
        # user_name = user.name
        # user_id = user.id
        # print(user)

        # todo_list = TodoList.query.filter_by(char_id=char_id).first()
        # print(todo_list)
        if request.method == 'POST' and 'save_list' in request.form:
            flash('List Successfully Saved!')
            print('to do list saved')
            with app.app_context():

                todo_list = TodoList.query.filter_by(char_id=char_id).first()
                todo_list.list_owner_id = current_user.id
                db.session.commit()

    if request.method == 'POST' and 'change_date' in request.form:
        change_date = True

    if request.method == 'POST' and 'new_date' in request.form:
        new_date = True
        change_date = False
        the_new_date = request.form.get('new_date')
        todo_list = TodoList.query.filter_by(char_id=char_id).first()
        todo_list.name = the_new_date
        db.session.commit()



    if request.method == 'POST' and 'checked_box' in request.form:

        # print('checkbox test worked!')
        task_name = request.form.get('checked_box')
        completed_task_list.append(task_name)
        task_in_db = Task.query.filter_by(td_list_id=char_id).all()
        # print(task_in_db)
        for tasks in task_in_db:
            if tasks.task_name == task_name:
                tasks.task_completed = True
                db.session.commit()

                print('task match!')
    # print(completed_task_list)
    # Count the number of completed tasks
    # completed_task_count = Task.query.filter_by(task_completed=True).count()
    completed_task_count = Task.query.filter(Task.td_list_id==char_id,Task.task_completed==True).count()
    print(completed_task_count)
        # checked_tasks = request.form.getlist('checked_box')
        # 'checked_tasks' will contain a list of values of checked checkboxes

        # if not checked_tasks:
        #     print('No tasks selected!')
        #
        # for task in checked_tasks:
        #     if not task:
        #         continue
        #         print(task)
        #     # Process each task here
        # disabled = True

            # print(todo_list)

        # if request.method == 'POST':
        #     todo_list = TodoList(list_owner=user_name,list_owner_id=user_id, char_id=char_id)
        #     db.session.add(todo_list)
        #     db.session.commit()

    if request.method == 'POST' and 'new_task' in request.form:

        # try:
        #     print(current_user.email)
        #     print(user_id)
        # except AttributeError:
        #     print('ok')
        if current_user.is_authenticated:
            print('task matched to owner')
            # user = User.query.filter_by(email=current_user.email).first()
            # user_name = user.name
            # user_id = user.id
            with app.app_context():
                new_task_in_list = Task(td_list_id=char_id, task_name=new_task,owner_id=current_user.id,task_completed=False)

                db.session.add(new_task_in_list)

        #         todo_list = TodoList(list_owner=current_user.name,list_owner_id=current_user.id,char_id=char_id)
        #         db.session.add(todo_list)
                db.session.commit()
        else:
            with app.app_context():
                new_task_in_list = Task(td_list_id=char_id,task_name=new_task,task_completed=False)

                db.session.add(new_task_in_list)
                # try:
                # todo_list = TodoList(list_owner=user_name, list_owner_id=user_id, char_id=char_id)
                # db.session.add(todo_list)
                # except AttributeError:
                #     print('ok')
                db.session.commit()

        tasks_in_list = Task.query.filter_by(td_list_id=char_id).all()
        return redirect(url_for('todo_list',char_id=char_id))


    return render_template('show_list.html',date=today,tasks=tasks_in_list,char_id=char_id,logged_in=current_user.is_authenticated,completed_task_list=completed_task_count,change_date=change_date,new_date=new_date,the_new_date=the_new_date,todo_list=todo_list)



@app.route('/manage_lists/<user_id>',methods=['GET','POST'])
# @login_required
def manage_lists(user_id):
    if current_user.is_authenticated:
        print('authenticated')
        # user_id = current_user.id
        list_of_list = TodoList.query.filter_by(list_owner_id=current_user.id).all()
        print(list_of_list)
        task_counts = {}  # Create an empty dictionary to store task counts

        for list in list_of_list:
            print(list.char_id)
            # completed_task_count = Task.query.filter(Task.td_list_id == list.char_id, Task.task_completed == True).count()
            # print(completed_task_count)
            task_count = Task.query.filter(Task.td_list_id == list.char_id, Task.task_completed == False).count()
            task_counts[list.char_id] = task_count  # Store task count for each list


            # task_left_for_list = t

    else:
        return redirect(url_for('login'))
    return render_template('manage.html',list_of_list=list_of_list,user_id=current_user.id,logged_in=current_user.is_authenticated,task_counts=task_counts)

if __name__ == '__main__':
    app.run(debug=True)