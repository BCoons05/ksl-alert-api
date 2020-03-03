from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
from environs import Env
import os


app = Flask(__name__)
CORS(app)
heroku = Heroku(app)

env = Env()
env.read_env()
DATABASE_URL = env("DATABASE_URL")

basedir = os.path.abspath(os.path.dirname(__file__))
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL


db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(), nullable = False)
    # Post works fine but wont return these values...
    # results = db.relationship('Result', backref='user')
    # alerts = db.relationship('Alert', backref='user')

    def __init__(self, name):
        self.name = name

class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key = True)
    year_min = db.Column(db.Integer())
    year_max = db.Column(db.Integer())
    make = db.Column(db.String())
    model = db.Column(db.String())
    price_min = db.Column(db.Integer())
    price_max = db.Column(db.Integer())
    miles_min = db.Column(db.Integer())
    miles_max = db.Column(db.Integer())
    user_id = db.Column(db.Integer())
    # only partially working
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, year_min, year_max, make, model, price_min, price_max, miles_min, miles_max, user_id):
        self.year_min = year_min
        self.year_max = year_max
        self.make = make
        self.model = model
        self.price_min = price_min
        self.price_max = price_max
        self.miles_min = miles_min
        self.miles_max = miles_max
        self.user_id = user_id

class Result(db.Model):
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key = True)
    year = db.Column(db.Integer())
    make = db.Column(db.String())
    model = db.Column(db.String())
    miles = db.Column(db.Integer())
    price = db.Column(db.Integer())
    link = db.Column(db.String)
    user_id = db.Column(db.Integer)
    # not working right
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, year, make, model, miles, price, link, user_id):
        self.year = year
        self.make = make
        self.model = model
        self.miles = miles
        self.price = price
        self.link = link
        self.user_id = user_id

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name")

class AlertSchema(ma.Schema):
    class Meta:
        fields = ("id", "year_min", "year_max", "make", "model", "price_min", "price_max", "miles_min", "miles_max", "user_id")

class ResultSchema(ma.Schema):
    class Meta:
        fields = ("id", "year", "make", "model", "price", "link", "user_id")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

alert_schema = AlertSchema()
alerts_schema = AlertSchema(many=True)

result_schema = ResultSchema()
results_schema = ResultSchema(many=True)

# CRUD

# GET
@app.route("/users", methods=["GET"])
def get_users():
    all_users = User.query.join(Result).all()
    userResult = users_schema.dump(all_users)

    return jsonify(userResult)

@app.route("/alerts", methods=["GET"])
def get_alerts():
    all_alerts = Alert.query.all()
    alertResult = alerts_schema.dump(all_alerts)

    return jsonify(alertResult)

@app.route("/results", methods=["GET"])
def get_results():
    all_results = Result.query.all()
    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)

# GET by ID


# POST new user
@app.route("/user", methods=["POST"])
def add_user():
    name = request.json["name"]

    new_user = User(name)

    db.session.add(new_user)
    db.session.commit()

    user = User.query.get(new_user.name)
    return user_schema.jsonify(user)


# POST new alert
@app.route("/alert", methods=["POST"])
def add_alert():
    year_min = request.json["year_min"]
    year_max = request.json["year_max"]
    make = request.json["make"]
    model = request.json["model"]
    price_min = request.json["price_min"]
    price_max = request.json["price_max"]
    miles_min = request.json["miles_min"]
    miles_max = request.json["miles_max"]
    user_id = request.json["user_id"]

    new_alert = Alert(year_min, year_max, make, model, price_min, price_max, miles_min, miles_max, user_id)

    db.session.add(new_alert)
    db.session.commit()

    alert = Alert.query.get(new_alert.user_id)
    return alert_schema.jsonify(alert)

# POST new result
@app.route("/result", methods=["POST"])
def add_result():
    year = request.json["year"]
    make = request.json["make"]
    model = request.json["model"]
    price = request.json["price"]
    miles = request.json["miles"]
    link = request.json["link"]
    user_id = request.json["user_id"]

    new_result = Result(year, make, model, price, miles, link, user_id)

    db.session.add(new_result)
    db.session.commit()

    result = Result.query.get(new_result.user_id)
    return alert_schema.jsonify(result)

# PUT/PATCH by ID -- Not sure what we would patch at the moment, I can update this if I find a use
# @app.route("/car/<id>", methods=["PATCH"])
# def update_car(id):
#     car = Car.query.get(id)

#     new_car = request.json["car"]

#     todo.done = new_car

#     db.session.commit()
#     return car.jsonify(car)

# DELETE -- Again I am not sure why we would delete a car... I can update this if I find a use
# @app.route("/todo/<id>", methods=["DELETE"])
# def delete_todo(id):
#     todo = Todo.query.get(id)
#     db.session.delete(todo)
#     db.session.commit()

#     return jsonify("Todo Deleted and stuff")


if __name__ == "__main__":
    app.debug = True
    app.run()