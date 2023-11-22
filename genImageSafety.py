import datetime
import os
import subprocess
import io
import base64
import hashlib
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from Crypto.Cipher import AES
from PIL import Image, PngImagePlugin
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData


def main():
    subprocess.Popen(["run.bat"])
    load_dotenv()
    development = 1

    def image_Gen():
        load_dotenv()
        global filename
        os.chdir(os.getenv("SD_output"))
        SD_url = os.getenv("SD_url")

        t_delta = datetime.timedelta(hours=9)
        JST = datetime.timezone(t_delta, "JST")

        key = os.getenv("sharedKEY")
        print("QRコードをかざしてください：", end="")
        QR_input = input().strip()
        iv = QR_input[:24]
        crypted = QR_input[24:]

        # KEYからダイジェスト計算
        key_dg = hashlib.sha256(key.encode()).digest()
        # AES-256-CBC 復号化
        cipher = AES.new(key_dg, AES.MODE_CBC, base64.b64decode(iv))
        # Base64エンコードされたデータをデコード
        crypted = base64.b64decode(crypted)
        # 復号化
        prompt = cipher.decrypt(crypted)
        # パディングを取り除く（もしあれば）
        prompt = prompt.rstrip(b"\0")
        # バイト列を文字列に変換
        prompt = prompt.decode("utf-8")
        print(prompt)
        global user_id
        user_id = prompt.split(",")[0][1:]

        payload = {
            "prompt": prompt,
            "seed": -1,
            "batch_size": 1,
            "steps": 20,
            "cfg_scale": 7,
            "width": 1000,
            "height": 1000,
            "negative_prompt": "EasyNegative",
            "s_noise": 1,
            "script_args": [],
            "sampler_index": "Euler a",
        }
        print("生成中...")
        response = requests.post(url=f"{SD_url}/sdapi/v1/txt2img", json=payload)
        r = response.json()

        # pngに情報を書き込み
        for i in r["images"]:
            image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))

            png_payload = {"image": "data:image/png;base64," + i}
            response2 = requests.post(url=f"{SD_url}/sdapi/v1/png-info", json=png_payload)
            pnginfo = PngImagePlugin.PngInfo()
            if development:
                pnginfo.add_text("parameters", response2.json().get("info"))
            else:
                pnginfo.add_text("Created by ", os.getenv("AUTHER"))
            # pnginfo.add_text("safetyInfo", safetyResult)
            now = datetime.datetime.now(JST)
            filename = str(now.strftime("%Y%m%d%H%M%S") + ".jpg")
            image.save(filename, "JPEG", quality=98, pnginfo=pnginfo)
            global image_path
            image_path = os.path.join(filename)

        print("Image Generated!\n")
        if development:
            upload_image()
        else:
            analyze_image()

    def analyze_image():
        print("SafetyCheckStarted.")
        key = os.getenv("AZURE_KEY1")
        endpoint = os.getenv("AZURE_ENDPOINT")

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
        try:
            if response.hate_result.severity != 0:
                raise Exception(f"差別的なコンテンツが検出されました レベル：{response.hate_result.severity}")
            if response.self_harm_result.severity != 0:
                raise Exception(f"自傷的なコンテンツが検出されました レベル：{response.self_harm_result.severity}")
            if response.sexual_result.severity != 0:
                raise Exception(f"性的なコンテンツが検出されました レベル：{response.sexual_result.severity}")
            if response.violence_result.severity != 0:
                raise Exception(f"暴力的なコンテンツが検出されました レベル：{response.violence_result.severity}")
        except Exception as e:
            print(e)
            image_Gen()
        else:
            upload_image()

    def upload_image():
        WEB_url = os.getenv("WEB_URL") + user_id + "/updatePicture"

        files = {"picture": open(image_path, "rb")}
        response = requests.patch(
            WEB_url, auth=HTTPBasicAuth(os.getenv("UPLOAD_USER"), os.getenv("UPLOAD_PASS")), files=files
        )

        if response.status_code == 200:
            print("Update successful")
        else:
            print("Update failed")

    while True:
        image_Gen()


if __name__ == "__main__":
    main()
