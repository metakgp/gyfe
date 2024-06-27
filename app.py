from flask import Flask, render_template, request, make_response, jsonify
import requests
import logging
from iitkgp_erp_login import session_manager, erp
import gyfe
import io
app = Flask(__name__)


jwt_secret_key :str = "secret-key"
headers = {
        "timeout": "20",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
    }

session_manager = session_manager.SessionManager(jwt_secret_key=jwt_secret_key, headers=headers)

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

def handle_auth() -> ErpResponse:
    if "Authorization" in request.headers:
        header = request.headers["Authorization"].split(" ")
        if len(header) == 2:
            return ErpResponse(True, data={
                "jwt": header[1]
            }).to_response()
        else:
            return ErpResponse(False, "Poorly formatted authorization header. Should be of format 'Bearer <token>'", status_code=401).to_response()
    else:
        return ErpResponse(False, "Authentication token not provided", status_code=401).to_response()


    
@app.route("/secret-question", methods=["POST"])
def get_secret_question():
    try:
        data = request.form
        roll_number = data.get("roll_number")
        if not roll_number:
            return ErpResponse(False, "Roll Number not provided", status_code=400).to_response()

        secret_question, jwt = session_manager.get_secret_question(
            roll_number)
        return ErpResponse(True, data={
            "secret_question": secret_question,
            "jwt": jwt
        }).to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()

@app.route("/request-otp", methods=["POST"])
def request_otp():
    try:
        jwt = None
        auth_resp, status_code = handle_auth()
        if status_code != 200:
            return auth_resp, status_code
        else:
            jwt = auth_resp.get_json().get("jwt")

        password = request.form.get("password")
        secret_answer = request.form.get("secret_answer")
        if not all([password, secret_answer]):
            return ErpResponse(False, "Missing password or secret answer", status_code=400).to_response()

        session_manager.request_otp(jwt, password, secret_answer)
        return ErpResponse(True, message="OTP has been sent to your connected email accounts").to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()

@app.route("/login", methods=["POST"])
def login():
    try:
        jwt = None
        auth_resp, status_code = handle_auth()
        if status_code != 200:
            return auth_resp, status_code
        else:
            jwt = auth_resp.get_json().get("jwt")

        password = request.form.get("password")
        secret_answer = request.form.get("secret_answer")
        otp = request.form.get("otp")
        if not all([secret_answer, password, otp]):
            return ErpResponse(False, "Missing password, secret answer or otp", status_code=400).to_response()

        session_manager.login(jwt, password, secret_answer, otp)
        return ErpResponse(True, message="Logged in to ERP").to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()

@app.route("/logout", methods=["GET"])
def logout():
    try:
        jwt = None
        auth_resp, status_code = handle_auth()
        if status_code != 200:
            return auth_resp, status_code
        else:
            jwt = auth_resp.get_json().get("jwt")

        session_manager.end_session(jwt=jwt)

        return ErpResponse(True, message="Logged out of ERP").to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()

@app.route('/get_csv', methods=["POST"])
def get_csv():
    try:
        jwt = None
        auth_resp, status_code = handle_auth()
        if status_code != 200:
            return auth_resp, status_code
        else:
            jwt = auth_resp.get_json().get("jwt")
        
        class argument:
            def __init__(self, session = None, semester= None, year= None, electives= None):
                self.session = session
                self.semester = semester
                self.year = int(year)
                self.notp = True
                self.electives = electives
        
        args = argument(request.form.get('session'), request.form.get('semester'), request.form.get('year'), request.form.get('electives'))
        
        if not all ([args.session, args.semester, args.year, args.notp, args.electives]):
            return ErpResponse(False, "Missing args for csv file.", status_code=400).to_response()
        
        _, ssoToken = session_manager.get_erp_session(jwt=jwt)

        with open('new.txt', 'w') as file:
            file.write("START\n")
            file.write(ssoToken)
            file.write("\nEND")

        session = requests.Session()
        session.cookies.clear()
        session.cookies.set('ssoToken', ssoToken, domain='erp.iitkgp.ac.in')

        if args.electives == "breadth":
            file = gyfe.save_breadths(args, session, False)
        elif args.electives == "depth":
            file = gyfe.save_depths(args, session, False)
        
        buffer = io.StringIO()
        buffer.write(file)
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=data.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response  


    except Exception as e:
        logging.error(f" {e}")
        return ErpResponse(False, str(e), status_code=500).to_response()
    
    
    
