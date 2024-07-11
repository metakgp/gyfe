from flask import Flask, request, jsonify, after_this_request, send_from_directory
import iitkgp_erp_login.erp as erp
import iitkgp_erp_login.utils as erp_utils
import logging
import gyfe
from datetime import datetime
import requests
from flask_cors import CORS
import os
from typing import Dict, List

app = Flask(__name__)
CORS(app)
headers = {
    "timeout": "20",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
}


def check_missing_fields(all_fields: Dict[str, str]) -> List[str]:
    return [field for field, value in all_fields.items() if not value]


class ErpResponse:
    def __init__(
        self,
        success: bool,
        message: str = None,
        data: dict = None,
        status_code: int = 200,
    ):
        self.success = success
        self.message = message
        self.data = data or {}
        self.status_code = status_code

        if not success:
            logging.error(f" {message}")

    def to_dict(self):
        response = {"status": "success" if self.success else "error"}
        if self.message:
            response["message"] = self.message
        if self.data:
            response |= self.data
        return response

    def to_response(self):
        return jsonify(self.to_dict()), self.status_code


@app.route("/secret-question", methods=["POST"])
def get_secret_question():
    try:
        data = request.form
        all_fields = {
            "roll_number": data.get("roll_number"),
        }
        missing = check_missing_fields(all_fields)
        if len(missing) > 0:
            return ErpResponse(
                False, f"Missing Fields: {", ".join(missing)}", status_code=400
            ).to_response()

        session = requests.Session()
        secret_question = erp.get_secret_question(
            headers=headers,
            session=session,
            roll_number=all_fields["roll_number"],
            log=True,
        )
        sessionToken = erp_utils.get_cookie(session, "JSESSIONID")

        return ErpResponse(
            True,
            data={"SECRET_QUESTION": secret_question, "SESSION_TOKEN": sessionToken},
        ).to_response()
    except erp.ErpLoginError as e:
        return ErpResponse(False, str(e), status_code=401).to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()


@app.route("/request-otp", methods=["POST"])
def request_otp():
    try:
        data = request.form
        all_fields = {
            "roll_number": data.get("roll_number"),
            "password": data.get("password"),
            "secret_answer": data.get("secret_answer"),
            "sessionToken": request.headers["Session-Token"],
        }
        missing = check_missing_fields(all_fields)
        if len(missing) > 0:
            return ErpResponse(
                False, f"Missing Fields: {", ".join(missing)}", status_code=400
            ).to_response()

        login_details = erp.get_login_details(
            ROLL_NUMBER=all_fields["roll_number"],
            PASSWORD=all_fields["password"],
            secret_answer=all_fields["secret_answer"],
            sessionToken=all_fields["sessionToken"],
        )

        session = requests.Session()
        erp_utils.set_cookie(session, "JSESSIONID", all_fields["sessionToken"])
        erp.request_otp(
            headers=headers, session=session, login_details=login_details, log=True
        )

        return ErpResponse(
            True, message="OTP has been sent to your connected email accounts"
        ).to_response()
    except erp.ErpLoginError as e:
        return ErpResponse(False, str(e), status_code=401).to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.form
        all_fields = {
            "roll_number": data.get("roll_number"),
            "password": data.get("password"),
            "secret_answer": data.get("secret_answer"),
            "otp": data.get("otp"),
            "sessionToken": request.headers["Session-Token"],
        }
        missing = check_missing_fields(all_fields)
        if len(missing) > 0:
            return ErpResponse(
                False, f"Missing Fields: {", ".join(missing)}", status_code=400
            ).to_response()

        login_details = erp.get_login_details(
            ROLL_NUMBER=all_fields["roll_number"],
            PASSWORD=all_fields["password"],
            secret_answer=all_fields["secret_answer"],
            sessionToken=all_fields["sessionToken"],
        )
        login_details["email_otp"] = all_fields["otp"]

        session = requests.Session()
        erp_utils.set_cookie(session, "JSESSIONID", all_fields["sessionToken"])
        ssoToken = erp.signin(
            headers=headers, session=session, login_details=login_details, log=True
        )

        return ErpResponse(True, data={"ssoToken": ssoToken}).to_response()
    except erp.ErpLoginError as e:
        return ErpResponse(False, str(e), status_code=401).to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()


@app.route("/elective/<elective>", methods=["POST"])
def elective(elective):
    try:
        data = request.form
        all_fields = {
            "roll_number": data.get("roll_number"),
            "ssoToken": request.headers["SSO-Token"],
        }
        missing = check_missing_fields(all_fields)
        if len(missing) > 0:
            return ErpResponse(
                False, f"Missing Fields: {", ".join(missing)}", status_code=400
            ).to_response()

        DEPT = all_fields["roll_number"][2:4]
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month in [1, 2, 3, 4, 5, 6]:
            semester = "SPRING"
            acad_session = f"{str(current_year - 1)}-{str(current_year)}"
            year = current_year - int("20" + all_fields["roll_number"][:2]) - 1
        elif current_month in [7, 8, 9, 10, 11, 12]:
            semester = "AUTUMN"
            acad_session = f"{str(current_year)}-{str(current_year + 1)}"
            year = current_year - int("20" + all_fields["roll_number"][:2])

        semester = data.get("semester") or semester
        acad_session = data.get("session") or acad_session
        year = int(data.get("year")) - 1 if data.get("year") else year

        responses = gyfe.fetch_response(
            acad_session, semester, year, elective, DEPT, all_fields["ssoToken"]
        )

        if not all(responses):
            return ErpResponse(
                False,
                "Failed to retrieve data..",
                status_code=500,
            ).to_response()

        if elective == "breadth":
            file_path = gyfe.save_breadths(responses, False, file_type="xlsx")
        elif elective == "depth":
            file_path = gyfe.save_depths(responses, False, file_type="xlsx")

        file_path = f"{file_path}.xlsx"

        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
            except Exception as error:
                app.logger.error(
                    "Error removing or closing downloaded file handle", error
                )
            return response

        mydir = os.getcwd()
        return send_from_directory(path=file_path, directory=mydir, as_attachment=True)
    except erp.ErpLoginError as e:
        return ErpResponse(False, str(e), status_code=401).to_response()
    except Exception as e:
        return ErpResponse(False, str(e), status_code=500).to_response()
