from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

app = Flask(__name__)

SQLALCHEMY_USERNAME = 'base-user'
SQLALCHEMY_PASSWORD = '9!dN$9GA6#ZobYEKFTAER2MK'
SQLALCHEMY_HOST = '2a599e2f061246909bc828e6bd4c37b3.db.arvandbaas.ir'
SQLALCHEMY_PORT = '3306'
SQLALCHEMY_DATABASE = 'default'

SQLALCHEMY_DATABASE_URI = f"mysql://{SQLALCHEMY_USERNAME}:{SQLALCHEMY_PASSWORD}@{SQLALCHEMY_HOST}:{SQLALCHEMY_PORT}/{SQLALCHEMY_DATABASE}"

print("Initializing SQLAlchemy")

# Initialize SQLAlchemy
Base = declarative_base()

print("SQLAlchemy initialized")

class Song(Base):
    __tablename__ = 'songs'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    SongID = Column(String(255))
    Email = Column(String(255))
    Status = Column(String(20))
    SpotifyID = Column(String(255), nullable=True)

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

@app.route('/upload', methods=['POST'])
def upload_file():
    email = request.form['email']
    desired_file = request.files['file']

    # Generate SongID (this is just a placeholder)
    song_id = str(uuid.uuid4())

    # Add entry to SQL database
    session = Session()
    new_song = Song(SongID=song_id, Status='pending', Email=email)
    session.add(new_song)
    session.commit()
    session.close()

    return jsonify({'song_id': song_id}), 200

if __name__ == '__main__':
    app.run(debug=True)
