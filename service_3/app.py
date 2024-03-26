import requests
from sqlalchemy import create_engine, Column, String, Integer, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os, sys
from time import sleep
import logging

logging.basicConfig(level=logging.DEBUG)

MAIL_API_KEY = '2625c947cc9213cb9acba6a7afe8dcc9-b02bcf9f-3568313f'


SQLALCHEMY_USERNAME = 'root'
SQLALCHEMY_PASSWORD = 'sPnKe8MyZzOCAR7uT0Usny0e'
SQLALCHEMY_HOST = 'everest.liara.cloud'
SQLALCHEMY_PORT = '31531'
SQLALCHEMY_DATABASE = 'lucid_sutherland'

SQLALCHEMY_DATABASE_URI = f"mysql://{SQLALCHEMY_USERNAME}:{SQLALCHEMY_PASSWORD}@{SQLALCHEMY_HOST}:{SQLALCHEMY_PORT}/{SQLALCHEMY_DATABASE}"

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 50  # seconds


BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'



spotify_url = "https://spotify23.p.rapidapi.com/recommendations/"
spotify_headers = {
	"X-RapidAPI-Key": "2422b29fa3msh1e80dd00b7dce64p1f37d3jsne4495c664901",
	"X-RapidAPI-Host": "spotify23.p.rapidapi.com"
}

print("Initializing SQLAlchemy")
# Initialize SQLAlchemy
Base = declarative_base()
print("SQLAlchemy initialized")

class Song(Base):
    __tablename__ = 'songs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    song_request_id = Column(String(255))
    email = Column(String(255))
    status = Column(String(20))
    spotify_id = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint('song_request_id', name='uq_song_request_id'),
    )


engine = create_engine(SQLALCHEMY_DATABASE_URI)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def db_update_status(song_request_id, status):
    session = Session()
    try:
        song = session.query(Song).filter_by(song_request_id=song_request_id).first()
        logging.debug({song, song_request_id, status})
        if song:
            song.status = status
            session.commit()
            print(f" [DB] Updated status of song {song_request_id} to {status}")
        else:
            print(f" [DB] Song with ID {song_request_id} not found.")
    except Exception as e:
        print(f" [DB] Error occurred while updating status for song {song_request_id}: {e}")
        session.rollback() 
    finally:
        session.close()
 

def track_recommender(song_request_id, spotify_id):
    querystring = {"limit":"5","seed_tracks":spotify_id}

    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            response = requests.get(spotify_url, headers=spotify_headers, params=querystring, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response
            else:
                logging.warning(response.json())

        except Exception as e:
            print(f'Retry {retry_count + 1}/{MAX_RETRIES}: Error occurred: {e}')
            retry_count += 1
            sleep(RETRY_DELAY)
    else:
        print(f'Reached maximum retries ({MAX_RETRIES}). Request failed.')
        db_update_status(song_request_id, 'failed')
        return None


def email_body_creator(response):
    print("in body_creator")
    tracks = response['tracks']
    track_info = []
    for track in tracks:
        track_info.append(f"Name: {track['name']}\nArtist: {track['artists'][0]['name']}\nAlbum: {track['album']['name']}\n\n")

    tracks_text = '\n'.join(track_info)

    email_body = f"Here are some song recommendations for you:\n\n{tracks_text}"
    return email_body

def send_mail(recommender_respnse):
	return requests.post(
		"https://api.mailgun.net/v3/sandboxb8b05a380798427f9e0a9aa542a22cfa.mailgun.org/messages",
		auth=("api", MAIL_API_KEY),
		data={"from": "Spotify Recommender <raein@sandboxb8b05a380798427f9e0a9aa542a22cfa.mailgun.org>",
			"to": ["raeen.soltani@gmail.com"],
			"subject": "Here is Some Tracks, Just for You",
			"text": email_body_creator(recommender_respnse)})


def main():
    while True:
        session = Session()
        try:
            song = session.query(Song).filter_by(status='ready').first()
        except Exception as e:
            print(f" [DB] Error occurred while finding song with status ready {e}")
            session.rollback() 
        finally:
            session.close()

        if song is not None:
            recommended_tracks = track_recommender(song.song_request_id ,song.spotify_id)

            if (recommended_tracks is None):
                logging.warning('invalid response from track recommender service')
                continue

            logging.debug(recommended_tracks.json())

            mail_response = send_mail(recommended_tracks.json())

            logging.debug(mail_response.json())

            if mail_response.status_code == 200:
                print(' [*] Email sent successfully.')
                db_update_status(song.song_request_id, 'done')
            else:
                print(' [*] Email sent successfully.')
                db_update_status(song.song_request_id, 'failed')

        sleep(10)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
