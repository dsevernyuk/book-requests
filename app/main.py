from flask import Flask
import redis

from book_request import book_request, REDIS_CLIENT_CONFIG_KEY

app = Flask(__name__)
app.register_blueprint(book_request, url_prefix='/request')

redis_client = redis.StrictRedis(host='redis-server', port=6379, db=0)
app.config[REDIS_CLIENT_CONFIG_KEY] = redis_client


if __name__ == '__main__':

    # Seeding book list since it won't be possible to add book request without books
    books = ['Title 1', 'Title 2']
    redis_client.sadd('books', *books)

    app.run(host='0.0.0.0', port=5000, debug=True)
