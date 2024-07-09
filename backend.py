
from flask import Flask, request, send_file, jsonify
import iitkgp_erp_login.erp as erp
import logging
import gyfe
import io
from datetime import datetime
import requests

app = Flask(__name__)

headers = {
        "timeout": "20",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
        }

class ErpResponse:
    def __init__(self, success: bool, message: str = None, data: dict = None, status_code: int = 200):
        self.success = success
        self.message = message
        self.data = data or {}
        self.status_code = status_code

        if not success:
            logging.error(f" {message}")

    def to_dict(self):
        response = {
            "status": "success" if self.success else "error",
            "message": self.message
        }
        if self.data:
            response.update(self.data)
        return response

    def to_response(self):
        return jsonify(self.to_dict()), self.status_code

@app.route("/secret-question", methods=["POST"])
def get_secret_question():
    try:
        data = request.get_json()
        roll_number = data.get("roll_number")
        if not roll_number:
            return ErpResponse(False, "Roll Number not provided.", status_code=400).to_response()
        
        session = requests.Session()

        secret_question = erp.get_secret_question(headers=headers, session=session, roll_number=roll_number, log=True)
        JSESSIONID = session.cookies.get('JSESSIONID')

        return ErpResponse(True, data={
            "secret_question": secret_question,
            "JSESSIONID": JSESSIONID
        }).to_response()

    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()

@app.route("/request-otp", methods=["POST"])
def request_otp():
    try:
        data = request.get_json()
        JSESSIONID = data.get("JSESSIONID")
        if not JSESSIONID:
            return ErpResponse(False, "JSESSIONID not provided.", status_code=400).to_response()
        
        ROLL_NUMBER = data.get("roll_number")
        PASSWORD = data.get("password")
        secret_answer = data.get("secret_answer")
        if not all([ROLL_NUMBER, PASSWORD, secret_answer]):
            return ErpResponse(False, "Missing password or secret answer", status_code=400).to_response()

        session = requests.Session()
        session.cookies.set(name='JSESSIONID', value=JSESSIONID, domain='erp.iitkgp.ac.in')
        login_details = erp.get_login_details(
            ROLL_NUMBER=ROLL_NUMBER,
            PASSWORD=PASSWORD,
            secret_answer=secret_answer,
            sessionToken=JSESSIONID
        )

        erp.request_otp(headers=headers, session=session, login_details=login_details, log=True)
        return ErpResponse(True, message="OTP has been sent to your connected email accounts").to_response()

    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        JSESSIONID = data.get("JSESSIONID")
        if not JSESSIONID:
            return ErpResponse(False, "JSESSIONID not provided.", status_code=400).to_response()

        ROLL_NUMBER = data.get("roll_number")
        PASSWORD = data.get("password")
        secret_answer = data.get("secret_answer")
        otp = data.get("otp")

        if not all([ROLL_NUMBER, secret_answer, PASSWORD, otp]):
            return ErpResponse(False, "Missing roll number, password, secret answer or otp", status_code=400).to_response()

        login_details = erp.get_login_details(
            ROLL_NUMBER=ROLL_NUMBER,
            PASSWORD=PASSWORD,
            secret_answer=secret_answer,
            sessionToken=JSESSIONID,
        )
        login_details["email_otp"] = otp

        session = requests.Session()
        session.cookies.set(name='JSESSIONID', value=JSESSIONID, domain='erp.iitkgp.ac.in')

        ssoToken = erp.signin(headers=headers, session=session, login_details=login_details, log=True)
        return ErpResponse(True, data={
            "ssoToken": ssoToken
        }).to_response()

    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()

@app.route('/elective/<ELECTIVE>', methods=["POST"])
def elective(ELECTIVE):
    try:
        data = request.get_json()
        ssoToken = data.get("ssoToken")
        if not ssoToken:
            return ErpResponse(False, "ssoToken not provided.", status_code=400).to_response()

        ROLL_NUMBER = data.get("roll_number")
        DEPT = ROLL_NUMBER[2:4]
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month in [1, 2, 3, 4, 5, 6]:
            SEMESTER = "SPRING"
            SESSION = str(current_year - 1) +'-'+ str(current_year)
            YEAR = current_year - int("20"+ROLL_NUMBER[:2]) - 1
        elif current_month in [7, 8, 9, 10, 11, 12]:
            SEMESTER = "AUTUMN"
            SESSION = str(current_year) +'-'+ str(current_year + 1)
            YEAR = current_year - int("20"+ROLL_NUMBER[:2])
        
        SEMESTER = data.get("semester") if data.get("semester") else SEMESTER
        SESSION = data.get("session") if data.get("session") else SESSION
        YEAR = int(data.get("year"))-1 if data.get("year") else YEAR

        responses = gyfe.fetch_response(SESSION, SEMESTER, YEAR, ELECTIVE, DEPT, ssoToken)

        if not all(responses):
            return ErpResponse(False, "Failed to retrieve data..", status_code=500).to_response()

        if ELECTIVE == "breadth":
            file = gyfe.save_breadths(responses, False)
        elif ELECTIVE == "depth":
            file = gyfe.save_depths(responses, False)
        
        csv = io.BytesIO()
        csv.write(file.encode('utf-8'))
        csv.seek(0)
        
        return send_file(
            csv,
            as_attachment=True,
            mimetype='text/csv',
            download_name=f"${ELECTIVE}_{ROLL_NUMBER}.csv"
        )

    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()