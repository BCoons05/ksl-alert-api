from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, text, or_
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
from environs import Env
from DateTime import DateTime
import os
import json


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
    # Phone number for alerts
    daPass = db.Column(db.String(), nullable = False)
    results = db.relationship('Result', backref='user', lazy=True)
    alerts = db.relationship('Alert', backref='user', lazy=True)

    def __init__(self, name, email, daPass):
        self.name = name
        self.email = email
        # Phone
        self.daPass = daPass


# This is used to store all cars from KSL
class Car(db.Model):
    __tablename__ = "cars"
    id = db.Column(db.Integer, primary_key = True)
    year = db.Column(db.Integer, nullable = False)
    make = db.Column(db.String, nullable = False)
    model = db.Column(db.String, nullable = False)
    trim = db.Column(db.String)
    miles = db.Column(db.Integer, nullable = False)
    price = db.Column(db.Integer, nullable = False)
    link = db.Column(db.String, nullable = False)
    vin = db.Column(db.String, nullable = False)
    liters = db.Column(db.String)
    cylinders = db.Column(db.Integer, nullable = False)
    drive = db.Column(db.String)
    doors = db.Column(db.Integer)
    fuel = db.Column(db.String)
    seller = db.Column(db.String, nullable = False)


    def __init__(self, year, make, model, trim, miles, price, link, vin, liters, cylinders, drive, doors, fuel, seller):
        self.year = year
        self.make = make
        self.model = model
        self.trim = trim
        self.miles = miles
        self.price = price
        self.link = link
        self.vin = vin
        self.liters = liters
        self.cylinders = cylinders
        self.drive = drive
        self.doors = doors
        self.fuel = fuel
        self.seller = seller


# A user's alert
# TODO Do I need price and miles min and max? We are going to use the averages or ML for price and miles ...
class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key = True)
    year_min = db.Column(db.Integer)
    year_max = db.Column(db.Integer)
    make = db.Column(db.String)
    model = db.Column(db.String)
    trim = db.Column(db.String)
    price_min = db.Column(db.Integer)
    price_max = db.Column(db.Integer)
    miles_min = db.Column(db.Integer)
    miles_max = db.Column(db.Integer)
    deviation = db.Column(db.Integer)
    liters = db.Column(db.String)
    cylinders = db.Column(db.Integer, nullable = False)
    drive = db.Column(db.String)
    doors = db.Column(db.Integer)
    fuel = db.Column(db.String)
    seller = db.Column(db.String, nullable = False)
    # created = db.Column()
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # user = db.relationship("User", back_populates="alerts")
    results = db.relationship('Result', backref='alert', lazy=True)

    def __init__(self, year_min, year_max, make, model, trim, price_min, price_max, miles_min, miles_max, deviation, liters, cylinders, drive, doors, fuel, seller, user_id):
        self.year_min = year_min
        self.year_max = year_max
        self.make = make
        self.model = model
        self.trim = trim
        self.price_min = price_min
        self.price_max = price_max
        self.miles_min = miles_min
        self.miles_max = miles_max
        self.deviation = deviation
        self.liters = liters
        self.cylinders = cylinders
        self.drive = drive
        self.doors = doors
        self.fuel = fuel
        self.seller = seller
        self.user_id = user_id


