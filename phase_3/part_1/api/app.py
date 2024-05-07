from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import logging
import requests
import redis
import json

import os

app = Flask(__name__)
logging.basicConfig(level=logging.ERROR)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')

ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'elasticsearch')
ELASTICSEARCH_PORT = os.getenv('ELASTICSEARCH_PORT', '9200')

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
elk = Elasticsearch(f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")


imdb_url = "https://imdb146.p.rapidapi.com/v1/find/"


imdb_headers = {
	"X-RapidAPI-Key": "2422b29fa3msh1e80dd00b7dce64p1f37d3jsne4495c664901",
	"X-RapidAPI-Host": "imdb146.p.rapidapi.com"
}


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        if r.exists(query):
            print("Retrieving from Redis cache")
            return json.loads(r.get(query))
        else:
            resp = elk.search(index="movies", body={"query": {"match": {"Series_Title": query}}})
            if (not resp['hits']['hits']):
                response = requests.get(imdb_url, headers=imdb_headers, params={"query":query})
                if response.status_code != 200:
                    return jsonify({'error': 'Internal error, IMDB server'}), 500
                if response.json()['titleResults']['hasExactMatches'] is False:
                    return jsonify({'error': 'No result found!'}), 404
                else:
                    r.set(query, json.dumps(response.json()))
                    return response.json()
            else:
                r.set(query, json.dumps(resp))
                return resp
    else:
        return "No query provided"

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)