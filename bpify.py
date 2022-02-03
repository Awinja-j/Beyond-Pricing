import uuid
from flask import Flask, request, jsonify, json, abort
from markets import MARKETS
from datetime import datetime, date
import requests


app = Flask(__name__)
listings_ = []


@app.route("/test_flask", methods=["GET", "POST"])
def test_flask():
    """Example to show how to use Flask and extract information from the incoming request.
    It is not intended to be the only way to do things with Flask, rather more a way to help you not spend too much time on Flask.
    
    Ref: http://flask.palletsprojects.com/en/1.1.x/

    Try to make those requests:
    curl "http://localhost:5000/test_flask?first=beyond&last=pricing"
    curl "http://localhost:5000/test_flask" -H "Content-Type: application/json" -X POST -d '{"first":"beyond", "last":"pricing"}' 
    
    """
    # This contains the method used to access the route, such as GET or POST, etc
    method = request.method

    # Query parameters
    # It is a dict like object
    # Ref: https://flask.palletsprojects.com/en/1.1.x/api/?highlight=args#flask.Request.args
    query_params = request.args
    query_params_serialized = ", ".join(f"{k}: {v}" for k, v in query_params.items())

    # Get the data as JSON directly
    # If the mimetype does not indicate JSON (application/json, see is_json), this returns None.
    # Ref: https://flask.palletsprojects.com/en/1.1.x/api/?highlight=get_json#flask.Request.get_json
    data_json = request.get_json()

    return jsonify(
        {
            "method": method,
            "query_params": query_params_serialized,
            "data_json": data_json,
        }
    )


@app.route("/markets")
def markets():
    return jsonify([market.to_dict() for market in MARKETS.get_all()])


@app.route("/listings", methods=["GET", "POST"])
def listings():
    if request.method == 'POST':
        request_data = request.get_json()
        title = None
        base_price = None
        currency = None
        market = None
        host_name = None
        date = None
        price = None

        if request_data:
            if 'title' in request_data:
                title = request_data['title']
            if 'base_price' in request_data:
                base_price = request_data['base_price']
            if 'currency' in request_data:
                currency = request_data['currency']
            if 'market' in request_data:
                market = request_data['market']
            if 'host_name' in request_data:
                host_name = request_data['host_name']
            if 'date' in request_data:
                date = request_data['date']
        listing = {
            'title': title,
            'base_price' : base_price,
            'currency': currency,
            'market': market,
            'host_name': host_name,
            'listing_id': uuid.uuid4().int,
            'date': date
        }
        if listing not in listings_:
            listings_.append(listing)
            return jsonify(listing), 201

    if request.method == 'GET':
        list_of_markets = []
        market = request.args.get('market')
        if market:
            m = (market.split(','))
            for i in m:
                for list in listings_:
                    if list['market'] == i:
                        list_of_markets.append(list)
            return jsonify({'list_of_markets': list_of_markets}), 200


        operator = ['base_price.e', 'base_price.gt', 'base_price.gte', 'base_price.lt', 'base_price.lte']

        for i in operator:
            if i in request.args:
                operator_ = i
                break

        base_price = request.args[operator_]
        currency = request.args.get('currency')

        base_price = int(base_price)

        if base_price and currency:
            for line in listings_:
                if operator_ == 'base_price.e':
                    if line['base_price'] == base_price and line['currency'] ==  currency:
                        list_of_markets.append(line)
                if operator_ == 'base_price.gt':
                    if line['base_price'] > base_price and line['currency'] ==  currency:
                        list_of_markets.append(line)
                if operator_ == 'base_price.gte':
                    if line['base_price'] >= base_price and line['currency'] ==  currency:
                        list_of_markets.append(line)
                if operator_ == 'base_price.lt':
                    if line['base_price'] < base_price and line['currency'] ==  currency:
                        list_of_markets.append(line)
                if operator_ == 'base_price.lte':
                    if line['base_price'] <= base_price and line['currency'] ==  currency:
                        list_of_markets.append(line)
            return jsonify({'list_of_markets': list_of_markets}),200
            

        if currency and not base_price:
            for list in listings_:
                if list['currency'] == currency:
                    list_of_markets.append(list)
        return jsonify({'list_of_markets': list_of_markets}), 200
        


@app.route("/listings/<int:id>", methods=["GET", "PUT", "DELETE"])
def listing(id):
    result = {}

    if request.method == 'GET':
        for line in listings_:
            if line.get('listing_id') == id:
                result = line
        return jsonify(result), 200

    if request.method == 'DELETE':
        for line in range(len(listings_)):
            if listings_[line]['listing_id'] == id:
                del listings_[line]
                break
        return jsonify({'DELETE': 'RESOURCE DELETED'}), 410
    
    if request.method == 'PUT':
        for line in listings_:
            if line.get('listing_id') == id:
                data = request.get_json()
                line.update(data)
        return jsonify({'UPDATED': 'RESOURCE UPDATED'}), 200

def is_weekend(d):
    return d.weekday() > 4
def is_wednesday(d):
    return d.weekday() == 2
def is_friday(d):
    return d.weekday() == 4

@app.route("/listings/<int:id>/calendar", methods=["GET"])
def listing_calendar(id):
    calendar_listings = []
    markets1 = ['paris', 'lisbon']
    market2 = 'san-francisco'
    currency = request.args.get('currency')
    price_list = []
    
    for line in listings_:
        if line['listing_id'] == id:
            calendar_listings.append(line)

    for market in calendar_listings:
        if not currency:
            currency = market['currency']
            base_price = int(market['base_price'])

        else:
            base_price = int(market['base_price'])
            convert_to = currency
            convert_from = market['currency']
            APP_ID = '2752093315864224a8dc365fac1209ec'
            url = 'https://openexchangerates.org/api/latest.json?app_id={}&base={}&symbols={}'.format(APP_ID, convert_from, convert_to)
            response = requests.get(url)
            data = response.json()
            base_price = data['rates'][convert_to]
    
        market_date = datetime.strptime(market['date'], '%Y-%m-%d').date()

        if market['market'] in markets1 and is_weekend(market_date):
            base_price = base_price * 1.5
            price_list.append({'currency': currency, 'date': market['date'], 'price': base_price})

        if market['market'] in market2 and is_wednesday(market_date):
            base_price = base_price * 0.70
            price_list.append({'currency': currency, 'date': market['date'], 'price': base_price})

        if is_friday(market_date):
            base_price = base_price * 1.25
            price_list.append({'currency': currency, 'date': market['date'], 'price': base_price})

        price_list.append({'currency': currency, 'date': market['date'], 'price': base_price})

    return jsonify({'calendar_listings': price_list}), 200


        