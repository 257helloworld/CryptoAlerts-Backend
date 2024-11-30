def get_template(coin_name, condition, price):
    alert_confirmation_mail = \
    f"""
    <html>
    <body>
        <h3>Crypto Alert</h3>
        You will recive an email when 
        <img src="" alt=""/>{coin_name} value goes {condition} {price} INR.
        <button>Set Another Alert</button>
    </body>
    </html>
    """
    return alert_confirmation_mail
