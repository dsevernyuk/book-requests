from flask import Blueprint, jsonify, current_app, request
from datetime import datetime
import urllib.parse
import json
import pickle
from email_validator import validate_email, EmailNotValidError
from jsonschema import validate as json_validate, ValidationError

book_request = Blueprint('book_request', __name__)

REDIS_CLIENT_CONFIG_KEY = 'redis-client'
BOOK_REQUEST_SCHEMA = {
    'type': 'object',
    'properties': {
        'title': {
            'type': 'string',
        },
        'email': {
            'type': 'string',
        },
    },
    'required': ['title', 'email'],
}


def get_redis_client():
    return current_app.config[REDIS_CLIENT_CONFIG_KEY]


def generate_id(title, email):
    return urllib.parse.quote(title+email, safe='')    


def enquote_id(id):
    return urllib.parse.quote(id, safe='')    


@book_request.route('/', methods=['GET'])
def get_requests():
    all_requests =  get_redis_client().hgetall('requests')
    all_values = [pickle.loads(val) for val in all_requests.values()] 
    return jsonify(all_values)


@book_request.route('/<id>', methods=['GET'])
def get_request(id):
        val = get_redis_client().hget('requests', enquote_id(id))
        if val:
            return jsonify(pickle.loads(val))
        else:
            return jsonify({'error': f'Request with id \'{id}\' does not exists'}), 404


@book_request.route('/', methods=['POST'])
def add_request():
    payload = request.json

    try:
        json_validate(payload, schema=BOOK_REQUEST_SCHEMA)
    except ValidationError as e:
        return jsonify({'error': e.message}), 400

    user_email = payload.get('email')
    book_title = payload.get('title')

    if not get_redis_client().sismember('books', book_title):
        return jsonify({'error': f'Book with title \'{book_title}\' not in the library'}), 400

    try:
        validate_email(user_email)
    except EmailNotValidError as e:
        return jsonify({'error': f'User email \'{user_email}\' is invalid'}), 400

    request_id = generate_id(book_title, user_email)
    if get_redis_client().hexists('requests', request_id):
        return jsonify({'error': 'This request is already recorded'}), 400

    new_book_request = {
        'title': book_title,
        'email': user_email,
        'id': request_id,
        'timestamp': datetime.utcnow(),
    }
    get_redis_client().hset('requests', key=new_book_request['id'], value=pickle.dumps(new_book_request))

    return jsonify(new_book_request)


@book_request.route('/<id>', methods=['DELETE'])
def delete_request(id):
    val = get_redis_client().hdel('requests', enquote_id(id))
    if val:
        return '', 200
    else:
        return jsonify({'error': f'Request with id \'{id}\' does not exists'}), 404
