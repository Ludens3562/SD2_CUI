import datetime
import os
import io
import base64
import hashlib
import requests
from requests.auth import HTTPBasicAuth
from Crypto.Cipher import AES
from PIL import Image, PngImagePlugin
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData

global image_path
development = 1

def analyze_image():
    print("SafetyCheckStarted.")
    endpoint = os.environ.get('CONTENT_SAFETY_ENDPOINT')
    key = os.environ.get('CONTENT_SAFETY_KEY')

    # Create an Content Safety client
    client = ContentSafetyClient(endpoint, AzureKeyCredential(key))


    # Build request
    with open(image_path, "rb") as file:
        request = AnalyzeImageOptions(image=ImageData(content=file.read()))

    # Analyze image
    try:
        response = client.analyze_image(request)
    except HttpResponseError as e:
        print("Analyze image failed.")
        if e.error:
            print(f"Error code: {e.error.code}")
            print(f"Error message: {e.error.message}")
            raise
        print(e)
        raise

    if response.hate_result:
        print(f"Hate severity: {response.hate_result.severity}")
    if response.self_harm_result:
        print(f"SelfHarm severity: {response.self_harm_result.severity}")
    if response.sexual_result:
        print(f"Sexual severity: {response.sexual_result.severity}")
    if response.violence_result:
        print(f"Violence severity: {response.violence_result.severity}")
    upload_image()
        

def upload_image():
    # user_id = input("ユーザIDを入力してん")
    url = "http://127.0.0.1:3000/users/" + user_id + "/updatePicture"

    files = {'picture': open(image_path, 'rb')}
    response = requests.patch(url, auth=HTTPBasicAuth('user', 'pass'), files=files)

    if response.status_code == 200:
        print('Update successful')
    else:
        print('Update failed')

global filename
os.chdir("C://Users//ODPJ2023//Documents//SD2_CUI//outputs")

# stableDiffusionのURL
url = "http://127.0.0.1:7860"

# 時刻のイニシャライズ
t_delta = datetime.timedelta(hours=9)
JST = datetime.timezone(t_delta, 'JST')
now = datetime.datetime.now(JST)

key = b'Enter your key here'
print("QRコードをかざしてください： ", end="")
QR_input = input().strip()
# 暗号鍵と初期化ベクトル（IV）
iv = QR_input[:24]
print (iv)
crypted = QR_input[24:]
print (crypted)

# KEYからダイジェスト計算
key_dg = hashlib.sha256(key).digest()

# AES-256-CBC 復号化
cipher = AES.new(key_dg, AES.MODE_CBC, base64.b64decode(iv))

# Base64エンコードされたデータをデコード
crypted = base64.b64decode(crypted)

# 復号化
prompt = cipher.decrypt(crypted)

# パディングを取り除く（もしあれば）
prompt = prompt.rstrip(b'\0')

# バイト列を文字列に変換
prompt = prompt.decode('utf-8')
global user_id
user_id = prompt.split(',')[0][1:]
print(user_id)

payload = {
    "prompt": prompt,
    "seed": -1,
    "batch_size": 1,
    "steps": 20,
    "cfg_scale": 7,
    "width": 512,
    "height": 512,
    "negative_prompt": "EasyNegative",
    "s_noise": 1,
    "script_args": [],
"sampler_index": "Euler a",
}
print("生成中...")
response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
r = response.json()

# pngに情報を書き込み
for i in r['images']:
    image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

    png_payload = {
        "image": "data:image/png;base64," + i
    }
    response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
    pnginfo = PngImagePlugin.PngInfo()
    if development:
        pnginfo.add_text("parameters", response2.json().get("info"))
    else:
        pnginfo.add_text("Created by ", "小田切プロジェクト2023")
    # pnginfo.add_text("safetyInfo", safetyResult)
    filename = str(now.strftime('%Y%m%d%H%M%S') + ".png")
    image.save(filename, pnginfo=pnginfo)
    image_path = os.path.join(filename)

print("Done!\n")
if development:
    upload_image()
else:
    analyze_image()