from flask import Flask, request, jsonify
import boto3
import pika
from sqlalchemy import create_engine, Column, String, Integer, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
import logging

app = Flask(__name__)
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

print("Initializing SQLAlchemy")

# Initialize SQLAlchemy
Base = declarative_base()

print("SQLAlchemy initialized")

try:
   s3 = boto3.resource(
       's3',
       endpoint_url=S3_ENDPOINT_URL,
       aws_access_key_id= S3_ACCESS_KEY_ID,
       aws_secret_access_key= S3_SECRET_ACCESS_KEY
   )
except Exception as exc:
   logging.info(exc)

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

@app.route('/upload', methods=['POST'])
def upload_file():
    user_email = request.form['email']
    desired_file = request.files['file']

    # Generate SongID
    song_id = str(uuid.uuid4())

    # Add Song to S3
    try:
        s3.Bucket(S3_BUCKET_NAME).upload_fileobj(desired_file, song_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Publish song_id to RabbitMQ for further processing
    channel.basic_publish(exchange='', routing_key='songs', body=song_id)

    # Add entry to SQL database
    session = Session()
    new_song = Song(song_request_id=song_id, status='pending', email=user_email)
    session.add(new_song)
    session.commit()
    session.close()

    return jsonify({'song_id': song_id}), 200

if __name__ == '__main__':
    app.run(debug=True)