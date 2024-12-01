from flask import Flask, json, redirect, request, Response, jsonify, url_for
from requests import Request, Session
from flask_mail import Mail, Message
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from apscheduler.schedulers.background import BackgroundScheduler
import key
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from services.email import send_email
from templates import alert_confirmation_mail, alert_mail

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
        return jsonify(data["data"]), 200
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return jsonify(e), 500

@app.route('/get_coins')
def get_coins():
    coin_id = request.args.get("coin_id")
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    parameters = {
        'id': coin_id
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
        result = result["data"]
        coins_data = dict()
        for coin_key, coin_value in result.items():
            coin_data = {
                'id': coin_value['id'],
                'price': coin_value["quote"]["INR"]["price"],
                'last_updated': coin_value["quote"]["INR"]["last_updated"],
                'name': coin_value['name'],
                'symbol': coin_value['symbol'],
                'logo': f"https://s2.coinmarketcap.com/static/img/coins/64x64/{coin_value['id']}.png"
            }
            coins_data[coin_key] = (coin_data)
            
        return jsonify(coins_data), 200
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return jsonify(e), 500

@app.route('/set_alert')
def set_alert():
    coin_id = request.args.get("coin_id")
    coin_name = request.args.get("coin_name")
    coin_symbol = request.args.get("coin_symbol")
    alert_method = request.args.get("alert_method")
    condition = request.args.get("condition")
    alert_price = request.args.get("alert_price")
    alert_medium = request.args.get("alert_medium")
    is_triggered = 0

    new_alert = [coin_id, coin_name, coin_symbol, alert_method, condition, alert_price, alert_medium, is_triggered]

    try:
        worksheet.append_row(new_alert)
        worksheet.get_all_records()
        return jsonify({"message":"Alert set successfully!", "alert": new_alert}), 200
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return jsonify(e), 500

def timestamp():
    now = datetime.datetime.now()
    timestamp = f"{now.hour}: {now.minute} : {now.second} IST"
    print(timestamp)

@app.route("/email")
def email():
    mailto = key.email_id
    html = alert_confirmation_mail.get_template("TNC Coin", "above", 0.06)
    try:
        if(send_email(subject = "Alert for TNC Coin set successfully!", html = html,mailto = mailto)):
            return jsonify("Email sent successfully!"), 200
    except Exception as e:
        return jsonify(e), 500

# scheduler = BackgroundScheduler()
# scheduler.add_job(func=say_hello, trigger="interval", minutes=1)
# scheduler.start()

if __name__ == '__main__':
    app.run(debug = True)