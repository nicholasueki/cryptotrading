import time
import requests
import json
import hmac
import hashlib
import base64

# Load API credentials
with open("keys.txt", "r") as f:
    lines = f.read().splitlines()
    api_key = lines[0]
    api_secret = lines[1]
    api_passphrase = lines[2]  # Coinbase Pro requires an additional passphrase

base_url = "https://api.pro.coinbase.com"


def get_coinbase_signature(secret, request_path, body, method, timestamp):
    message = timestamp + method + request_path + body
    hmac_key = base64.b64decode(secret)
    signature = hmac.new(hmac_key, message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(signature.digest()).decode('utf-8')


def coinbase_request(method, url_path, data=None):
    timestamp = str(time.time())
    body = json.dumps(data) if data else ''
    signature = get_coinbase_signature(api_secret, url_path, body, method, timestamp)

    headers = {
        'CB-ACCESS-KEY': api_key,
        'CB-ACCESS-SIGN': signature,
        'CB-ACCESS-TIMESTAMP': timestamp,
        'CB-ACCESS-PASSPHRASE': api_passphrase,
        'Content-Type': 'application/json'
    }

    if method == 'GET':
        resp = requests.get(base_url + url_path, headers=headers)
    else:
        resp = requests.post(base_url + url_path, headers=headers, data=body)
    
    return resp.json()


pair = input("Enter pair (e.g., BTC-USD): ")
ticker = coinbase_request('GET', f'/products/{pair}/ticker')
print("Current price:", ticker['price'])

equilibrium = float(input("Enter price: "))
increment = float(input("Enter increment: "))
amount = float(input("Enter amount: "))

buy_price = round(equilibrium - increment, 8)
sell_price = round(equilibrium + increment, 8)

previous_price = 0

while True:
    ticker = coinbase_request('GET', f'/products/{pair}/ticker')
    current_price = float(ticker['price'])

    if current_price <= buy_price:
        if round(previous_price, 8) == round(current_price, 8):
            time.sleep(5)
            continue
        print("Current price:", current_price)
        print(f"Buying {amount} of {pair} at {buy_price}")
        order = coinbase_request('POST', '/orders', {
            'product_id': pair,
            'side': 'buy',
            'price': str(buy_price),
            'size': str(amount),
            'type': 'limit',
            'post_only': True
        })
        if 'message' in order:
            print(f"Error placing buy order: {order['message']}")
        else:
            print("Buy order placed successfully!")
    elif current_price >= sell_price:
        if round(previous_price, 8) == round(current_price, 8):
            time.sleep(5)
            continue
        print("Current price:", current_price)
        print(f"Selling {amount} of {pair} at {sell_price}")
        order = coinbase_request('POST', '/orders', {
            'product_id': pair,
            'side': 'sell',
            'price': str(sell_price),
            'size': str(amount),
            'type': 'limit',
            'post_only': True
        })
        if 'message' in order:
            print(f"Error placing sell order: {order['message']}")
        else:
            print("Sell order placed successfully!")
    else:
        if round(previous_price, 8) == round(current_price, 8):
            time.sleep(5)
            continue
        print(f"Current price: {current_price}, not buying nor selling")

    previous_price = current_price
    time.sleep(5)
