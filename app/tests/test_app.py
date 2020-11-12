import fakeredis
import pytest
from datetime import datetime
import pickle

from app.main import app
from app.book_request import generate_id, REDIS_CLIENT_CONFIG_KEY

@pytest.fixture
def client():
    
    redis_client = fakeredis.FakeStrictRedis()
    app.config['redis-client'] = redis_client
    app.config['TESTING'] = True
    client = app.test_client()
    yield client


def setup_data(redis_client):
    books = ['Bestseller 1', 'Bestseller 2']
    redis_client.sadd('books', *books)
    
    entries = [
        {
            'title': 'Bestseller 1',
            'email': 'test@email.org',
            'timestamp': str(datetime.utcnow()),
        },
        {
            'title': 'Bestseller 2',
            'email': 'test@email2.edu',
            'timestamp': str(datetime.utcnow()),
        },
    ]
    
    for entry in entries:
        entry['id'] = generate_id(entry['title'], entry['email'])
        redis_client.hset('requests', entry['id'], pickle.dumps(entry))

    return entries


def test_get_all_requests(client):
    entries = setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])

    response = client.get('/request/')
    result = response.get_json()

    assert response.status_code == 200
    assert result
    assert len(result) == 2
    for index in range(len(result)):
        assert result[index] == entries[index]


def test_get_existing_request(client):
    entries = setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])

    response = client.get('/request/'+entries[1]['id'])
    result = response.get_json()

    assert response.status_code == 200
    assert result
    assert result == entries[1]


def test_get_notfound_request(client):
    setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])

    response = client.get('/request/unknown_id')
    result = response.get_json()

    assert response.status_code == 404
    assert 'error' in result


def test_post_request_success(client):
    setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])
    
    new_entry = {
        'title': 'Bestseller 1',
        'email': 'another@email.com',
    }
    response = client.post('/request/', json=new_entry)
    result = response.get_json()

    assert response.status_code == 200
    assert result
    assert result.get('title') == new_entry['title']
    assert result.get('email') == new_entry['email']
    assert result.get('id') is not None 
    assert result.get('timestamp') is not None


def test_post_request_error_missing_field(client):
    setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])
    
    new_entry = {
        'title': 'Bestseller 1',
    }
    response = client.post('/request/', json=new_entry)
    result = response.get_json()

    assert response.status_code == 400
    assert result
    assert 'error' in result
    assert 'email' in result['error']
    assert 'required' in result['error']


def test_post_request_error_book_notfound(client):
    setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])
    
    new_entry = {
        'title': 'New Book',
        'email': 'another@email',
    }
    response = client.post('/request/', json=new_entry)
    result = response.get_json()

    assert response.status_code == 400
    assert result
    assert 'error' in result
    assert new_entry['title'] in result['error']


def test_post_request_error_invalid_email(client):
    setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])
    
    new_entry = {
        'title': 'Bestseller 1',
        'email': 'another email',
    }
    response = client.post('/request/', json=new_entry)
    result = response.get_json()

    assert response.status_code == 400
    assert result
    assert 'error' in result
    assert new_entry['email'] in result['error']


def test_post_request_error_already_recorded(client):

    entries = setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])
    
    new_entry = {
        'title': entries[0]['title'],
        'email': entries[0]['email'],
    }

    response = client.post('/request/', json=new_entry)
    result = response.get_json()

    assert response.status_code == 400
    assert result
    assert 'error' in result
    assert 'already recorded' in result['error']


def test_delete_request_success(client):
    entries = setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])
    
    response = client.delete('/request/' + entries[0]['id'])
    result = response.get_json()

    assert response.status_code == 200


def test_delete_request_error(client):
    entries = setup_data(app.config[REDIS_CLIENT_CONFIG_KEY])
    
    response = client.delete('/request/unknown_id')
    result = response.get_json()

    assert response.status_code == 404
