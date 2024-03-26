import boto3
import pika
from sqlalchemy import create_engine, Column, String, Integer, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys, os
from time import sleep
import logging
import requests
logging.basicConfig(level=logging.DEBUG)


SQLALCHEMY_USERNAME = 'root'
SQLALCHEMY_PASSWORD = 'sPnKe8MyZzOCAR7uT0Usny0e'
SQLALCHEMY_HOST = 'everest.liara.cloud'
SQLALCHEMY_PORT = '31531'
SQLALCHEMY_DATABASE = 'lucid_sutherland'

SQLALCHEMY_DATABASE_URI = f"mysql://{SQLALCHEMY_USERNAME}:{SQLALCHEMY_PASSWORD}@{SQLALCHEMY_HOST}:{SQLALCHEMY_PORT}/{SQLALCHEMY_DATABASE}"

S3_ENDPOINT_URL = 'https://shahriar-s3.s3.ir-tbz-sh1.arvanstorage.ir'
S3_ACCESS_KEY_ID = 'e09e5cf1-2b7b-4bb0-8c4a-0bc5643ca4a3'
S3_SECRET_ACCESS_KEY = 'b21709d6da82b6023668066c67c593e20d20e1bf223f1e3746a447033014446c'
S3_BUCKET_NAME = 'songs'

RABBITMQ_HOST = 'fly-01.rmq.cloudamqp.com'
RABBITMQ_PORT = '5672'
RABBITMQ_USERNAME = 'skcomluz'
RABBITMQ_PASSWORD = '1wUvroILOWyLzVp9WYXxtvoUMfcps1qN'
RABBITMQ_VHOST = 'skcomluz'

LOCAL_DIRECTORY = './temp/'

BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 50  # seconds


shazam_url = "https://shazam-api-free.p.rapidapi.com/shazam/recognize/"
shazam_headers = {
	"X-RapidAPI-Key": "2422b29fa3msh1e80dd00b7dce64p1f37d3jsne4495c664901",
	"X-RapidAPI-Host": "shazam-api-free.p.rapidapi.com"
}

spotify_url = "https://spotify23.p.rapidapi.com/search/"
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

try:
   s3 = boto3.resource(
       's3',
       endpoint_url=S3_ENDPOINT_URL,
       aws_access_key_id= S3_ACCESS_KEY_ID,
       aws_secret_access_key= S3_SECRET_ACCESS_KEY
   )
except Exception as exc:
   logging.info(exc)

def dbstat(song_request_id, status):
    session = Session()
    try:
        song = session.query(Song).filter_by(song_request_id=song_request_id).first()
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

def dbidupdate(song_request_id, spotify_id):
    session = Session()
    try:
        song = session.query(Song).filter_by(song_request_id=song_request_id).first()
        if song:
            song.spotify_id = spotify_id
            session.commit()
            print(f" [DB] Add Spotify id {spotify_id} for song {song_request_id}")
        else:
            print(f" [DB] Song with ID {song_request_id} not found.")
    except Exception as e:
        print(f" [DB] Error occurred while updating status for song {song_request_id}: {e}")
        session.rollback() 
    finally:
        session.close()


def spotifyreq(track_title, song_request_id):
    querystring = {"q":track_title,"type":"tracks","offset":"0","limit":"10","numberOfTopResults":"5"}
    
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            response = requests.get(spotify_url, headers=spotify_headers, params=querystring, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                spotify_id = response.json()['tracks']['items'][0]['data']['id']
                print(f' {GREEN}[s] Spotify ID: {spotify_id}{RESET}')
                dbidupdate(song_request_id, spotify_id)
                dbstat(song_request_id, 'ready')
                break 
            else:
                print(RED + response + RESET)
                dbstat(song_request_id, 'failed')
        except Exception as e:
            print(f'Retry {retry_count + 1}/{MAX_RETRIES}: Error occurred: {e}')
            retry_count += 1
            sleep(RETRY_DELAY)
    else:
        print(f'Reached maximum retries ({MAX_RETRIES}). Request failed.')
        dbstat(song_request_id, 'failed')

def shazamreq(song_request_id):
    local_file_path = f'./temp/{song_request_id}.mp3'
    files = {'upload_file': open(local_file_path, 'rb')}
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            response = requests.post(shazam_url, files=files, headers=shazam_headers, timeout=REQUEST_TIMEOUT)
            logging.debug(response.json())
            if response.status_code == 200:
                print(response)
                track_title = response.json()['track']['title']
                print(f' {BLUE}[s] Shazam: {track_title}.{RESET}')
                spotifyreq(track_title, song_request_id)
                break 
            else:
                print(RED + response + RESET)
                dbstat(song_request_id, 'failed')
        except Exception as e:
            print(f'Retry {retry_count + 1}/{MAX_RETRIES}: Error occurred: {e}')
            retry_count += 1
            sleep(RETRY_DELAY)
    else:
        print(f'Reached maximum retries ({MAX_RETRIES}). Request failed.')
        dbstat(song_request_id, 'failed')



def songproc(song_request_id):
    try:
        os.makedirs(LOCAL_DIRECTORY, exist_ok=True)
        local_file_path = os.path.join(LOCAL_DIRECTORY, song_request_id + ".mp3")
        s3.Bucket(S3_BUCKET_NAME).download_file(str(song_request_id), local_file_path)
        print(' [*] File downloaded successfully.')
        shazamreq(song_request_id)

    except Exception as e:
        print(e)
        dbstat(song_request_id, 'failed')

def main():
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD),
        socket_timeout=5
    )
    rabbitmq_connection = pika.BlockingConnection(parameters)
    channel = rabbitmq_connection.channel()
    channel.queue_declare(queue='songs')

    def callback(ch, method, properties, body):
        print(f" [x] Received {body}")
        songproc(song_request_id= body.decode('utf-8'))

    channel.basic_consume(queue='songs', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

