import os
import click # <-- Make sure 'click' is in your requirements.txt too!
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config # <-- Ensure config.py exists and is error-free

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

# THIS IS THE FUNCTION GUNICORN IS LOOKING FOR
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure necessary folders exist on the persistent disk
    instance_path = os.path.join(os.getenv("RENDER_DISK_PATH", "."), "instance")
    user_data_path = app.config['USER_DATA_PATH']
    os.makedirs(instance_path, exist_ok=True)
    os.makedirs(user_data_path, exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from panel_app.routes import main # <-- Ensure panel_app/routes.py exists and is error-free
    app.register_blueprint(main)

    # Command to create the first admin user
    @app.cli.command("create-admin")
    def create_admin():
        """Creates the admin user from .env variables."""
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not all([admin_email, admin_password]):
            print("Error: ADMIN_EMAIL and ADMIN_PASSWORD must be set in your environment.")
            return
        
        from panel_app.models import User # <-- Ensure panel_app/models.py exists and is error-free
        if User.query.filter_by(email=admin_email).first():
            print(f"Admin user with email {admin_email} already exists.")
            return

        hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')
        admin_user = User(email=admin_email, password=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user {admin_email} created successfully.")

    with app.app_context():
        db.create_all() # Create database tables if they don't exist

    return app # <-- Make sure this line is here and correctly indented
