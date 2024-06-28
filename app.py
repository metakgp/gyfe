from flask import Flask, render_template, request, send_file, jsonify
import requests
import logging
from iitkgp_erp_login import session_manager
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

@app.route('/fetch-csvfile', methods=["POST"])
def fetch_csvfile():
    try:
        jwt = None
        auth_resp, status_code = handle_auth()
        if status_code != 200:
            return auth_resp, status_code
        else:
            jwt = auth_resp.get_json().get("jwt")
        
        data = request.get_json()
        SESSION = data.get('session')
        SEMESTER = data.get('semester')
        YEAR = int(data.get('year'))
        ELECTIVES = data.get('electives')
        DEPT = data.get('dept')
        
        if not all([SESSION, SEMESTER, YEAR, ELECTIVES]):
            return ErpResponse(False, "Missing args to create the csv file.", status_code=400).to_response()
        
        headers = {
            "timeout": "20",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
        }

        TIMETABLE_URL = f"https://erp.iitkgp.ac.in/Acad/view/dept_final_timetable.jsp?action=second&course={DEPT}&session={SESSION}&index={YEAR}&semester={SEMESTER}&dept={DEPT}"
        ERP_ELECTIVES_URL = "https://erp.iitkgp.ac.in/Acad/central_breadth_tt.jsp"

        if ELECTIVES== "depth":
            SUBJ_LIST_URL = f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&for_session={SESSION}&for_semester={SEMESTER}&dept={DEPT}"
            response_1 = session_manager.request(jwt=jwt, method='GET', url=TIMETABLE_URL, headers=headers)
        
        elif ELECTIVES == "breadth":
            SUBJ_LIST_URL = f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&dept={DEPT}"
            response_1 = session_manager.request(jwt=jwt, method='GET', url=ERP_ELECTIVES_URL, headers=headers)

        else:
            return ErpResponse(False, "Invalid elective type.", status_code=400).to_response()
        
        semester = 2 * YEAR - 1 if SEMESTER=="AUTUMN" else 2 * YEAR
        COURSES_URL = f"https://erp.iitkgp.ac.in/Academic/student_performance_details_ug.htm?semno={semester}"

        response_2 = session_manager.request(jwt=jwt, method='GET', url=SUBJ_LIST_URL, headers=headers)
        response_3 = session_manager.request(jwt=jwt, method='POST', url=COURSES_URL, headers=headers)

        response = (response_1, response_2, response_3)

        if not all(response):
            return ErpResponse(False, "Failed to retrieve data..", status_code=500).to_response()

        if ELECTIVES == "breadth":
            file = gyfe.save_breadths(response, False)
        elif ELECTIVES == "depth":
            file = gyfe.save_depths(response, False)
        
        csv = io.BytesIO()
        csv.write(file.encode('utf-8'))
        csv.seek(0)
        
        return send_file(
            csv,
            as_attachment=True,
            mimetype='text/csv',
            download_name=f"$my_{ELECTIVES}.csv"
        )


    except Exception as e:
        logging.error(f" {e}")
        return ErpResponse(False, str(e), status_code=500).to_response()
    
    
    
