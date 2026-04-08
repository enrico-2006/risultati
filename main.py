from typing import List, Optional, Annotated
from fastapi import FastAPI, HTTPException, Depends, Query, Request, Form
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from functools import lru_cache
import sqlite3
import sqlalchemy 
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String, select, Function, ForeignKey, Insert, func, delete

DATABASE_URL = "sqlite:///./partite.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = sqlalchemy.orm.declarative_base()

class Partite(Base):
    __tablename__ = "partite"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String)
    ora = Column(String)
    team1 = Column(Integer, ForeignKey("squadre.id"), default=None)
    team2 = Column(Integer, ForeignKey("squadre.id"), default=None)
    score1 = Column(Integer)
    score2= Column(Integer)
    data = Column(String)
class Squadre(Base):
    __tablename__="squadre"
    id = Column(Integer, default=None, primary_key=True)
    nome = Column(String)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app=FastAPI(title="partite")
templates = Jinja2Templates(directory="./")

@app.get("/")
async def api(request: Request, db: Session = Depends(get_db)):
    subq1 = (select(Squadre.nome).where(Partite.team1 == Squadre.id).scalar_subquery())
    subq2 = (select(Squadre.nome).where(Partite.team2 == Squadre.id).scalar_subquery())
    risultati = db.query(Partite.id, func.strftime("%d-%m-%Y", Partite.data).label("data"), Partite.ora, (subq1.label("team1")), (subq2.label("team2")), Partite.score1, Partite.score2).order_by(Partite.data.desc(), Partite.ora.desc())
    return templates.TemplateResponse("index.html", {"request": request, "risultati": risultati, "partite_elenco": risultati})

@app.post("/api/partite")
def aggiungi(data: str = Form(...), ora: str = Form(...), team1: str = Form(...), team2: str = Form(...), score1: int = Form(...), score2: int = Form(...), db: Session = Depends(get_db)):
    team1 = (select(Squadre.id).where(Squadre.nome == team1).scalar_subquery())
    team2 = (select(Squadre.id).where(Squadre.nome == team2).scalar_subquery())
    nuovo_risultato = Partite(data = data, ora = ora, team1 = team1,  team2 = team2, score1= score1, score2 = score2)
    db.add(nuovo_risultato)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/api/partita/{id}")
def modifica_partita(
    id: int, 
    nuovo_gol_casa: int = Form(...), 
    nuovo_gol_trasferta: int = Form(...), 
    db: Session = Depends(get_db)
):
    # Cerchiamo la partita nel DB
    partita = db.query(Partite).filter(id == Partite.id).first()
    
    if partita:
        partita.score1 = nuovo_gol_casa
        partita.score2 = nuovo_gol_trasferta
        db.commit() # Salva i cambiamenti
        
    return RedirectResponse(url="/", status_code=303)

@app.post("/api/partita/elimina/{id}")
def delete_partita(
    id: int, 
    db: Session = Depends(get_db)
):
    # Cerchiamo la partita nel DB
    partita = db.query(Partite).filter(id == Partite.id).first()
    if partita:
        db.delete(partita) # Elimina la riga
        db.commit()
        
    return RedirectResponse(url="/", status_code=303)