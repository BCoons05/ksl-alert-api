from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, text, or_
from flask_marshmallow import Marshmallow, fields
from flask_cors import CORS
from flask_heroku import Heroku
from environs import Env
import datetime
import os
import json


app = Flask(__name__)
CORS(app)
heroku = Heroku(app)

env = Env()
env.read_env()
DATABASE_URL = env("DATABASE_URL")

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL


db = SQLAlchemy(app)
ma = Marshmallow(app)


# TODO add hash or other security
class User(db.Model):
    """Class for new user.

    preferred contact can be "phone", "email", or "off".
    active will be set to True unless account is cancelled. 
    Deactivated should then be set to the date of cancellation.
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(), nullable = False)
    email = db.Column(db.String(), nullable = False)
    phone = db.Column(db.String())
    preferred_contact = db.Column(db.String, nullable = False)
    daPass = db.Column(db.String(), nullable = False)
    active = db.Column(db.Boolean, nullable = False)
    deactivated = db.Column(db.DateTime)
    results = db.relationship('Result', backref='user', lazy='joined')
    alerts = db.relationship('Alert', backref='user', lazy='joined')
    created_on = db.Column(db.DateTime, nullable = False)

    def __init__(self, name, email, phone, preferred_contact, daPass):
        self.name = name
        self.email = email
        self.phone = phone
        self.preferred_contact = preferred_contact
        self.daPass = daPass
        self.active = True
        self.created_on = datetime.datetime.now().strftime("%c")


# TODO add title to Car
class Car(db.Model):
    """
    Class for a car

    Used to store every car scraped
    """
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
    title = db.Column(db.String)
    seller = db.Column(db.String, nullable = False)
    created_on = db.Column(db.DateTime, nullable = False)


    def __init__(self, year, make, model, trim, miles, price, link, vin, liters, cylinders, drive, doors, fuel, title, seller):
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
        self.title = title
        self.seller = seller
        self.created_on = datetime.datetime.now().strftime("%c")



class Last_Scrape(db.Model):
    """
    Stores the car vins from the previous scrape.

    This is used like redis, to store the cars that we scraped last.
    We will check this table to see if we have a duplicate in the new
    scrape before adding the car to the db. Clear this table after each 
    use, then store the new scrape here.
    """
    id = db.Column(db.Integer, primary_key = True)
    vin = db.Column(db.String)

    def __init__(self, vin):
        self.vin = vin



# TODO Do I need price and miles min and max? We are going to use the averages or ML for price and miles ...
class Alert(db.Model):
    """
    Class for alerts

    used to create a new alert object to store in the db.
    Needs a user_id to the user that created the alert.
    Results will be joined if the result fits the parameters in this alert.
    """
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
    title = db.Column(db.String)
    seller = db.Column(db.String, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    results = db.relationship('Result', backref='alert', lazy='joined')
    active = db.Column(db.Boolean, nullable = False)
    created_on = db.Column(db.DateTime, nullable = False)

    def __init__(self, year_min, year_max, make, model, trim, price_min, price_max, miles_min, miles_max, deviation, liters, cylinders, drive, doors, fuel, title, seller, user_id):
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
        self.title = title
        self.seller = seller
        self.user_id = user_id
        self.active = True
        self.created_on = datetime.datetime.now().strftime("%c")


# This stores any cars that match an alert. related to user and alert.
class Result(db.Model):
    """
    Class for a result object

    Used to add a result to db. Holds the user id, alert id, and car id.
    User id is the user that created the alert. Alert id is the alert that 
    this result matched to. Car id is the car that matches the alert
    """
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key = True)
    car = db.relationship('Car', backref='result', lazy='joined')
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'))
    created_on = db.Column(db.DateTime, nullable = False)

    def __init__(self, car_id, user_id, alert_id):
        self.car_id = car_id
        self.user_id = user_id
        self.alert_id = alert_id
        self.created_on = datetime.datetime.now().strftime("%c")


class CarSchema(ma.Schema):
    class Meta:
        fields = ("id", "year", "make", "model", "trim", "miles", "price", "link", "vin", "liters", "cylinders", "drive", "doors", "fuel", "title", "seller", "created_on")

car_schema = CarSchema()
cars_schema = CarSchema(many=True)


class ResultSchema(ma.Schema):
    class Meta:
        fields = ("car", "car_id", "user_id", "alert_id", "created_on")
    car = ma.Nested(car_schema)

result_schema = ResultSchema()
results_schema = ResultSchema(many=True)

class AlertSchema(ma.Schema):
    class Meta:
        fields = ("id", "year_min", "year_max", "make", "model", "trim", "price_min", "price_max", "miles_min", "miles_max", "deviation", "liters", "cylinders", "drive", "doors", "fuel", "title", "seller", "user_id", "results", "created_on")
    results = ma.Nested(results_schema)

alert_schema = AlertSchema()
alerts_schema = AlertSchema(many=True)


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "email", "phone", "preferred_contact", "daPass", "alerts", "created_on")
    alerts = ma.Nested(alerts_schema)

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class Last_Scrape_Schema(ma.Schema):
    class Meta:
        fields = ("id", "vin")

last_scrapes_schema = Last_Scrape_Schema(many = True)
last_scrape_schema = Last_Scrape_Schema()


@app.route("/users", methods=["GET"])
def get_users():
    """
    Gets all users
    """
    all_users = User.query.all()
    usersResult = users_schema.dump(all_users)

    return jsonify(usersResult)


@app.route("/users/<int:id>", methods=["GET"])
def get_user_by_id(id):
    """
    Gets all users that match the given id
    """
    all_users = User.query.filter(User.id == id).all()
    userResult = users_schema.dump(all_users)

    return jsonify(userResult)


@app.route("/alerts", methods=["GET"])
def get_alerts():
    """
    Gets all alerts
    """
    all_alerts = Alert.query.all()
    alertsResult = alerts_schema.dump(all_alerts)

    return jsonify(alertsResult)



@app.route("/alerts/<int:id>", methods=["GET"])
def get_alerts_by_id(id):
    """
    Gets all alerts that match the given id
    """
    all_alerts = Alert.query.filter(Alert.user_id == id).all()
    alertResult = alerts_schema.dump(all_alerts)

    return jsonify(alertResult)



@app.route("/results", methods=["GET"])
def get_results():
    """
    Gets all results for all users
    """
    all_results = Result.query.all()

    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)



@app.route("/cars", methods=["GET"])
def get_cars():
    """
    Gets all cars
    """
    all_cars = Car.query.all()
    carResult = cars_schema.dump(all_cars)

    return jsonify(carResult)


@app.route("/get-last-scrape", methods=["GET"])
def get_last_scrape():
    """
    Gets the vins from the last scrape
    used to check for duplicate listings
    Clears table after each get request
    """
    get_scrape = Last_Scrape.query.all()
    last_scrape = last_scrapes_schema.dump(get_scrape)
    db.session.query(Last_Scrape).delete()
    db.session.commit()

    return jsonify(last_scrape)


@app.route("/user_results/<int:id>", methods=["GET"])
def get_results_by_user_id(id):
    """
    Gets all results by user id
    """
    all_results = Result.query.filter(Result.user_id == id).all()
    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)


@app.route("/alert_results/<int:id>", methods=["GET"])
def get_results_by_alert_id(id):
    """
    Gets all results for a given alert id
    """
    all_results = Result.query.filter(Result.alert_id == id).all()
    resultResult = results_schema.dump(all_results)

    return jsonify(resultResult)


@app.route("/search/all-cars", methods=["POST"])
def search_cars():
    """
    Searches all cars in the db using given query. Need this for the Chrome extension
    """
    default = 'any'
    make = request.json["make"]
    model = request.json["model"]
    year_min = request.json["year_min"] or request.json["year"]
    year_max = request.json["year_max"] or request.json["year"]
    miles_min = request.json["miles_min"] or 1
    miles_max = request.json["miles_max"] or 999999
    price_min = request.json["price_min"] or 1
    price_max = request.json["price_max"] or 9999999
    trim = request.json["trim"] or default
    liters = request.json["liters"] or default
    cylinders = request.json["cylinders"] or 0
    drive = request.json["drive"] or default
    doors = request.json["doors"] or 0
    fuel = request.json["fuel"] or default
    title = request.json["title"] or default
    seller = request.json["seller"] or default

    search_cars = db.session.query(Car)\
        .filter(
        Car.make.lower() == make.lower(),\
        Car.model.lower() == model.lower(),\
        year_min <= Car.year,\
        year_max >= Car.year,\
        miles_min <= Car.miles,\
        miles_max >= Car.miles,\
        price_min <= Car.price,\
        price_max >= Car.price,\
        or_(Car.trim == trim, trim == default),\
        or_(Car.liters == liters, liters == default),\
        or_(cylinders == 0, cylinders == Car.cylinders),\
        or_(drive == default, drive == Car.drive),\
        or_(doors == 0, doors == Car.doors),\
        or_(fuel == default, fuel == Car.fuel),\
        or_(title == default, title == Car.title),\
        or_(seller == default, seller == Car.seller)
        ).all()

    searchCars = cars_schema.dump(search_cars)

    return jsonify(searchCars)


# TODO Make this a POST? Also need to incorporate trim, drive, transmission, etc
@app.route("/cars/price/<make>-<model>-<int:year_min>-<int:year_max>", methods=["GET"])
def get_average_price(make, model, year_min, year_max):
    """
    Get average price for given make, model, and year range
    """
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


# TODO make this a post? Also need to incorporate trim, drive, transmission, etc
@app.route("/cars/miles/<make>-<model>-<int:year_min>-<int:year_max>", methods=["GET"])
def get_average_miles(make, model, year_min, year_max):
    """
    Get average miles for given make, model, and year range
    """
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


@app.route("/alert/search", methods=["POST"])
def check_alerts():
    """
    POST Search Alerts
    When we scrape KSL, before we post a result, we will check for a matching alert here. 
    If there is a match then create a result and send a message
    """
    default = 'any'
    year = request.json["year"]
    make = request.json["make"]
    model = request.json["model"]
    trim = request.json["trim"]
    miles = request.json["miles"]
    price = request.json["price"]
    liters = request.json["liters"]
    cylinders = request.json["cylinders"]
    drive = request.json["drive"]
    doors = request.json["doors"]
    fuel = request.json["fuel"]
    title = request.json["title"]
    seller = request.json["seller"]
    link = request.json["link"]
    vin = request.json["vin"]

    search_alerts = db.session.query(Alert)\
        .filter(Alert.active == True,\
        Alert.make.like(make),\
        Alert.model.like(model),\
        or_(Alert.trim == default, trim == Alert.trim),\
        Alert.year_min <= year,\
        Alert.year_max >= year,\
        Alert.miles_min <= miles,\
        Alert.miles_max >= miles,\
        Alert.price_min <= price,\
        Alert.price_max >= price,\
        or_(Alert.liters == default, liters == Alert.liters),\
        or_(Alert.cylinders == 0, cylinders == Alert.cylinders),\
        or_(Alert.drive == default, drive == Alert.drive),\
        or_(Alert.doors == 0, doors == Alert.doors),\
        or_(Alert.fuel == default, fuel == Alert.fuel),\
        or_(Alert.title == default, title == Alert.title),\
        or_(Alert.seller == default, seller == Alert.seller)
        ).all()

    searchAlerts = alerts_schema.dump(search_alerts)

    if(len(searchAlerts) > 0):
        new_car = Car(year, make, model, trim, miles, price, link, vin, liters, cylinders, drive, doors, fuel, title, seller)
        added_car = add_car_from_search_route(new_car)

        for alert in searchAlerts:
            # 'Response' object has no attribute 'id'
            new_result = Result(added_car[0].id, alert.user_id, alert.alert_id)
            add_result_from_diff_route(new_result)

            user = get_user_by_id(alert.user_id)
            # TODO This is where we call the twilio stuff using user.phone
            print('Deal found. Texting {user.phone}')

    # return jsonify(searchAlerts)
    return 'Deal found. Texting {user.phone}'


@app.route("/user", methods=["POST"])
def add_user():
    """
    POST new user
    """
    name = request.json["name"]
    email = request.json["email"]
    phone = request.json["phone"]
    preferred_contact = request.json["preferred_contact"]
    daPass = request.json["daPass"]

    new_user = User(name, email, phone, preferred_contact, daPass)

    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user)


@app.route("/alert", methods=["POST"])
def add_alert():
    """
    POST new alert
    """
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
    title = request.json["title"]
    seller = request.json["seller"]
    user_id = request.json["user_id"]

    new_alert = Alert(year_min, year_max, make, model, trim, price_min, price_max, miles_min, miles_max, deviation, liters, cylinders, drive, doors, fuel, title, seller, user_id)

    db.session.add(new_alert)
    db.session.commit()

    return alert_schema.jsonify(new_alert)



@app.route("/result", methods=["POST"])
def add_result():
    """
    POST new result
    If car matches an alert, then we will post that car as a result with the matching alert id
    """
    user_id = request.json["user_id"]
    alert_id = request.json["alert_id"]
    car_id = request.json["car_id"]

    new_result = Result(car_id, user_id, alert_id)

    db.session.add(new_result)
    db.session.commit()

    return alert_schema.jsonify(new_result)


def add_result_from_diff_route(result):
    db.session.add(new_result)
    db.session.commit()

    return alert_schema.jsonify(new_result)



@app.route("/set-last", methods=["POST"])
def set_last():
    """
    This is used to store the vins from the last scrape.
    Need this to stop from posting duplicate cars.
    Post every vin here, because we will clear this table after every GET
    """
    vin = request.json["vin"]
    new_scrape = Last_Scrape(vin)
    db.session.add(new_scrape)
    db.session.commit()

    return last_scrape_schema.jsonify(new_scrape)


@app.route("/car", methods=["POST"])
def add_car():
    """
    POST new car
    to post all cars scraped from ksl
    """
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
    title = request.json["title"]
    seller = request.json["seller"]

    new_car = Car(year, make, model, trim, miles, price, link, vin, liters, cylinders, drive, doors, fuel, title, seller)

    db.session.add(new_car)
    db.session.commit()

    return car_schema.jsonify(new_car)


def add_car_from_search_route(car):
    db.session.add(car)
    db.session.commit()

    return car_schema.jsonify(car)


# PUT/PATCH by ID -- TODO need routes for user and alert
# @app.route("/alert/<id>", methods=["PATCH"])
# def delete_alert(id):
#     alert = Alert.query.get(id)

#     new_alert = request.json["alert"]

#     todo.done = new_car

#     db.session.commit()
#     return car.jsonify(alert)


@app.route("/alert/<id>", methods=["DELETE"])
def delete_alert(id):
    """
    DELETE alert with given id
    """
    alert = Alert.query.get(id)
    db.session.delete(alert)
    db.session.commit()

    return jsonify(f"Alert {alert.id} deleted")


@app.route("/result/<id>", methods=["DELETE"])
def delete_result(id):
    """
    DELETE result by given id
    """
    result = Result.query.get(id)
    db.session.delete(result)
    db.session.commit()

    return jsonify(f"Result {result.id} deleted")


@app.route("/car/<id>", methods=["DELETE"])
def delete_car(id):
    """
    DELETE car by given id
    """
    car = Car.query.get(id)
    db.session.delete(car)
    db.session.commit()

    return jsonify(f"Car {car.id} deleted")


@app.route("/user/<id>", methods=["DELETE"])
def delete_user(id):
    """
    DELETE user by given id
    """
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()

    return jsonify(f"User {user.id} deleted")


if __name__ == "__main__":
    app.debug = True
    app.run()