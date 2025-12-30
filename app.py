from flask import (
    Flask,
    request,
    jsonify,
    after_this_request,
    send_from_directory,
)
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
    "User-Agent": "Mozilla/5.0",
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
            logging.error(message)

    def to_dict(self):
        response = {"status": "success" if self.success else "error"}
        if self.message:
            response["message"] = self.message
        if self.data:
            response.update(self.data)
        return response

    def to_response(self):
        return jsonify(self.to_dict()), self.status_code


@app.route("/secret-question", methods=["POST"])
def get_secret_question():
    try:
        data = request.form
        all_fields = {"roll_number": data.get("roll_number")}

        missing = check_missing_fields(all_fields)
        if missing:
            return ErpResponse(
                False, f"Missing Fields: {', '.join(missing)}", 400
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
            data={
                "SECRET_QUESTION": secret_question,
                "SESSION_TOKEN": sessionToken,
            },
        ).to_response()

    except Exception as e:
        return ErpResponse(False, str(e), 500).to_response()


@app.route("/request-otp", methods=["POST"])
def request_otp():
    try:
        data = request.form
        all_fields = {
            "roll_number": data.get("roll_number"),
            "password": data.get("password"),
            "secret_answer": data.get("secret_answer"),
            "sessionToken": request.headers.get("Session-Token"),
        }

        missing = check_missing_fields(all_fields)
        if missing:
            return ErpResponse(
                False, f"Missing Fields: {', '.join(missing)}", 400
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
            True, message="OTP sent successfully"
        ).to_response()

    except Exception as e:
        return ErpResponse(False, str(e), 500).to_response()


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.form
        all_fields = {
            "roll_number": data.get("roll_number"),
            "password": data.get("password"),
            "secret_answer": data.get("secret_answer"),
            "otp": data.get("otp"),
            "sessionToken": request.headers.get("Session-Token"),
        }

        missing = check_missing_fields(all_fields)
        if missing:
            return ErpResponse(
                False, f"Missing Fields: {', '.join(missing)}", 400
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

    except Exception as e:
        return ErpResponse(False, str(e), 500).to_response()


@app.route("/elective/<elective>", methods=["POST"])
def elective(elective):
    try:
        data = request.form
        view = request.args.get("view")  # list or download

        all_fields = {
            "roll_number": data.get("roll_number"),
            "ssoToken": request.headers.get("SSO-Token"),
        }

        missing = check_missing_fields(all_fields)
        if missing:
            return ErpResponse(
                False, f"Missing Fields: {', '.join(missing)}", 400
            ).to_response()

        session = requests.Session()
        erp_utils.set_cookie(session, "ssoToken", all_fields["ssoToken"])

        if not erp.session_alive(session=session):
            return ErpResponse(
                False, "Session expired. Please login again.", 401
            ).to_response()

        DEPT = all_fields["roll_number"][2:4]
        now = datetime.now()

        if now.month <= 6:
            semester = "SPRING"
            acad_session = f"{now.year - 1}-{now.year}"
            year = now.year - int("20" + all_fields["roll_number"][:2])
        else:
            semester = "AUTUMN"
            acad_session = f"{now.year}-{now.year + 1}"
            year = now.year - int("20" + all_fields["roll_number"][:2]) + 1

        responses = gyfe.fetch_response(
            acad_session,
            semester,
            year,
            elective,
            DEPT,
            all_fields["ssoToken"],
        )

        if not responses:
            return ErpResponse(False, "Failed to retrieve data.", 500).to_response()

        # ✅ LIST MODE (Frontend rendering)
        if view == "list":
            return ErpResponse(True, data={"items": responses}).to_response()

        # ⬇️ DEFAULT: DOWNLOAD MODE
        if elective == "breadth":
            file_path = gyfe.save_breadths(responses, False, "xlsx")
        else:
            file_path = gyfe.save_depths(responses, False, "xlsx")

        file_path = f"{file_path}.xlsx"

        @after_this_request
        def cleanup(response):
            try:
                os.remove(file_path)
            except Exception:
                pass
            return response

        return send_from_directory(
            directory=os.getcwd(),
            path=file_path,
            as_attachment=True,
        )

    except Exception as e:
        return ErpResponse(False, str(e), 500).to_response()
