import os
from flask import render_template, url_for, flash, redirect, request, abort, Blueprint # <-- Added Blueprint here
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
# We only need db and bcrypt from our app package
from panel_app import db, bcrypt 
from panel_app.models import User, Bot, BotStatus
from panel_app.forms import RegistrationForm, LoginForm
from config import Config

# DEFINE the blueprint here. Do not import it.
main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data, password=hashed_password)
        db.session.add(user)
        # Every new user gets a Bot entry associated with them
        bot = Bot(owner=user, status=BotStatus.STOPPED)
        db.session.add(bot)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    user_folder = os.path.join(Config.USER_DATA_PATH, str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)

    if request.method == 'POST':
        # Check which form was submitted
        action = request.form.get('action')
        
        if action == 'upload_bot' and 'bot_file' in request.files:
            file = request.files['bot_file']
            if file and file.filename.endswith('.py'):
                file.save(os.path.join(user_folder, 'bot.py'))
                flash('bot.py uploaded successfully!', 'success')
            else:
                flash('Invalid file. Please upload a .py file.', 'danger')

        elif action == 'upload_reqs' and 'req_file' in request.files:
            file = request.files['req_file']
            if file and file.filename == 'requirements.txt':
                file.save(os.path.join(user_folder, 'requirements.txt'))
                flash('requirements.txt uploaded successfully!', 'success')
            else:
                flash('Invalid file. Please upload a file named requirements.txt.', 'danger')
        
        elif action == 'upload_db' and 'db_file' in request.files:
            file = request.files['db_file']
            if file and file.filename.endswith('.db'):
                # We save it with a consistent name for simplicity
                file.save(os.path.join(user_folder, 'user.db'))
                flash('Database file uploaded successfully!', 'success')
            else:
                flash('Invalid file. Please upload a .db file.', 'danger')
        
        return redirect(url_for('main.dashboard'))

    # Prepare data for GET request
    bot = current_user.bot
    files = {
        'bot_py': os.path.exists(os.path.join(user_folder, 'bot.py')),
        'req_txt': os.path.exists(os.path.join(user_folder, 'requirements.txt')),
        'db_file': os.path.exists(os.path.join(user_folder, 'user.db'))
    }
    
    log_content = "No log file found."
    log_file_path = os.path.join(user_folder, 'bot.log')
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r') as f:
                log_content = f.read()
        except Exception as e:
            log_content = f"Error reading log file: {e}"

    return render_template('dashboard.html', title='Dashboard', bot=bot, files=files, log_content=log_content)

@main.route("/bot/start")
@login_required
def start_bot():
    bot = current_user.bot
    bot.status = BotStatus.RUNNING
    db.session.commit()
    flash('Bot start request sent! It may take up to a minute to come online.', 'info')
    return redirect(url_for('main.dashboard'))

@main.route("/bot/stop")
@login_required
def stop_bot():
    bot = current_user.bot
    bot.status = BotStatus.STOPPED
    db.session.commit()
    flash('Bot stop request sent!', 'info')
    return redirect(url_for('main.dashboard'))

@main.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403) # Forbidden
    
    # Join User and Bot tables to get all info in one query
    users_with_bots = db.session.query(User, Bot).join(Bot, User.id == Bot.user_id).all()
    return render_template('admin.html', title='Admin Panel', users_with_bots=users_with_bots)
