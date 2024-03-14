import boto3
import pika
from sqlalchemy import create_engine, Column, String, Integer, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys, os
import logging
import requests
logging.basicConfig(level=logging.INFO)


SQLALCHEMY_USERNAME = 'base-user'
SQLALCHEMY_PASSWORD = '9!dN$9GA6#ZobYEKFTAER2MK'
SQLALCHEMY_HOST = '2a599e2f061246909bc828e6bd4c37b3.db.arvandbaas.ir'
SQLALCHEMY_PORT = '3306'
SQLALCHEMY_DATABASE = 'default'

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

shazam_url = "https://shazam-api-free.p.rapidapi.com/shazam/recognize/"
shazam_headers = {
	"X-RapidAPI-Key": "2422b29fa3msh1e80dd00b7dce64p1f37d3jsne4495c664901",
	"X-RapidAPI-Host": "shazam-api-free.p.rapidapi.com"
}


try:
   s3 = boto3.resource(
       's3',
       endpoint_url=S3_ENDPOINT_URL,
       aws_access_key_id= S3_ACCESS_KEY_ID,
       aws_secret_access_key= S3_SECRET_ACCESS_KEY
   )
except Exception as exc:
   logging.info(exc)

def dbstatup(song_request_id, status):
    pass

def spotifyreq(track_name):
    pass

def shazamreq(song_request_id):
        local_file_path = f'./temp/{song_request_id}.mp3'
        files = {'upload_file': open(local_file_path, 'rb')}
        response = requests.post(shazam_url, files=files, headers=shazam_headers)
        if response.status_code == 200:
            pass
        else:
            dbstatup(song_request_id, 'failed')



LOCAL_DIRECTORY = './temp/'

def songproc(song_request_id):
    try:
        os.makedirs(LOCAL_DIRECTORY, exist_ok=True)
        local_file_path = os.path.join(LOCAL_DIRECTORY, song_request_id + ".mp3")

        s3.Bucket(S3_BUCKET_NAME).download_file(str(song_request_id), local_file_path)
        print(' [*] File downloaded successfully.')

        shazamrequest(song_request_id)


    except Exception as e:
        print(e)  # need to handle this later



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
        songproccessor(song_request_id= body.decode('utf-8'))

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

