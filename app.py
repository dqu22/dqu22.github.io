import os
import pandas
import numpy as np
from flask import Flask, request, render_template

listings = {}
neighborhoods = {}
app = Flask(__name__)


# assumptions made:
# availability_30 is only affected by bookings. That is, if it's 0, then the airbnb is booked for the whole month
# all prices are per person (without accounting for decreasing marginal cost)
# neighborhoods are squares of length 1.2 degrees
# bookings are uniformly distributed throughout a period of time
# we only take bookings with greater than 75 reviews as to not take newer airbnbs which might skew the data
# assume price/bookings data follows a quadratic trend, which is common for more price/quantity relationships


def get_listings():
    df = pandas.read_csv('data/listings.csv').fillna(0)
    for i, r in df.iterrows():
        try:
            listings[r.id] = {'city': r.city, 'state': r.state, 'latitude': float(r.latitude), 'longitude': float(r.longitude), 'price': (float(r.price[1:]) / r.accommodates), 'numreviews': r.number_of_reviews, 'rating': r.review_scores_rating, 'neighborhood': r.neighbourhood_cleansed, 'bookings30': 30 - r.availability_30, 'bookingstotal': 365 - r.availability_365}
            neighborhoods[r.neighbourhood_cleansed] += 1;
        except:
            pass

def find_neighborhood(longitude, latitude):
    for k, v in listings.items():
        if abs(v['longitude'] - longitude) < 0.6 and abs(v['latitude'] - latitude) < 0.6:
            return v['neighborhood']
    return("None")

def weekly_income(neighborhood):
    total = 0
    count = 0
    for k, v in listings.items():
        if v['neighborhood'] == neighborhood and v['rating'] != 0 and v['numreviews'] > 75:
            total += (v['price'] * v['bookings30'] / 30 * 7)
            count += 1
    return total / count

def maximize_bookings(neighborhood):
    xs = []
    ys = []
    for k, v in listings.items():
        if v['neighborhood'] == neighborhood and v['rating'] != 0 and v['numreviews'] > 75:
            xs.append(v['bookingstotal'])
            ys.append(v['price'])
    x = np.array(xs)
    y = np.array(ys)
    z = np.polyfit(x, y, 2)
    print(z)
    p = float(-z[1] / (2 * z[0]))
    return (p, z[2] + z[1] * p + z[0] * p * p)

def oops(s):
    return render_template("oops.html", s=s)

@app.route("/")
def index():
    return render_template('index.html', neighborhoods=neighborhoods)

@app.route('/trends/<int:id>')
def get_trend(id):
    array = []
    if id == 1:
        legend = 'Price vs. Rating'
        for k, v in listings.items():
            if v['rating'] != 0 and v['numreviews'] > 75:
                array.append({'c1': v['rating'], 'c2': v['price']})
    if id == 2:
        legend = 'Price vs. Num Bookings'
        for k, v in listings.items():
            if v['rating'] != 0 and v['numreviews'] > 75:
                array.append({'c1': v['bookingstotal'], 'c2': v['price']})

    if id == 3:
        legend = 'Num Bookings vs. Rating'
        for k, v in listings.items():
            if v['rating'] != 0 and v['numreviews'] > 75:
                array.append({'c1': v['bookingstotal'], 'c2': v['rating']})
    return render_template('chart.html', legend=legend, array=array)

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return oops("You shouldn't be here!")
    longitude = float(request.form['long'])
    latitude = float(request.form['lat'])
    print(longitude, latitude)
    n = find_neighborhood(longitude, latitude)
    if n == "None":
        return oops("Neighborhood not found")
    income = weekly_income(n)
    price, bookings = maximize_bookings(n)
    return render_template('searched.html', income=income, price=price, bookings=bookings)

if __name__ == "__main__":
    get_listings()
    app.run()
