import base64
import hashlib
from Crypto.Cipher import AES

# 32バイトのキー (256ビット#
key = b'Enter your key here'
# 暗号化されたデータ（Base64エンコードされた文字列）
QR_input = "0aK13IucRTpkqk92K/uINA==ptwlvrdOjxzOZXe56fRpiTbxRN0Ya3w33Qt1i38MUm7iKaNZ6DSBz5+VYI4qdrCjrf60k/UeAtE6nSF1yYmwZamV3H4brikP69Ogbi5YH22kJmd8ZSlaNSYqFPteeN+y"

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
encrypted_data = base64.b64decode(crypted)

# 復号化
plaintext = cipher.decrypt(encrypted_data)

# パディングを取り除く（もしあれば）
plaintext = plaintext.rstrip(b'\0')

# バイト列を文字列に変換
plaintext = plaintext.decode('utf-8')

# 復号化されたデータを表示
print(plaintext,end='')
