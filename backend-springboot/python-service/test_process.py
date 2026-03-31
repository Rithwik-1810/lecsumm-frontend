import requests
import io

def test():
    print("Testing /process endpoint on localhost:5000...")
    # Create a tiny dummy wav file
    dummy_wav = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    files = {'file': ('test.wav', io.BytesIO(dummy_wav), 'audio/wav')}
    data = {'language': 'english'}
    
    try:
        response = requests.post('http://127.0.0.0:5000/process', files=files, data=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        # Try 127.0.0.1
        try:
            response = requests.post('http://127.0.0.1:5000/process', files=files, data=data, timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e2:
            print(f"Connection failed: {e2}")

if __name__ == '__main__':
    test()
