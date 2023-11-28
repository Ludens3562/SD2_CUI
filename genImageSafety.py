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
from openai import OpenAI


def main():
    # プリントサブシステム開始
    subprocess.Popen(["run.bat"])
    load_dotenv()
    os.chdir(os.getenv("SD_output"))
    SD_url = os.getenv("SD_url")
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, "JST")
    development = 1

    def decrypt(param):
        # param 0 = SD and DALLE3
        # param 1 = SD
        # param 2 = DALLE3
        load_dotenv()
        key = os.getenv("sharedKEY")
        print("QRコードをかざしてください：", end="")
        input_raw = input().strip()
        iv = input_raw[:24]
        pt_data = input_raw[24:]
        # 復号化
        key_dg = hashlib.sha256(key.encode()).digest()
        cipher = AES.new(key_dg, AES.MODE_CBC, base64.b64decode(iv))
        pt_data = base64.b64decode(pt_data)
        prompt = cipher.decrypt(pt_data)
        prompt = prompt.rstrip(b"\0")
        prompt = prompt.decode("utf-8")
        print(prompt)
        user_id = prompt.split(",")[0][1:]

        if param == 0:
            SD_imageGen(prompt, user_id)
            DALLE3_imageGen(prompt, user_id)
        elif param == 1:
            SD_imageGen(prompt, user_id)
        elif param == 2:
            DALLE3_imageGen(prompt, user_id)
        else:
            print("パラメータの値が不正です")

    def SD_imageGen(prompt, id):
        payload = {
            "prompt": prompt,
            "seed": -1,
            "batch_size": 1,
            "steps": 30,
            "cfg_scale": 7,
            "width": 1024,
            "height": 1024,
            "negative_prompt": "EasyNegative",
            "s_noise": 1,
            "script_args": [],
            "sampler_index": "Euler a",
        }
        print("SD2_生成中...")
        response = requests.post(url=f"{SD_url}/sdapi/v1/txt2img", json=payload)
        r = response.json()

        # pngに情報を書き込み
        for i in r["images"]:
            image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))
            png_payload = {"image": "data:image/png;base64," + i}
            pnginfo = PngImagePlugin.PngInfo()
            if development:
                # プロンプトデータAPI取得
                response2 = requests.post(url=f"{SD_url}/sdapi/v1/png-info", json=png_payload)
                pnginfo.add_text("parameters", response2.json().get("info"))
            else:
                pnginfo.add_text("Created by ", os.getenv("AUTHER"))
            # pnginfo.add_text("safetyInfo", safetyResult)
            now = datetime.datetime.now(JST)
            filename = str("SD" + id + "-" + now.strftime("%Y%m%d%H%M%S") + ".jpg")
            image.save(filename, "JPEG", quality=98, pnginfo=pnginfo)
            image_path = os.path.join(filename)

        print("SD_Image Generated!\n")
        if development:
            upload_image(0, id, image_path)
        else:
            if isSafetyImage(image_path):
                upload_image(0, id, image_path)
            else:
                os.rename(filename, "【NG】" + filename)
                decrypt(1)

    def DALLE3_imageGen(prompt, id):
        OpenAI.API_KEY = os.getenv("OPENAI_API_KEY")
        client = OpenAI()
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            style="natural",
            response_format="b64_json",
            n=1,
            user="SD2_CUI" + "_" + id,
        )
        # image_url = response.data[0].url
        print(response)
        image_data = base64.b64decode(response.data[0].b64_json)
        image = Image.open(io.BytesIO(image_data))
        now = datetime.datetime.now(JST)
        filename = str("DE" + id + "-" + +now.strftime("%Y%m%d%H%M%S") + ".jpg")
        image.save(filename)
        image_path = os.path.join(filename)

        if development:
            upload_image(1, id, image_path)
        else:
            if isSafetyImage(image_path):
                upload_image(1, id, image_path)
            else:
                os.rename(filename, "【NG】" + filename)
                decrypt(2)

    def isSafetyImage(image_path):
        print("SafetyCheckStarted.\n")
        key = os.getenv("AZURE_KEY1")
        endpoint = os.getenv("AZURE_ENDPOINT")

        client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
        with open(image_path, "rb") as file:
            request = AnalyzeImageOptions(image=ImageData(content=file.read()))

        try:
            response = client.analyze_image(request)
        except HttpResponseError as e:
            print("Analyze image failed.")
            if e.error:
                print(f"Error code: {e.error.code}")
                print(f"Error message: {e.error.message}\n")
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
            return False
        else:
            return True

    def upload_image(param, id, image_path):
        # param 1 = SD image
        # param 2 = DALLE3 image
        if param == 0:
            WEB_url = os.getenv("WEB_URL") + id + "/updatePicture"
        if param == 1:
            WEB_url = os.getenv("WEB_URL") + id + "/updatePicture_dall"
        else:
            print("パラメータの値が不正です")

        files = {"picture": open(image_path, "rb")}
        response = requests.patch(
            WEB_url, auth=HTTPBasicAuth(os.getenv("UPLOAD_USER"), os.getenv("UPLOAD_PASS")), files=files
        )

        if response.status_code == 200:
            print("Update successful")
        else:
            print("UploadError\n statuscode:" + response.status_code)

    while True:
        decrypt(2)


if __name__ == "__main__":
    main()
