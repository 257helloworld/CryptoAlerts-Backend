from flask import Flask, json, redirect, request, Response, jsonify, url_for
from requests import Request, Session
from flask_mail import Mail, Message
import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from apscheduler.schedulers.background import BackgroundScheduler
import key
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from services.email import send_email
import services.telegram
from templates import alert_confirmation_mail, alert_mail
import threading
import asyncio
from functions import time_difference
import random

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(credentials)

spreadsheet = client.open_by_key("10e8hzXF25BlCiFklgaZnmO2sBsnx-lhart7iFO_S4Uk")

worksheet = spreadsheet.get_worksheet(0)

app = Flask(__name__)
mail = Mail(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465               
app.config['MAIL_USERNAME'] = key.mail_username
app.config['MAIL_PASSWORD'] = key.gmail_app_password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

@app.route('/all_coins')
def latest():
    with open("data/coins_data.json", "r") as f:
        file_data = json.load(f)
        cachedTime = file_data["timestamp"]
        if(not time_difference.is_greater_than_24_hours(cachedTime)):
            return jsonify(file_data["data"]), 200
    url = ' https://pro-api.coinmarketcap.com/v1/cryptocurrency/map'
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': key.cmc_api_key,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url)
        data = json.loads(response.text)
        new_file_data = {
            "timestamp": datetime.datetime.now().timestamp(),
            "data": data["data"]
        }
        with open("data/coins_data.json", "w") as f:
            f.write(json.dumps(new_file_data, indent = 4))
        return jsonify(data["data"]), 200
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return jsonify(e), 500
    

def get_prices_from_file(coin_ids_list):
    prices = dict()
    with open("data/coins_price_data.json", "r") as f:
        file_data = json.load(f)
    for c_id in coin_ids_list:
        prices[str(c_id)] = file_data.get(str(c_id))
    return prices

@app.route('/get_coins')
def get_coins(coin_ids = False):
    if(not coin_ids):
        coin_ids_string = request.args.get("coin_id")
        coin_ids_list = [int(c_id) for c_id in coin_ids_string.split(",")]
    if(coin_ids):
        coin_ids_string = ','.join(str(c_id) for c_id in coin_ids)
        coin_ids_list = coin_ids
    # return jsonify({"str": coin_ids_string, "lst": coin_ids_list})

    # Checking for recently cached prices.
    updated_prices = []
    not_updated_prices = []

    with open("data/coins_price_data.json", "r") as f:
        file_data = json.load(f)

    for c_id in coin_ids_list:
        coin = file_data.get(str(c_id))
        if(coin and (not time_difference.is_greater_than_1_hour(coin["timestamp"]))):
            updated_prices.append(c_id)
        else:
            not_updated_prices.append(c_id)
    
    if(len(not_updated_prices) == 0):
        return get_prices_from_file(coin_ids_list)
    
    # Fetch new rates for coin prices that are not cached.        
    coin_ids_string = ','.join(str(c_id) for c_id in not_updated_prices)
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    parameters = {
        'id': coin_ids_string
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': key.cmc_api_key,
    }
    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params = parameters)
        result = json.loads(response.text)
        if "data" not in result:
            result = None
        else:
            result = result["data"]
            for coin_key, coin_value in result.items():
                coin_data = {
                    'id': coin_value['id'],
                    'price': coin_value["quote"]["USD"]["price"],
                    'last_updated': coin_value["quote"]["USD"]["last_updated"],
                    'name': coin_value['name'],
                    'symbol': coin_value['symbol'],
                    'logo': f"https://s2.coinmarketcap.com/static/img/coins/64x64/{coin_value['id']}.png",
                    'timestamp': datetime.datetime.now().timestamp()
                }
                file_data[str(coin_key)] = (coin_data)
        # Updating new prices in file.
        with open("data/coins_price_data.json", "w") as f:
            f.write(json.dumps(file_data, indent = 4))

        return jsonify(get_prices_from_file(coin_ids_list)), 200
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return jsonify(e), 500

