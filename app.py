from flask import Flask, render_template, request, make_response
import requests
import iitkgp_erp_login.erp as erp
import erpcreds
import gyfe
import io
app = Flask(__name__)


headers = {
   'timeout': '20',
   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36',
}
session = requests.Session()

class args:
    def __init__(self):
        self.session = "2023-2024"
        self.semester = "AUTUMN"
        self.year = 3
        self.notp = True
        self.electives = "depth"

args = args()
if args.notp:
        _, ssoToken = erp.login(
            headers,
            session,
            ERPCREDS=erpcreds,
            LOGGING=True,
            SESSION_STORAGE_FILE=".session",
        )
else:
        _, ssoToken = erp.login(
            headers,
            session,
            ERPCREDS=erpcreds,
            OTP_CHECK_INTERVAL=2,
            LOGGING=True,
            SESSION_STORAGE_FILE=".session",
        )

@app.route('/get_csv')
def get_csv():
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
    
    
    
    
