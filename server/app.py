import werkzeug
# Fix for newer werkzeug versions
if not hasattr(werkzeug.urls, 'url_quote'):
    werkzeug.urls.url_quote = werkzeug.urls.quote

from flask import Flask, request, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Hero, Power, HeroPower
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

# Initialize Flask-RESTful API
api = Api(app)

@app.route('/')
def index():
    return '<h1>Code challenge</h1>'

# GET /heroes


class Heroes(Resource):
    def get(self):
        heroes = Hero.query.all()
        return [hero.to_dict(only=('id', 'name', 'super_name')) for hero in heroes], 200

# GET /heroes/:id


class HeroById(Resource):
    def get(self, id):
        hero = db.session.get(Hero, id)
        if not hero:
            return {"error": "Hero not found"}, 404
        
        # Include hero_powers with power details
        return hero.to_dict(), 200

# GET /powers


class Powers(Resource):
    def get(self):
        powers = Power.query.all()
        return [power.to_dict(only=('id', 'name', 'description')) for power in powers], 200

# GET /powers/:id and PATCH /powers/:id


class PowerById(Resource):
    def get(self, id):
        power = db.session.get(Power, id)
        if not power:
            return {"error": "Power not found"}, 404
        return power.to_dict(only=('id', 'name', 'description')), 200
    
    def patch(self, id):
        power = db.session.get(Power, id)
        if not power:
            return {"error": "Power not found"}, 404
        
        data = request.get_json()
        
        # Only update description
        if 'description' in data:
            try:
                power.description = data['description']
                db.session.commit()
                return power.to_dict(only=('id', 'name', 'description')), 200
            except ValueError as e:
                db.session.rollback()
                return {"errors": ["validation errors"]}, 400
        
        return power.to_dict(only=('id', 'name', 'description')), 200

# POST /hero_powers


class HeroPowers(Resource):
    def post(self):
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ('strength', 'hero_id', 'power_id')):
            return {"errors": ["Missing required fields"]}, 400
        
        # Verify hero and power exist
        hero = db.session.get(Hero, data['hero_id'])
        power = db.session.get(Power, data['power_id'])
        
        if not hero or not power:
            return {"errors": ["Hero or Power not found"]}, 404
        
        # Create new HeroPower
        try:
            hero_power = HeroPower(
                strength=data['strength'],
                hero_id=data['hero_id'],
                power_id=data['power_id']
            )
            db.session.add(hero_power)
            db.session.commit()
            
            # Return with hero and power details
            return hero_power.to_dict(), 200
        except ValueError as e:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400

# Add resources to API
api.add_resource(Heroes, '/heroes')
api.add_resource(HeroById, '/heroes/<int:id>')
api.add_resource(Powers, '/powers')
api.add_resource(PowerById, '/powers/<int:id>')
api.add_resource(HeroPowers, '/hero_powers')

if __name__ == '__main__':
    app.run(port=5555, debug=True)