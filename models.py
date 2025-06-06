from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(10))  # 'student' or 'faculty'

class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(50))  # paper/patent/project
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    is_selected = db.Column(db.Boolean, default=False)
    abstract_path = db.Column(db.String(200), nullable=True)
