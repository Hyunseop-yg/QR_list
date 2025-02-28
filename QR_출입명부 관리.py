import os
import pandas as pd
import qrcode
from flask import Flask, request, render_template
from PIL import Image, ImageDraw, ImageFont

# ------------------------------
# 📂 데이터베이스 설정 (엑셀 파일 자동 생성)
# ------------------------------
DATA_FILE = "participants.xlsx"

def load_data():
    """엑셀 파일이 없으면 자동 생성 후 로드"""
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["성명", "소속", "직위", "넘버링", "사전등록"])
        df.to_excel(DATA_FILE, index=False)
    else:
        df = pd.read_excel(DATA_FILE)
    return df

def save_data(df):
    """엑셀 파일로 데이터 저장"""
    df.to_excel(DATA_FILE, index=False)

def register_participant(name, affiliation, position, registered=True):
    """사전 등록되지 않은 참가자를 데이터에 추가"""
    df = load_data()

    # 기존 참가자 확인
    existing = df[(df["성명"] == name) & (df["소속"] == affiliation) & (df["직위"] == position)]
    if not existing.empty:
        return existing.iloc[0]["넘버링"]  # 이미 등록된 경우 기존 넘버링 반환

    # 새 넘버링 생성 (Y_1, N_1 형태)
    prefix = "Y" if registered else "N"
    count = df[df["넘버링"].str.startswith(prefix, na=False)].shape[0] + 1
    numbering = f"{prefix}_{count}"

    new_entry = pd.DataFrame([[name, affiliation, position, numbering, "Yes" if registered else "No"]],
                             columns=["성명", "소속", "직위", "넘버링", "사전등록"])
    df = pd.concat([df, new_entry], ignore_index=True)
    save_data(df)

    return numbering

# ------------------------------
# 🎯 **Render 배포 URL을 포함한 QR 코드 생성**
# ------------------------------
def generate_qr_jpg():
    """Render 배포 URL을 포함한 QR 코드 생성"""
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")

    # ✅ Render에서 배포된 도메인 (여기에 배포된 실제 URL 입력)
    cloud_url = "https://my-qrcode-app.onrender.com/scan_qr"
    qr = qrcode.make(cloud_url)

    # 파일 저장 경로 (JPG)
    file_name = "qrcodes/entry_qr.jpg"

    # QR 코드를 RGB 모드로 변환하여 저장 (JPG 형식 지원)
    qr = qr.convert("RGB")
    qr.save(file_name, "JPEG")

    return file_name

# ------------------------------
# 📲 Flask 웹 애플리케이션 (QR 코드 처리)
# ------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "QR 코드를 스캔하여 출입을 확인하세요."

@app.route('/scan_qr', methods=['GET'])
def scan_qr():
    """QR 코드 스캔 시 참가 여부 확인 페이지 표시"""
    return render_template("scan_qr.html")

@app.route('/check', methods=['POST'])
def check_participation():
    """QR 코드 스캔 후 참가 여부 확인"""
    name = request.form["name"]
    affiliation = request.form["affiliation"]
    position = request.form["position"]
    
    df = load_data()
    user = df[(df["성명"] == name) & (df["소속"] == affiliation) & (df["직위"] == position)]
    
    if not user.empty:
        return f"""
        <h2>사전 등록 확인 완료!</h2>
        <p>이름: {name}</p>
        <p>소속: {affiliation}</p>
        <p>직위: {position}</p>
        <p>넘버링: {user.iloc[0]["넘버링"]}</p>
        """
    else:
        register_participant(name, affiliation, position, registered=False)
        return f"""
        <h2>사전 등록이 확인되지 않았습니다.</h2>
        <p>새로운 등록이 완료되었습니다. 결제 후 명찰을 받을 수 있습니다.</p>
        <p>계좌 정보: 신한은행 110-521-754361 (예금주: 양현섭)</p>
        """

# ------------------------------
# 🚀 실행 (Flask 서버 시작)
# ------------------------------
if __name__ == "__main__":
    file_path = generate_qr_jpg()
    print(f"✅ 고정된 QR 코드가 생성되었습니다: {file_path}")
    
    # Flask 서버 실행 (Render 배포 시 사용)
    app.run(host='0.0.0.0', port=5000, debug=True)
