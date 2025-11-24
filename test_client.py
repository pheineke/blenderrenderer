import requests
import os

# Create a dummy blend file
with open('test.blend', 'wb') as f:
    f.write(b'DUMMY BLEND FILE CONTENT')

url = 'http://127.0.0.1:5000/'
files = {'file': open('test.blend', 'rb')}
data = {'render_type': 'image'}

try:
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text[:200]}") # Print first 200 chars
except Exception as e:
    print(f"Error: {e}")
finally:
    files['file'].close()
    if os.path.exists('test.blend'):
        os.remove('test.blend')
