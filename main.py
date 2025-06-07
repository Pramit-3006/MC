from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, Proposal
from database import SessionLocal, engine, Base
from rag_engine import RAGEngine
import shutil
import os

app = FastAPI()
rag = RAGEngine()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), role: str = Form(...), db: Session = next(get_db())):
    user = db.query(User).filter_by(username=username, role=role).first()
    if not user:
        user = User(username=username, role=role)
        db.add(user)
        db.commit()
    if role == "student":
        return templates.TemplateResponse("student_dashboard.html", {"request": request, "user": username})
    else:
        proposals = db.query(Proposal).filter_by(approved=False).all()
        return templates.TemplateResponse("faculty_dashboard.html", {"request": request, "proposals": proposals})

@app.post("/submit-proposal", response_class=HTMLResponse)
def submit_proposal(request: Request, username: str = Form(...), topic: list[str] = Form(...), db: Session = next(get_db())):
    joined = ', '.join(topic)
    proposal = Proposal(username=username, topics=joined)
    db.add(proposal)
    db.commit()
    rag.add_proposal(f"{username}: {joined}")
    return templates.TemplateResponse("student_dashboard.html", {"request": request, "user": username, "msg": "Proposal submitted!"})

@app.post("/approve", response_class=HTMLResponse)
def approve_proposal(request: Request, proposal_id: int = Form(...), db: Session = next(get_db())):
    proposal = db.query(Proposal).get(proposal_id)
    proposal.approved = True
    db.commit()
    proposals = db.query(Proposal).filter_by(approved=False).all()
    return templates.TemplateResponse("faculty_dashboard.html", {"request": request, "proposals": proposals, "msg": "Approved."})

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request, username: str, db: Session = next(get_db())):
    proposal = db.query(Proposal).filter_by(username=username, approved=True, abstract_uploaded=False).first()
    return templates.TemplateResponse("upload_abstract.html", {"request": request, "user": username, "allowed": bool(proposal)})

@app.post("/upload")
async def upload(username: str = Form(...), file: UploadFile = File(...), db: Session = next(get_db())):
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    proposal = db.query(Proposal).filter_by(username=username, approved=True, abstract_uploaded=False).first()
    proposal.abstract_uploaded = True
    proposal.abstract_file = path
    db.commit()
    return {"status": "uploaded", "file": path}

@app.post("/ask-ai", response_class=HTMLResponse)
def ask_ai(request: Request, question: str = Form(...)):
    answer = rag.query_proposals(question)
    return templates.TemplateResponse("rag_suggestions.html", {"request": request, "answer": answer})
