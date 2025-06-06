from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os

from config import Config
from models import db, User, Proposal

app = Flask(Mentor Connect)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', role=current_user.role)

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if current_user.role != 'student':
        return "Unauthorized", 403
    if request.method == 'POST':
        types = request.form.getlist('type')
        for t in types:
            proposal = Proposal(student_id=current_user.id, type=t, title=request.form['title'], description=request.form['desc'])
            db.session.add(proposal)
        db.session.commit()
        flash('Proposals submitted!')
        return redirect(url_for('dashboard'))
    return render_template('student_submit.html')

@app.route('/select', methods=['GET', 'POST'])
@login_required
def select():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
    proposals = Proposal.query.filter_by(is_selected=False).all()
    if request.method == 'POST':
        selected_ids = request.form.getlist('select')
        for pid in selected_ids:
            proposal = Proposal.query.get(int(pid))
            proposal.is_selected = True
        db.session.commit()
        flash("Topics selected. Notification sent to students (simulated).")
        return redirect(url_for('dashboard'))
    return render_template('faculty_select.html', proposals=proposals)

@app.route('/upload_abstract/<int:proposal_id>', methods=['GET', 'POST'])
@login_required
def upload_abstract(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    if proposal.student_id != current_user.id or not proposal.is_selected:
        return "Unauthorized", 403
    if request.method == 'POST':
        file = request.files['abstract']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            proposal.abstract_path = path
            db.session.commit()
            flash("Abstract uploaded successfully.")
            return redirect(url_for('dashboard'))
        flash("Invalid file format.")
    return render_template('upload_abstract.html', proposal=proposal)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
