from flask import Flask, request, send_file, jsonify, make_response
import iitkgp_erp_login.erp as erp
import iitkgp_erp_login.utils as erp_utils
import logging
import gyfe
import io
from datetime import datetime
import requests
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
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
            "status": "success" if self.success else "error"
        }
        if self.message:
            response.update({"message": self.message})
        if self.data:
            response.update(self.data)
        return response

    def to_response(self):
        return jsonify(self.to_dict()), self.status_code


@app.route("/secret-question", methods=["POST"])
def get_secret_question():
    try:
        data = request.form
        roll_number = data.get("roll_number")
        if not roll_number:
            return ErpResponse(False, "Roll Number not provided", status_code=400).to_response()

        session = requests.Session()
        secret_question = erp.get_secret_question(
            headers=headers, session=session, roll_number=roll_number, log=True)
        sessionToken = erp_utils.get_cookie(session, 'JSESSIONID')

        return ErpResponse(True, data={
            "SECRET_QUESTION": secret_question,
            "SESSION_TOKEN": sessionToken
        }).to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()


@app.route("/request-otp", methods=["POST"])
def request_otp():
    try:
        sessionToken = request.headers["Session-Token"]
        if not sessionToken:
            return ErpResponse(False, "Session-Token header not found", status_code=400).to_response()

        data = request.form
        roll_number = data.get("roll_number")
        password = data.get("password")
        secret_answer = data.get("secret_answer")
        if not all([roll_number, password, secret_answer]):
            return ErpResponse(False, "Missing roll_number or password or secret answer", status_code=400).to_response()

        login_details = erp.get_login_details(
            ROLL_NUMBER=roll_number,
            PASSWORD=password,
            secret_answer=secret_answer,
            sessionToken=sessionToken
        )

        session = requests.Session()
        erp_utils.set_cookie(session, 'JSESSIONID', sessionToken)
        erp.request_otp(headers=headers, session=session,
                        login_details=login_details, log=True)

        return ErpResponse(True, message="OTP has been sent to your connected email accounts").to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()


@app.route("/login", methods=["POST"])
def login():
    try:
        sessionToken = request.headers["Session-Token"]
        if not sessionToken:
            return ErpResponse(False, "Session-Token header not found", status_code=400).to_response()

        data = request.form
        roll_number = data.get("roll_number")
        password = data.get("password")
        secret_answer = data.get("secret_answer")
        otp = data.get("otp")
        if not all([roll_number, password, secret_answer, otp]):
            return ErpResponse(False, "Missing roll_number or password or secret answer or otp", status_code=400).to_response()

        login_details = erp.get_login_details(
            ROLL_NUMBER=roll_number,
            PASSWORD=password,
            secret_answer=secret_answer,
            sessionToken=sessionToken
        )
        login_details["email_otp"] = otp

        session = requests.Session()
        erp_utils.set_cookie(session, 'JSESSIONID', sessionToken)
        ssoToken = erp.signin(headers=headers, session=session,
                              login_details=login_details, log=True)

        return ErpResponse(True, data={
            "ssoToken": ssoToken
        }).to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()


@app.route('/elective/<elective>', methods=["POST"])
def elective(elective):
    try:
        ssoToken = request.headers["SSO-Token"]
        if not ssoToken:
            return ErpResponse(False, "User not logged in.", status_code=401).to_response()

        data = request.form
        ROLL_NUMBER = data.get("roll_number")
        if not ROLL_NUMBER:
            return ErpResponse(False, "Roll Number not provided", status_code=400).to_response()
        DEPT = ROLL_NUMBER[2:4]
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month in [1, 2, 3, 4, 5, 6]:
            semester = "SPRING"
            acad_session = str(current_year - 1) +'-'+ str(current_year)
            year = current_year - int("20"+ROLL_NUMBER[:2]) - 1
        elif current_month in [7, 8, 9, 10, 11, 12]:
            semester = "AUTUMN"
            acad_session = str(current_year) +'-'+ str(current_year + 1)
            year = current_year - int("20"+ROLL_NUMBER[:2])
        
        semester = data.get("semester") if data.get("semester") else semester
        acad_session = data.get("session") if data.get("session") else acad_session
        year = int(data.get("year"))-1 if data.get("year") else year

        responses = gyfe.fetch_response(acad_session, semester, year, elective, DEPT, ssoToken)

        if not all(responses):
            return ErpResponse(False, "Failed to retrieve data..", status_code=500).to_response()

        if elective == "breadth":
            file = gyfe.save_breadths(responses, False)
        elif elective == "depth":
            file = gyfe.save_depths(responses, False)
        
        csv = io.BytesIO()
        csv.write(file.encode('utf-8'))
        csv.seek(0)
        
        return send_file(
            csv,
            as_attachment=True,
            mimetype='text/csv',
            download_name=f"${elective}_{ROLL_NUMBER}.csv"
        )

    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()
