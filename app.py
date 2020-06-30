from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
from environs import Env
import os

# https://ksl-alerts-user-api.herokuapp.coms/search/Toyota-Sienna-1990-2017-50-250000-50-200000

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
    name = db.Column(db.String, nullable = False)
    email = db.Column(db.String, nullable = False)
    results = db.relationship('Result')
    alerts = db.relationship('Alert')

    def __init__(self, name, email):
        self.name = name
        self.email = email

class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key = True)
    year_min = db.Column(db.Integer)
    year_max = db.Column(db.Integer)
    make = db.Column(db.String)
    model = db.Column(db.String)
    price_min = db.Column(db.Integer)
    price_max = db.Column(db.Integer)
    miles_min = db.Column(db.Integer)
    miles_max = db.Column(db.Integer)
    deviation = db.Column(db.Integer)
    # user_id = db.Column(db.Integer())
    # only partially working
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="alerts")

    def __init__(self, year_min, year_max, make, model, price_min, price_max, miles_min, miles_max, deviation, user_id):
        self.year_min = year_min
        self.year_max = year_max
        self.make = make
        self.model = model
        self.price_min = price_min
        self.price_max = price_max
        self.miles_min = miles_min
        self.miles_max = miles_max
        self.deviation = deviation
        self.user_id = user_id

class Result(db.Model):
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key = True)
    year = db.Column(db.Integer)
    make = db.Column(db.String)
    model = db.Column(db.String)
    miles = db.Column(db.Integer)
    price = db.Column(db.Integer)
    link = db.Column(db.String)
    # user_id = db.Column(db.Integer)
    # not working right
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="results")

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
        fields = ("id", "name", "email")

class AlertSchema(ma.Schema):
    class Meta:
        fields = ("id", "year_min", "year_max", "make", "model", "price_min", "price_max", "miles_min", "miles_max", "user_id")

class ResultSchema(ma.Schema):
    class Meta:
        fields = ("id", "year", "make", "model", "price", "miles", "link", "user_id")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

alert_schema = AlertSchema()
alerts_schema = AlertSchema(many=True)

result_schema = ResultSchema()
results_schema = ResultSchema(many=True)

# CRUD

# GET
# GET user by email TODO not working but need to change this to tokens
@app.route("/user/<userEmail>", methods=["GET"])
def get_user(userEmail):
    found_user = User.query.filter(User.email.like(userEmail)).all()
    # all_users = db.session.query(Alert).join(User).filter(User.id == Alert.user_id).all()
    userResult = user_schema.dump(found_user)

    if userResult:
        return jsonify(userResult)
    else:
        return jsonify(userResult)

#Get all users
@app.route("/users", methods=["GET"])
def get_users():
    all_users = User.query.all()
    usersResult = users_schema.dump(all_users)

    return jsonify(usersResult)

#Get all alerts
@app.route("/alerts", methods=["GET"])
def get_alerts():
    all_alerts = Alert.query.all()
    alertResult = alerts_schema.dump(all_alerts)

    return jsonify(alertResult)

#get alerts by user id
@app.route("/alerts/<id>", methods=["GET"])
def get_alerts_by_id(id):
    all_alerts = Alert.query.filter(Alert.user_id == id).all()
    alertResult = alerts_schema.dump(all_alerts)

    return jsonify(alertResult)

#Get all results
@app.route("/results", methods=["GET"])
def get_results():
    all_results = Result.query.all()
    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)

#Get results by user id
@app.route("/results/<id>", methods=["GET"])
def get_results_by_id(id):
    all_results = Result.query.filter(Result.user_id == id).all()
    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)

#Search
@app.route("/results/search/<make>-<model>-yearRange=<year_min>-<year_max>-milesRange=<price_min>-<price_max>-priceRange=<miles_min>-<miles_max>", methods=["GET"])
def get_search_results(make, model, year_min, year_max, miles_min, miles_max, price_min, price_max):
    search_results = Result.query\
        .filter(Result.make.like(make))\
        .filter(Result.model.like(model))\
        .filter(Result.year >= year_min)\
        .filter(Result.year <= year_max)\
        .filter(Result.miles >= miles_min)\
        .filter(Result.miles <= miles_max)\
        .filter(Result.price >= price_min)\
        .filter(Result.price <= price_max).all()
    searchResult = results_schema.dump(search_results)

    return jsonify(searchResult)

#Get average price 
@app.route("/results/price/<make>-<model>-<year_min>-<year_max>", methods=["GET"])
def get_average_price(make, model, year_min, year_max):
    average_price = db.session.query(func.avg(Result.price).label('average'))\
        .filter(Result.make.like(make))\
        .filter(Result.model.like(model))\
        .filter(Result.year >= year_min)\
        .filter(Result.year <= year_max).all()
    
    return jsonify({"averagePrice": average_price[0][0]})


#Get average miles 
@app.route("/results/miles/<make>-<model>-<year_min>-<year_max>", methods=["GET"])
def get_average_miles(make, model, year_min, year_max):
    average_miles = db.session.query(func.avg(Result.miles).label('average')).filter(
        Result.make.like(make)).filter(
        Result.model.like(model)).filter(
        Result.year >= year_min).filter(
        Result.year <= year_max
        ).all()

    return jsonify({"averageMiles": average_miles[0][0]})

# POST new user
@app.route("/user", methods=["POST"])
def add_user():
    name = request.json["name"]
    email = request.json["email"]

    new_user = User(name, email)

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
    deviation = request.json["deviation"]
    user_id = request.json["user_id"]

    new_alert = Alert(year_min, year_max, make, model, price_min, price_max, miles_min, miles_max, deviation, user_id)

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
# @app.route("/alert/<id>", methods=["PATCH"])
# def delete_alert(id):
#     alert = Alert.query.get(id)

#     new_alert = request.json["alert"]

#     todo.done = new_car

#     db.session.commit()
#     return car.jsonify(alert)

# DELETE alert
@app.route("/alert/<id>", methods=["DELETE"])
def delete_alert(id):
    alert = Alert.query.get(id)
    db.session.delete(alert)
    db.session.commit()

    return jsonify("Alert Deleted and stuff")

# DELETE result
@app.route("/result/<id>", methods=["DELETE"])
def result_resultt(id):
    result = Result.query.get(id)
    db.session.delete(result)
    db.session.commit()

    return jsonify("Result Deleted and stuff")

# DELETE user
@app.route("/user/<id>", methods=["DELETE"])
def delete_user(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()

    return jsonify("User Deleted and stuff")

# @app.route("/user/<id>", methods=["GET"])
# def find_user(name):
#     # user = User.query.get(name)
#     all_users = User.query.all()
#     userResult = users_schema.dump(user)

#     return jsonify(userResult)


if __name__ == "__main__":
    app.debug = True
    app.run()