@app.route('/set_alert')
def set_alert():
    alert_id = generate_unique_alert_id()
    coin_id = request.args.get("coin_id")
    coin_name = request.args.get("coin_name")
    coin_symbol = request.args.get("coin_symbol")
    alert_method = request.args.get("alert_method")
    condition = request.args.get("condition")
    alert_price = request.args.get("alert_price")
    currency = request.args.get("currency")
    alert_medium = request.args.get("alert_medium")
    is_triggered = 0

    new_alert_row = [alert_id, coin_id, coin_name, coin_symbol, alert_method, condition, alert_price, currency, alert_medium, is_triggered]

    try:
        worksheet.append_row(new_alert_row)
        worksheet.get_all_records()
        return jsonify({"message":"Alert set successfully!", "alert": new_alert_row}), 200
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return jsonify(e), 500
    
@app.route('/check_alert_conditions')
def check_alert_conditions():
    all_records = worksheet.get_all_records()
    not_triggered_records = [alert for alert in all_records if not alert["is_triggered"]]
    crypto_ids = list(set([alert["crypto_id"] for alert in not_triggered_records]))
    crypto_rates = get_coins(crypto_ids)
    with open("data/currency_data.json", "r") as f:        
        fiat_currency_rates = json.load(f)["data"]
    # Checking condition
    alerts = list()
    for alert in not_triggered_records:
        crypto_price_in_USD = crypto_rates.get(str(alert["crypto_id"]))["price"]
        USD_to_currency_conversion_rate = fiat_currency_rates[alert["currency"]]["rate"]
        crypto_price_in_currency = crypto_price_in_USD * USD_to_currency_conversion_rate

        if(alert["condition"] == "Above" and (crypto_price_in_currency >= alert["alert_price"])):
            alerts.append(alert)
        elif(alert["condition"] == "Below" and (crypto_price_in_currency <= alert["alert_price"])):
            alerts.append(alert)
    if(len(alerts) > 0):
        trigger_alerts(alerts)
    return jsonify({
        "Sending alerts to": alerts
    })

def generate_unique_alert_id():
    with open("data/generated_alert_ids.json", "r") as f:
        generated_alert_ids = json.load(f)
    while(True):
        new_id = random.randint(10101010, 90909090)
        if(new_id not in generated_alert_ids):
            break
    with open("data/generated_alert_ids.json", "w") as f:
        generated_alert_ids[str(new_id)] = datetime.datetime.now().timestamp()
        f.write(json.dumps(generated_alert_ids, indent = 4))
    return new_id

def trigger_alerts(alerts):
    # Send alerts
    for alert in alerts:
        """
            Sending alerts based on alert receiving medium.    
        
        """
    # Set is_triggered to true in workbook.
        alert_id = alert["alert_id"]
        cell_row = worksheet.find(str(alert_id), in_column = 1).row
        worksheet.update_cell(row = cell_row, col = 10, value = 1)

# def timestamp():
#     now = datetime.datetime.now()
#     timestamp = f"{now.hour}: {now.minute} : {now.second} IST"
#     print(timestamp)

@app.route("/email_alert_confirmation")
def email():
    mailto = key.email_id
    html = alert_confirmation_mail.get_template("Bitcoin", 1,"above", 3757, "INR")
    try:
        if(send_email(subject = "Alert for TNC Coin set successfully!", html = html,mailto = mailto)):
            return jsonify("Email sent successfully!"), 200
    except Exception as e:
        return jsonify(e), 500

# scheduler = BackgroundScheduler()
# scheduler.add_job(func=say_hello, trigger="interval", minutes = 1)
# scheduler.start()

@app.route("/get_currencies")
def get_currencies():
    # Return cached rates.
    with open("data/currency_data.json", "r") as f:
        file_data = json.load(f)
    if(not time_difference.is_greater_than_1_hour(file_data["timestamp"])):
        return jsonify(file_data["data"])
    
    # Fetch new rates every hour.
    url = f"https://openexchangerates.org/api/latest.json?app_id={key.open_exchange_rates_app_id}&base=USD&prettyprint=true&show_alternative=false"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers = headers)
    new_data = json.loads(response.text)["rates"]
    
    for k, v in file_data["data"].items():
        file_data["data"][k]["rate"] = new_data.get(k)
    file_data["timestamp"] = datetime.datetime.now().timestamp()

    with open("data/currency_data.json", "w") as f:
        f.write(json.dumps(file_data, indent = 4))
    
    return jsonify(file_data["data"])

@app.route("/")
def helloWorld():
    return "Alive :)"

if __name__ == '__main__':
    services.telegram.telegram_app.start()
    threading.Thread(target = app.run, daemon = True).start()
    services.telegram.pyrogram.idle()
    services.telegram.telegram_app.stop()