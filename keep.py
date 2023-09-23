import time
import pprint
import requests
import urllib.parse
import hashlib
import hmac
import base64



with open("keys.txt", "r") as f:
    lines = f.read().splitlines()
    api_key = lines[0]
    api_sec = lines[1]



api_url = "https://api.kraken.com"



def get_kraken_signature(urlpath, data, secret):

    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()



def kraken_request(url_path, data, api_key, api_sec):

    headers = {"API-KEY": api_key, "API-Sign": get_kraken_signature(url_path, data, api_sec)}
    resp = requests.post((api_url + url_path), headers = headers, data = data)
    return resp



pair = input("Enter pair: ")
current_price = requests.get("https://api.kraken.com/0/public/Ticker?pair=" + pair).json()['result'][pair]['c'][0]
print("Current price: " + current_price)
equilibrium = float(input("Enter price: "))
increment = float(input("Enter increment: "))
amount = float(input("Enter amount: "))
# increment = 0.00000011
# equilibrium = float(current_price)+increment
# amount = 1
buy_price = round(equilibrium - increment, 8)
sell_price = round(equilibrium + increment, 8)



#resp_balance = kraken_request('/0/private/Balance', {
#    "nonce": str(int(1000 * time.time()))
#}, api_key, api_sec)


#balance = round(float(resp_balance.json()['result']['XXBT']) * float(requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDC").json()['result']['XBTUSDC']['c'][0]) + float(resp_balance.json()['result']['KEEP']) * float(requests.get("https://api.kraken.com/0/public/Ticker?pair=KEEPUSD").json()['result']['KEEPUSD']['c'][0]), 2)
#balance_keep = balance / round(float(requests.get("https://api.kraken.com/0/public/Ticker?pair=KEEPUSD").json()['result']['KEEPUSD']['c'][0]), 2)
#keep_balance = round(float(resp_balance.json()['result']['KEEP']), 2)
#print("Balance in KEEP: " + str(round(balance_keep, 2)))
#print("80% suggested limit: " + str(round(balance_keep * 0.8, 2)))
#print("Keep balance: " + str(keep_balance))
#buy_limit = float(input("Enter KEEP limit: "))
previous_price = 0


