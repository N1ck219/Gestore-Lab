import urllib.request
import json

try:
    url = "http://localhost:5000/api/materie_fbb"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        res_data = response.read().decode('utf-8')
        data = json.loads(res_data)
        print("Success! Status code: 200")
        print(f"Number of materials: {len(data['materie'])}")
        for idx, item in enumerate(data['materie'], 1):
            print(f"{idx}. Code: {item['codice']}, Name: {item['nome']}, Qty: {item['qnt']}, Lots Count: {len(item.get('lotti', []))}")
except Exception as e:
    print(f"Error querying FBB endpoint: {e}")