# This stores any cars that match an alert. related to user and alert.
class Result(db.Model):
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key = True)
    year = db.Column(db.Integer)
    make = db.Column(db.String)
    model = db.Column(db.String)
    trim = db.Column(db.String)
    miles = db.Column(db.Integer)
    price = db.Column(db.Integer)
    link = db.Column(db.String)
    vin = db.Column(db.String, nullable = False)
    liters = db.Column(db.String)
    cylinders = db.Column(db.Integer, nullable = False)
    drive = db.Column(db.String)
    doors = db.Column(db.Integer)
    fuel = db.Column(db.String)
    seller = db.Column(db.String, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'))
    # user = db.relationship("User", back_populates="results")
    # alert = db.relationship("Alert", back_populates="results")

    def __init__(self, year, make, model, trim, miles, price, link, vin, liters, cylinders, drive, doors, fuel, seller, user_id, alert_id):
        self.year = year
        self.make = make
        self.model = model
        self.trim = trim
        self.miles = miles
        self.price = price
        self.link = link
        self.vin = vin
        self.liters = liters
        self.cylinders = cylinders
        self.drive = drive
        self.doors = doors
        self.fuel = fuel
        self.seller = seller
        self.user_id = user_id
        self.alert_id = alert_id


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "email", "daPass")


class AlertSchema(ma.Schema):
    class Meta:
        fields = ("id", "year_min", "year_max", "make", "model", "trim", "price_min", "price_max", "miles_min", "miles_max", "deviation", "liters", "cylinders", "drive", "doors", "fuel", "seller", "user_id")


class ResultSchema(ma.Schema):
    class Meta:
        fields = ("id", "year", "make", "model", "trim", "miles", "price", "link", "vin", "liters", "cylinders", "drive", "doors", "fuel", "seller", "user_id", "alert_id")


class CarSchema(ma.Schema):
    class Meta:
        fields = ("id", "year", "make", "model", "trim", "miles", "price", "link", "vin", "liters", "cylinders", "drive", "doors", "fuel", "seller")


user_schema = UserSchema()
users_schema = UserSchema(many=True)

alert_schema = AlertSchema()
alerts_schema = AlertSchema(many=True)

result_schema = ResultSchema()
results_schema = ResultSchema(many=True)

car_schema = CarSchema()
cars_schema = CarSchema(many=True)


# CRUD
# TODO Need to update all searches with liters, engine, cylinders, drive, doors, seller
# may need different routes depending on which params are passed. 


#Get all users
@app.route("/users", methods=["GET"])
def get_users():
    all_users = User.query.all()
    usersResult = users_schema.dump(all_users)

    return jsonify(usersResult)


# get all alerts
@app.route("/alerts", methods=["GET"])
def get_alerts():
    all_alerts = Alert.query.all()
    alertsResult = alerts_schema.dump(all_alerts)

    return jsonify(alertsResult)


#get alerts by user id
@app.route("/alerts/<int:id>", methods=["GET"])
def get_alerts_by_id(id):
    all_alerts = Alert.query.filter(Alert.user_id == id).all()
    alertResult = alerts_schema.dump(all_alerts)

    return jsonify(alertResult)


#Get all results for all users
@app.route("/results", methods=["GET"])
def get_results():
    all_results = Result.query.all()
    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)


#Get all cars 
@app.route("/cars", methods=["GET"])
def get_cars():
    all_cars = Car.query.all()
    carResult = cars_schema.dump(all_cars)

    return jsonify(carResult)


#Get results by user id
@app.route("/user_results/<int:id>", methods=["GET"])
def get_results_by_user_id(id):
    all_results = Result.query.filter(Result.user_id == id).all()
    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)


#Get results by alert id
@app.route("/alert_results/<int:id>", methods=["GET"])
def get_results_by_alert_id(id):
    all_results = Result.query.filter(Result.alert_id == id).all()
    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)


#Search all alert Results
# This will get all results that match a search query. May not use it. 
@app.route("/search/results/<make>-<model>-<int:year_min>-<int:year_max>-<int:miles_min>-<int:miles_max>-<int:price_min>-<int:price_max>", methods=["GET"])
def get_search_results(make, model, year_min, year_max, miles_min, miles_max, price_min, price_max):
    search_results = db.session.query(Result)\
        .filter(Result.make.like(make),\
        Result.model.like(model),\
        Result.year >= year_min,\
        Result.year <= year_max,\
        Result.miles >= miles_min,\
        Result.miles <= miles_max,\
        Result.price >= price_min,\
        Result.price <= price_max).all()

    searchResult = results_schema.dump(search_results)

    return jsonify(searchResult)