while True:
    #balance = round(float(resp_balance.json()['result']['XXBT']) * float(requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDC").json()['result']['XBTUSDC']['c'][0]) + float(resp_balance.json()['result']['KEEP']) * float(requests.get("https://api.kraken.com/0/public/Ticker?pair=KEEPUSD").json()['result']['KEEPUSD']['c'][0]), 2)
    current_price = requests.get("https://api.kraken.com/0/public/Ticker?pair=" + pair).json()['result'][pair]['c'][0]
    #btc_per = float(resp_balance.json()['result']['XXBT']) * float(requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDC").json()['result']['XBTUSDC']['c'][0]) / balance
    #keep_balance = round(float(resp_balance.json()['result']['KEEP']), 2)
    #if btc_per <= 0.2:
    #    print("Buy limit reached")
    #    time.sleep(60)
    #    continue
    #if keep_balance >= buy_limit:
    #    print("Buy limit reached")
    #    time.sleep(60)
    if float(current_price) <= buy_price:
        txid = None
        if round(previous_price, 8) == round(float(current_price), 8):
            time.sleep(5)
            continue
        print("Current price: " + current_price)
        print(f"Buying {amount} of {pair} at {buy_price}")
        print("Buy price: " + str(buy_price))
        print("Sell price: " + str(sell_price))
        resp = kraken_request("/0/private/AddOrder", {
            "nonce": str(int(1000 * time.time())),
            "ordertype": "limit",
            "type": "buy",
            "volume": amount,
            "pair": pair,
            "price": round(buy_price, 8)
        }, api_key, api_sec)
        # Parse the JSON response
        response_data = resp.json()

        # Check for errors in the response
        if 'error' in response_data and response_data['error']:
            print(f"Error in API response: {response_data['error']}")
        else:
            try:
                
                txid = str(response_data['result']['txid'])
                
                 
                txid = txid[2:-2]
                 
            except KeyError:
                print("Unexpected response structure. 'txid' not found in 'result'.")
        # If txid was successfully extracted, then proceed with subsequent operations
        if txid:
            len_txid = len(txid)
            # ... (any other code that uses txid)With this structure, the code will only attempt to compute len_txid (and any other operations relying on txid) if txid was successfully extracted. If there was an error or an unexpected response structure, the subsequent operations won't be executed.
        not_filled = True
        while not_filled:
            current_price = requests.get("https://api.kraken.com/0/public/Ticker?pair=" + pair).json()['result'][pair]['c'][0]
            if float(current_price) >= buy_price + increment:
                resp = kraken_request('/0/private/CancelOrder', {
                    "nonce": str(int(1000*time.time())),
                    "txid": txid
                }, api_key, api_sec)
                print(current_price)
                print("Price increased before order was filled")
                print("Order canceled")
                resp = kraken_request('/0/private/ClosedOrders', {
                    "nonce": str(int(1000*time.time())),
                }, api_key, api_sec)
                vol_exec = round(float(resp.json()['result']['closed'][txid]['vol_exec']), 8)
                resp = kraken_request("/0/private/AddOrder", {
                    "nonce": str(int(1000 * time.time())),
                    "ordertype": "limit",
                    "type": "sell",
                    "volume": vol_exec,
                    "pair": pair,
                    "price": round(float(current_price), 8)
                }, api_key, api_sec)
                if not resp.json()['error']:
                    print(f"Selling {vol_exec} of KEEPXBT at {round(float(current_price), 8)}")
                else:
                    print(f"Error: {resp.json()['error']}")
                not_filled = False
                print("Buy price: " + str(buy_price))
                print("Sell price: " + str(sell_price))
            else:
                try:
                    resp = kraken_request('/0/private/ClosedOrders', {
                        "nonce": str(int(1000*time.time())),
                    }, api_key, api_sec)
                    # print(resp.json())
                    closed_trade = resp.json()['result']['closed'][txid]
                    
                    not_filled = False
                    resp = kraken_request("/0/private/AddOrder", {
                        "nonce": str(int(1000 * time.time())),
                        "ordertype": "limit",
                        "type": "sell",
                        "volume": amount,
                        "pair": pair,
                        "price": round(buy_price + increment, 8)
                    }, api_key, api_sec)
                    if not resp.json()['error']:
                        print("Success!")
                    else:
                        print(f"Error: {resp.json()['error']}")
                    buy_price = round(buy_price - increment, 8)
                    print("New buy price: " + str(buy_price))
                    sell_price = round(sell_price - increment, 8)
                    print("New sell price: " + str(sell_price))
                    time.sleep(5)
                except:
                    print("Order not filled yet")
                    time.sleep(5)
                    pass
    elif float(current_price) >= sell_price:
        if round(previous_price, 8) == round(float(current_price), 8):
            time.sleep(5)
            continue
        print("Current price: " + current_price)
        print(f"Selling {amount} of KEEPXBT at {sell_price}")
        print("Buy price: " + str(buy_price))
        print("Sell price: " + str(sell_price))
        resp = kraken_request("/0/private/AddOrder", {
            "nonce": str(int(1000 * time.time())),
            "ordertype": "limit",
            "type": "sell",
            "volume": amount,
            "pair": pair,
            "price": round(sell_price, 8)
        }, api_key, api_sec)
        txid = str(resp.json()['result']['txid'])
        len_txid = len(txid)
        txid = txid[2 : len_txid - 2]
        
        resp = kraken_request('/0/private/ClosedOrders', {
            "nonce": str(int(1000*time.time())),
        }, api_key, api_sec)
        closed_trades = resp.json()['result']['closed']
        not_filled = True
        while not_filled:
            current_price = requests.get("https://api.kraken.com/0/public/Ticker?pair=" + pair).json()['result'][pair]['c'][0]
            if float(current_price) <= sell_price - increment:
                resp_cancel_sell = kraken_request('/0/private/CancelOrder', {
                    "nonce": str(int(1000*time.time())),
                    "txid": txid
                }, api_key, api_sec)
                print(current_price)
                print("Price decreased before order was filled")
                print("Order canceled")
                resp = kraken_request('/0/private/ClosedOrders', {
                    "nonce": str(int(1000*time.time())),
                }, api_key, api_sec)
                vol_exec = round(float(resp.json()['result']['closed'][txid]['vol_exec']), 8)
                resp = kraken_request("/0/private/AddOrder", {
                    "nonce": str(int(1000 * time.time())),
                    "ordertype": "limit",
                    "type": "buy",
                    "volume": vol_exec,
                    "pair": pair,
                    "price": round(float(current_price), 8)
                }, api_key, api_sec)
                if not resp.json()['error']:
                    print(f"Buying {vol_exec} of KEEPXBT at {round(float(current_price), 8)}")
                else:
                    print(f"Error: {resp.json()['error']}")
                not_filled = False
                print("Buy price: " + str(buy_price))
                print("Sell price: " + str(sell_price))
            else:
                try:
                    resp = kraken_request('/0/private/ClosedOrders', {
                        "nonce": str(int(1000*time.time())),
                    }, api_key, api_sec)
                    closed_trade = resp.json()['result']['closed'][txid]
                    not_filled = False
                    resp = kraken_request("/0/private/AddOrder", {
                        "nonce": str(int(1000 * time.time())),
                        "ordertype": "limit",
                        "type": "buy",
                        "volume": amount,
                        "pair": pair,
                        "price": round(sell_price - increment, 8)
                    }, api_key, api_sec)
                    if not resp.json()['error']:
                        print("Success!")
                    else:
                        print(f"Error: {resp.json()['error']}")
                    buy_price = round(buy_price + increment, 8)
                    print("New buy price: " + str(buy_price))
                    sell_price = round(sell_price + increment, 8)
                    print("New sell price: " + str(sell_price))
                    time.sleep(5)
                except:
                    print("Order not filled yet")
                    time.sleep(5)
                    pass
    else:
        if round(previous_price, 8) == round(float(current_price), 8):
            time.sleep(5)
            continue
        print(f"Current price: {current_price}, not buying nor selling")
        print("Buy price: " + str(buy_price))
        print("Sell price: " + str(sell_price))
        time.sleep(5)
    previous_price = float(current_price)