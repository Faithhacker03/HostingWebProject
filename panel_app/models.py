import enum
from panel_app import db, login_manager
from flask_login import UserMixin

# This class defines the possible states a user's bot can be in.
# Using an Enum makes the code cleaner and less prone to typos than using simple strings.
class BotStatus(enum.Enum):
    STOPPED = "Stopped"
    RUNNING = "Running"
    ERROR = "Error"


# This function is required by the Flask-Login extension.
# It tells Flask-Login how to find a specific user from the ID stored in their session cookie.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# This class defines the 'users' table in our database.
# It inherits from db.Model (for SQLAlchemy functionality) and UserMixin (for Flask-Login).
class User(db.Model, UserMixin):
    # The primary key for the table. Each user will have a unique, auto-incrementing ID.
    id = db.Column(db.Integer, primary_key=True)
    
    # The user's email address. It must be unique and cannot be empty.
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # The user's hashed password. We store a hash, NEVER the plain text password.
    password = db.Column(db.String(60), nullable=False)
    
    # A boolean flag to determine if a user is an administrator.
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # This creates a one-to-one relationship with the Bot model.
    # It means each User can have one Bot. 'backref' lets us access the User from a Bot object (e.g., my_bot.owner).
    # 'uselist=False' specifies that this is a one-to-one, not a one-to-many relationship.
    bot = db.relationship('Bot', backref='owner', uselist=False, cascade="all, delete-orphan")


# This class defines the 'bots' table in our database.
# It stores the state and metadata for each user's bot.
class Bot(db.Model):
    # The primary key for the bots table.
    id = db.Column(db.Integer, primary_key=True)
    
    # A foreign key linking this bot back to its owner in the 'users' table.
    # This ensures that every bot belongs to a registered user.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # The current status of the bot, using our BotStatus Enum.
    status = db.Column(db.Enum(BotStatus), default=BotStatus.STOPPED, nullable=False)
    
    # The Process ID (PID) of the running bot script.
    # This is how our runner.py script knows which process to stop. It can be null if the bot is stopped.
    pid = db.Column(db.Integer, nullable=True)
    
    # The path to the bot's log file on the persistent disk.
    log_file = db.Column(db.String(200), nullable=True)
