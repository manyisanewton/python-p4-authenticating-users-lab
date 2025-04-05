#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)

# Debug all incoming requests
@app.before_request
def log_request():
    print(f"Incoming request: {request.method} {request.path}")
    if request.method == 'POST':
        print(f"Request JSON: {request.get_json()}")

# Authentication Resources
class Login(Resource):
    def post(self):
        print("Received POST to /login")
        try:
            data = request.get_json()
            if not data or 'username' not in data:
                print("No username provided in request")
                return {'error': 'Username is required'}, 400
            
            username = data['username']
            print(f"Looking up user: {username}")
            user = User.query.filter_by(username=username).first()
            
            if user:
                session['user_id'] = user.id
                print(f"User found, set session['user_id'] = {user.id}")
                return user.to_dict(), 200
            else:
                print(f"User '{username}' not found in database")
                return {'error': 'User not found'}, 404
        except Exception as e:
            print(f"Error in Login: {str(e)}")
            return {'error': 'Internal server error'}, 500

class Logout(Resource):
    def delete(self):
        print("Received DELETE to /logout")
        session.pop('user_id', None)
        return '', 204

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        print(f"Checking session, user_id: {user_id}")
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                print(f"User found: {user.username}")
                return user.to_dict(), 200
            else:
                print(f"User ID {user_id} not found, clearing session")
                session.pop('user_id', None)
        print("No user_id in session, returning 401")
        return {}, 401

# Other Resources
class ClearSession(Resource):
    def delete(self):
        print("Received DELETE to /clear")
        session['page_views'] = None
        session['user_id'] = None
        return {}, 204

class IndexArticle(Resource):
    def get(self):
        print("Received GET to /articles")
        articles = [article.to_dict() for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):
    def get(self, id):
        print(f"Received GET to /articles/{id}")
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1
        print(f"Page views: {session['page_views']}")
        if session['page_views'] <= 3:
            article = Article.query.filter(Article.id == id).first()
            if article:
                return make_response(jsonify(article.to_dict()), 200)
            return {'error': 'Article not found'}, 404
        return {'message': 'Maximum pageview limit reached'}, 401

# Register Resources
api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')
api.add_resource(Login, '/login', '/login/')  # Handle both with and without slash
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(port=5555, debug=True)