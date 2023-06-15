"""SQLAlchemy models for Seren"""

import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png"
    )

    bio = db.Column(
        db.Text,
        default="N/A"
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    last_quest = db.Column(
        db.DateTime
    )

    location = db.Column(
        db.Text,
        default="N/A"
    )

    password = db.Column(
        db.Text,
        nullable=False
    )

    quests = db.relationship('Quest')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`."""

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Quest(db.Model):
    """A user quest uncompleted or completed."""

    __tablename__ = 'quests'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String,
        nullable=False
    )

    address = db.Column(
        db.String,
        nullable=False
    )

    image = db.Column(
        db.String,
        nullable=False
    )

    complete_image = db.Column(
        db.String,
        default="NONE"
    )

    status = db.Column(
        db.String,
        default="In-progress"
    )

    reflection = db.Column(
        db.String,
        default="NONE"
    )

    points = db.Column(
        db.Integer,
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    user = db.relationship('User')


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """
    
    db.app = app
    db.init_app(app)
    # db.drop_all()
    db.create_all()