#Search All Cars
# Searches all cars in the db using given query. Need this for the Chrome extension
# Make and Model need to be titleized currently.
@app.route("/search/<make>-<model>-<int:year_min>-<int:year_max>-<int:miles_min>-<int:miles_max>-<int:price_min>-<int:price_max>", methods=["GET"])
def get_search_cars(make, model, year_min, year_max, miles_min, miles_max, price_min, price_max):
    search_cars = db.session.query(Car).filter(\
    # search_cars = Car.query.filter(\
    Car.make.like(make),\
    Car.model.like(model),\
    Car.year >= year_min,\
    Car.year <= year_max,\
    Car.miles >= miles_min,\
    Car.miles <= miles_max,\
    Car.price >= price_min,\
    Car.price <= price_max
    ).all()

    searchCars = cars_schema.dump(search_cars)

    return jsonify(searchCars)


#Get average price
@app.route("/cars/price/<make>-<model>-<int:year_min>-<int:year_max>", methods=["GET"])
def get_average_price(make, model, year_min, year_max):
    average_price = db.session.query(func.avg(Car.price).label('average'))\
        .filter(Car.make.like(make),\
        Car.model.like(model),\
        Car.year >= year_min,\
        Car.year <= year_max).all()
    
    if average_price[0][0]:
        return jsonify({
            'avg_price': int(average_price[0][0])
        })
    else:
        return "not enough data"


#Get average miles 
@app.route("/cars/miles/<make>-<model>-<int:year_min>-<int:year_max>", methods=["GET"])
def get_average_miles(make, model, year_min, year_max):
    average_miles = db.session.query(func.avg(Car.miles).label('average'))\
        .filter(
        Car.make.like(make),\
        Car.model.like(model),\
        Car.year >= year_min,\
        Car.year <= year_max).all()

    if average_miles[0][0]:
        return jsonify({
            'avg_miles': int(average_miles[0][0])
        })
    else: 
        return "not enough data"


#Search Alerts
# When we scrape KSL, before we post a result, we will check for a matching alert here. If there is a match then create a result and send a message
@app.route("/alerts/<make>-<model>-<int:year>-<int:miles>-<int:price>", methods=["GET"])
def get_matching_alerts(make, model, year, miles, price):
    search_alerts = db.session.query(Alert)\
        .filter(Alert.make.like(make),\
        Alert.model.like(model),\
        Alert.year_min <= year,\
        Alert.year_max >= year,\
        Alert.miles_min <= miles,\
        Alert.miles_max >= miles,\
        Alert.price_min <= price,\
        Alert.price_max >= price
        ).all()
    searchAlerts = alerts_schema.dump(search_alerts)

    return jsonify(searchAlerts)

# POST Search Alerts
@app.route("/alert/search", methods=["POST"])
def check_alerts():
    year = request.json["year"]
    make = request.json["make"]
    model = request.json["model"]
    trim = request.json["trim"]
    miles = request.json["miles"]
    price = request.json["price"]
    link = request.json["link"]
    vin = request.json["vin"]
    liters = request.json["liters"]
    cylinders = request.json["cylinders"]
    drive = request.json["drive"]
    doors = request.json["doors"]
    fuel = request.json["fuel"]
    seller = request.json["seller"]

    search_alerts = db.session.query(Alert)\
        .filter(Alert.make.like(make),\
        Alert.model.like(model),\
        Alert.trim.like(trim),\
        Alert.year_min <= year,\
        Alert.year_max >= year,\
        Alert.miles_min <= miles,\
        Alert.miles_max >= miles,\
        Alert.price_min <= price,\
        Alert.price_max >= price,\
        # Alert.liters == liters,\
        # Alert.cylinders == cylinders,\
        # Alert.drive == drive,\
        # Alert.doors == doors,\
        # Alert.fuel == fuel,\
        # Alert.seller == seller,\
        or_(Alert.liters == liters, Alert.liters == "any"),\
        or_(Alert.cylinders == cylinders, str(Alert.cylinders) == "any"),\
        or_(Alert.drive == drive, Alert.drive == "any"),\
        or_(Alert.doors == doors, str(Alert.doors) == "any"),\
        or_(Alert.fuel == fuel, Alert.fuel == "any"),\
        or_(Alert.seller == seller, Alert.seller == "any")
        ).all()

    searchAlerts = alerts_schema.dump(search_alerts)

    return jsonify(searchAlerts)


