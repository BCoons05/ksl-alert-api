from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
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
    email = db.Column(db.String(), nullable = False)
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

class Car(db.Model):
    __tablename__ = "cars"
    id = db.Column(db.Integer, primary_key = True)
    year = db.Column(db.Integer)
    make = db.Column(db.String)
    model = db.Column(db.String)
    miles = db.Column(db.Integer)
    price = db.Column(db.Integer)
    link = db.Column(db.String)


    def __init__(self, year, make, model, miles, price, link):
        self.year = year
        self.make = make
        self.model = model
        self.miles = miles
        self.price = price
        self.link = link

class Avg_price(db.Model):
    __tablename__ = "average_price"
    id = db.Column(db.Integer, primary_key = True)
    average_price = db.Column(db.Integer)

    def __init__(self, average_price):
        self.average_price = average_price

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "email")

class AlertSchema(ma.Schema):
    class Meta:
        fields = ("id", "year_min", "year_max", "make", "model", "price_min", "price_max", "miles_min", "miles_max", "user_id")

class ResultSchema(ma.Schema):
    class Meta:
        fields = ("id", "year", "make", "model", "miles", "price", "link", "user_id")

class CarSchema(ma.Schema):
    class Meta:
        fields = ("id", "year", "make", "model", "miles", "price", "link")

#In case I want to save the averages
class PriceAverageSchema(ma.Schema):
    class Meta:
        fields = ("id", "average_price")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

alert_schema = AlertSchema()
alerts_schema = AlertSchema(many=True)

result_schema = ResultSchema()
results_schema = ResultSchema(many=True)

car_schema = CarSchema()
cars_schema = CarSchema(many=True)

average_schema = PriceAverageSchema()
averages_schema = PriceAverageSchema(many=True)

# CRUD

# GET
@app.route("/user/<email>", methods=["GET"])
def get_user(email):
    found_user = User.query.filter(User.email == email)
    # all_users = db.session.query(Alert).join(User).filter(User.id == Alert.user_id).all()
    userResult = user_schema.dump(found_user)

    if userResult:
        return jsonify(userResult)
    else:
        return jsonify("User not found")

#Get all users
@app.route("/users", methods=["GET"])
def get_users():
    all_users = User.query.all()
    usersResult = users_schema.dump(all_users)

    return jsonify(all_users)

#get alerts by user id
@app.route("/alerts/<id>", methods=["GET"])
def get_alerts(id):
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

#Search Results
@app.route("/search/<make>-<model>-<year_min>-<year_max>-<miles_min>-<miles_max>-<price_min>-<price_max>", methods=["GET"])
def get_search_results(make, model, year_min, year_max, miles_min, miles_max, price_min, price_max):
    search_results = db.session.query()\
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

#Search All Cars
@app.route("/search/<make>-<model>-<year_min>-<year_max>-<miles_min>-<miles_max>-<price_min>-<price_max>", methods=["GET"])
def get_search_cars(make, model, year_min, year_max, miles_min, miles_max, price_min, price_max):
    search_cars = db.session.query()\
        .filter(Car.make.like(make))\
        .filter(Car.model.like(model))\
        .filter(Car.year >= year_min)\
        .filter(Car.year <= year_max)\
        .filter(Car.miles >= miles_min)\
        .filter(Car.miles <= miles_max)\
        .filter(Car.price >= price_min)\
        .filter(Car.price <= price_max).all()
    searchCars = cars_schema.dump(search_cars)

    return jsonify(searchCars)

#Get average price 
@app.route("/results/miles/<make>-<model>-<year_min>-<year_max>", methods=["GET"])
def get_average_price(make, model, year_min, year_max):
    average_price = db.session.query(func.avg(Result.price).label('average'))\
        .filter(Result.make.like(make))\
        .filter(Result.model.like(model))\
        .filter(Result.year >= year_min)\
        .filter(Result.year <= year_max).all()
    
    price_str = str(average_price[0][0])

    return price_str[0 : price_str.index('.')]


#Get average miles 
@app.route("/results/price/<make>-<model>-<year_min>-<year_max>", methods=["GET"])
def get_average_miles(make, model, year_min, year_max):
    average_miles = db.session.query(func.avg(Result.miles).label('average')).filter(
        Result.make.like(make)).filter(
        Result.model.like(model)).filter(
        Result.year >= year_min).filter(
        Result.year <= year_max
        ).all()

    miles_str = str(average_miles[0][0])

    return miles_str[0 : miles_str.index('.')]


# POST new user
@app.route("/user", methods=["POST"])
def add_user():
    name = request.json["name"]
    email = request.json["email"]

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
    miles = request.json["miles"]
    price = request.json["price"]
    link = request.json["link"]
    user_id = request.json["user_id"]

    new_result = Result(year, make, model, miles, price, link, user_id)

    db.session.add(new_result)
    db.session.commit()

    result = Result.query.get(new_result.user_id)
    return alert_schema.jsonify(result)

# POST new car
@app.route("/car", methods=["POST"])
def add_car():
    year = request.json["year"]
    make = request.json["make"]
    model = request.json["model"]
    miles = request.json["miles"]
    price = request.json["price"]
    link = request.json["link"]

    new_car = Car(year, make, model, miles, price, link)

    db.session.add(new_car)
    db.session.commit()

    car = Car.query.get(new_car.model)
    return alert_schema.jsonify(car)

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
def delete_result(id):
    result = Result.query.get(id)
    db.session.delete(result)
    db.session.commit()

    return jsonify("Result Deleted and stuff")

# DELETE car
@app.route("/car/<id>", methods=["DELETE"])
def delete_resultt(id):
    car = Car.query.get(id)
    db.session.delete(car)
    db.session.commit()

    return jsonify("Car Deleted and stuff")

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