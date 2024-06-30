from flask import Flask, request, send_file, jsonify
import logging
from iitkgp_erp_login import session_manager
import gyfe
import io
import os
import jwt as jwt_gen
from dotenv import load_dotenv
from datetime import datetime

app = Flask(__name__)

load_dotenv()
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

if not app.config['JWT_SECRET_KEY']:
    raise ValueError("No JWT_SECRET_KEY set for Flask application")

jwt_secret_key = app.config['JWT_SECRET_KEY']
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
        data = request.get_json()
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

        data = request.get_json()
        password = data.get("password")
        secret_answer = data.get("secret_answer")
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

        data = request.get_json()
        password = data.get("password")
        secret_answer = data.get("secret_answer")
        otp = data.get("otp")
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

@app.route('/elective/<ELECTIVE>', methods=["GET"])
def elective(ELECTIVE):
    try:
        jwt = None
        auth_resp, status_code = handle_auth()
        if status_code != 200:
            return auth_resp, status_code
        else:
            jwt = auth_resp.get_json().get("jwt")
        
        ROLL_NUMBER = jwt_gen.decode(jwt, jwt_secret_key, algorithms=['HS256'])["roll_number"]

        YEAR = int(ROLL_NUMBER[1])
        DEPT = ROLL_NUMBER[2:4]
        current_month = datetime.now().month
        if current_month in [12, 1, 2, 3, 4, 5]:
            SEMESTER = "SPRING"
            SESSION = str(datetime.now().year - 1) +'-'+ str(datetime.now().year)
        elif current_month in [6, 7, 8, 9, 10, 11]:
            SEMESTER = "AUTUMN"
            SESSION = str(datetime.now().year) +'-'+ str(datetime.now().year + 1)
        
        """
        save_depth and save_breadth needs 2 responses, that is PRIMARY_RESP and SUBJ_LIST_RESP,
        both function calls find_core_courses inside them, which requires COURSES_RESP to run.

        fetching all the responses and making a tuple named "response" and passing to gyfe.save_depths() or gyfe.save_breadths().
        """

        TIMETABLE_URL = f"https://erp.iitkgp.ac.in/Acad/view/dept_final_timetable.jsp?action=second&course={DEPT}&session={SESSION}&index={YEAR}&semester={SEMESTER}&dept={DEPT}"
        ERP_ELECTIVES_URL = "https://erp.iitkgp.ac.in/Acad/central_breadth_tt.jsp"

        if ELECTIVE== "depth":
            SUBJ_LIST_URL = f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&for_session={SESSION}&for_semester={SEMESTER}&dept={DEPT}"
            PRIMARY_RESP = session_manager.request(jwt=jwt, method='GET', url=TIMETABLE_URL, headers=headers)
        elif ELECTIVE == "breadth":
            SUBJ_LIST_URL = f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&dept={DEPT}"
            PRIMARY_RESP = session_manager.request(jwt=jwt, method='GET', url=ERP_ELECTIVES_URL, headers=headers)
        else:
            return ErpResponse(False, "Invalid elective type.", status_code=404).to_response()
        
        semester = 2 * YEAR - 1 if SEMESTER=="AUTUMN" else 2 * YEAR
        COURSES_URL = f"https://erp.iitkgp.ac.in/Academic/student_performance_details_ug.htm?semno={semester}"

        SUBJ_LIST_RESP = session_manager.request(jwt=jwt, method='GET', url=SUBJ_LIST_URL, headers=headers)
        COURSES_RESP = session_manager.request(jwt=jwt, method='POST', url=COURSES_URL, headers=headers)

        response = (PRIMARY_RESP, SUBJ_LIST_RESP, COURSES_RESP) 

        if not all(response):
            return ErpResponse(False, "Failed to retrieve data..", status_code=500).to_response()

        if ELECTIVE == "breadth":
            file = gyfe.save_breadths(response, False)
        elif ELECTIVE == "depth":
            file = gyfe.save_depths(response, False)
        
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