# POST new user
@app.route("/user", methods=["POST"])
def add_user():
    name = request.json["name"]
    email = request.json["email"]
    daPass = request.json["daPass"]

    new_user = User(name, email, daPass)

    db.session.add(new_user)
    db.session.commit()

    # user = User.query.get(new_user.name)
    return user_schema.jsonify(new_user)


# POST new alert
@app.route("/alert", methods=["POST"])
def add_alert():
    year_min = request.json["year_min"]
    year_max = request.json["year_max"]
    make = request.json["make"]
    model = request.json["model"]
    trim = request.json["trim"]
    price_min = request.json["price_min"]
    price_max = request.json["price_max"]
    miles_min = request.json["miles_min"]
    miles_max = request.json["miles_max"]
    deviation = request.json["deviation"]
    liters = request.json["liters"]
    cylinders = request.json["cylinders"]
    drive = request.json["drive"]
    doors = request.json["doors"]
    fuel = request.json["fuel"]
    seller = request.json["seller"]
    user_id = request.json["user_id"]

    new_alert = Alert(year_min, year_max, make, model, trim, price_min, price_max, miles_min, miles_max, deviation, liters, cylinders, drive, doors, fuel, seller, user_id)

    db.session.add(new_alert)
    db.session.commit()

    # alert = Alert.query.get(new_alert.user_id)
    return alert_schema.jsonify(new_alert)


# POST new result
# If car matches an alert, then we will post that car as a result with the matching alert id
@app.route("/result", methods=["POST"])
def add_result():
    year = request.json["year"]
    make = request.json["make"]
    model = request.json["model"]
    trim = request.json["trim"]
    miles = request.json["miles"]
    price = request.json["price"]
    link = request.json["link"]
    vin = request.json["vin"]
    liters = request.json["liters"]
    cylinders = request.json["cylinders"]
    drive = request.json["drive"]
    doors = request.json["doors"]
    fuel = request.json["fuel"]
    seller = request.json["seller"]
    user_id = request.json["user_id"]
    alert_id = request.json["alert_id"]

    new_result = Result(year, make, model, trim, miles, price, link, vin, liters, cylinders, drive, doors, fuel, seller, user_id, alert_id)

    db.session.add(new_result)
    db.session.commit()

    return alert_schema.jsonify(new_result)


# POST new car
# to post all cars scraped from ksl
@app.route("/car", methods=["POST"])
def add_car():
    year = request.json["year"]
    make = request.json["make"]
    model = request.json["model"]
    trim = request.json["trim"]
    miles = request.json["miles"]
    price = request.json["price"]
    link = request.json["link"]
    vin = request.json["vin"]
    liters = request.json["liters"]
    cylinders = request.json["cylinders"]
    drive = request.json["drive"]
    doors = request.json["doors"]
    fuel = request.json["fuel"]
    seller = request.json["seller"]

    new_car = Car(year, make, model, trim, miles, price, link, vin, liters, cylinders, drive, doors, fuel, seller)

    db.session.add(new_car)
    db.session.commit()

    return alert_schema.jsonify(new_car)


# PUT/PATCH by ID -- TODO this will be to update an alert. Will need an update for user info too
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


if __name__ == "__main__":
    app.debug = True
    app.run()