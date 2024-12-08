def get_template(coin_name, coin_id, condition, price, currency):
    alert_confirmation_mail = \
    f"""
    <html>
    <body>
        <h3>Crypto Alert</h3>
        You will recive an email when 
        <img style='width: 15px; height: 15px' src="https://s2.coinmarketcap.com/static/img/coins/64x64/{coin_id}.png" alt=""/>{coin_name} value goes {condition} {price} {currency}.
        <button>Set Another Alert</button>
    </body>
    </html>
    """
    return alert_confirmation_mail
