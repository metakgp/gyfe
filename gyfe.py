# scrape depth electives
import requests
import iitkgp_erp_login.erp as erp
import iitkgp_erp_login.utils as erp_utils
from bs4 import BeautifulSoup as bs
import pandas as pd
import argparse
from tabulate import tabulate
import re
import json

DEPT : str = None

try:
    import erpcreds
    DEPT = erpcreds.ROLL_NUMBER[2:4]
    manual = False
except:
    manual  = True

def parse_args():
    parser = argparse.ArgumentParser(description="Get depth electives from ERP")
    parser.add_argument("electives", type=str, help="breadth/depth")
    parser.add_argument("--notp", action="store_true", help="Enter OTP manually")
    parser.add_argument(
        "--year", type=int, help="Year of study (single digit)", required=True
    )
    parser.add_argument(
        "--session", type=str, default="2023-2024", help="Session (eg. 2023-2024)"
    )
    parser.add_argument(
        "--semester", type=str, default="SPRING", help="Semester (AUTUMN/SPRING)"
    )
    return parser.parse_args()

def find_core_courses(response: requests.Response) -> list[str]:
    #Get code of core courses
    core_course_codes = []
    try:
        core_courses = response.json()
    except:
        core_courses = {}
    
    for course in core_courses:
        if course['subtype'] == 'Depth CORE':
            core_course_codes.append(course['subno'])
    
    return core_course_codes

def find_all_unavailable_slots(unavailable_slots: list[str]) -> list[str]:
    all_unavailable_slots :list = []

    # overlappings between lab and theory slots
    with open("overlaps.json", "r") as f:
        overlaps = json.load(f)
 
    # some have more than 1 slot, they are separated
    for slot in unavailable_slots:
        if "," in slot:
            for s in slot.split(","):
                unavailable_slots.append(s.strip())
            # remove the original slot
            unavailable_slots.remove(slot)

    for slot in unavailable_slots:
        if len(slot) == 1:
            # it is a lab slot; check for overlap from overlaps.json
            all_unavailable_slots.extend(overlaps[slot])
            all_unavailable_slots.append(slot)

        # else, if there is F3 slot for example, add F2, F4 to unavailable slots, and vice versa similarly for whatever letters are there
        else:
            try:
                all_unavailable_slots.append(slot[0] + "2")
                all_unavailable_slots.append(slot[0] + "3")
                all_unavailable_slots.append(slot[0] + "4")
            except:
                pass

            # check if there are any lab slots overlapping with it
            for parent, slots in overlaps.items():
                if slot in slots:
                    all_unavailable_slots.append(parent)

    # remove duplicates if any
    all_unavailable_slots = list(set(all_unavailable_slots))

    return all_unavailable_slots

def save_depths(response :tuple, create_file:bool =True):
    """
    Workflow:
            - Check DeptWise timetable and scrape subjects
            - Make sure those subjects are not overlapping with core courses
                    - Subtask: find core courses
            - Go to Deptwise subject list to additionally scrape prof name and slot
    
    Parameters:
        response (tuple): Tuple containing three elements of requests.Response objects.
        create_file (bool): Flag to create a file or return the data as a string. Default is True.
        
    Returns:
        None or str: If create_file is False, returns the CSV string of available depth electives.
    """

    soup = bs(response[0].text, "html.parser")

    with open("minors.json", "r") as f:
        minors = json.load(f)

    # Find all the rows of the table containing course details
    rows = soup.find_all("tr")

    depth_course_codes = []
    venues = []

    # Loop through each row and extract the course details
    for row in rows:
        cells = row.find_all("td", align="center")
        # pattern = r"([A-Z0-9\s-]+)<br/>([A-Z0-9\s-]+)"  # compulsory courses have prof mentioned in 2nd line, using this to filter out
        for cell in cells:
            a_tag = cell.find("a")
            # matches = re.findall(pattern, str(a_tag))
            try:
                matches = a_tag.find_all(string=True)
            except:
                matches = []
            if len(matches) > 1:
                course_code = matches[0]
                depth_course_codes.append(course_code)

    data = {"Course Code": depth_course_codes}
    df_depths = pd.DataFrame(data=data)
    df_depths.drop_duplicates(subset=["Course Code"], inplace=True)

    # * Get code of core courses
    core_course_codes = find_core_courses(response[2])

    #* Remove core courses from depths
    df_depths = df_depths[~df_depths["Course Code"].isin(core_course_codes)]

    # * Now get prof names and slots
    soup = bs(response[1].text, "html.parser")

    #* Extract course information from the table rows
    courses = []
    parentTable = soup.find("table", {"id": "disptab"})
    rows = parentTable.find_all("tr")

    try:
        cc = course_code.strip()
    except:
        cc = None
    
    for row in rows[1:]:
        if "bgcolor" in row.attrs:
            continue
        cells = row.find_all("td")
        course = {
                "Course Code": cells[0].text.strip() if len(cells) > 0 else None,
                "Name": cells[1].text.strip() if len(cells) > 1 else None,
                "Faculty": cells[2].text.strip() if len(cells) > 2 else None,
                "LTP": cells[3].text.strip() if len(cells) > 3 else None,
                "Slot": cells[5].text.strip() if len(cells) > 5 else None,
                "Room": cells[6].text.strip() if len(cells) > 6 else None,
                "Minor": "-"
            }

        # adding which minor the course helps you get
        course_list = list(minors.keys())
        code_list = list(minors.values())
        for lst in code_list:
            pos = code_list.index(lst)
            for ele in lst:
                if cc == ele:
                    course["Minor"] = course_list[pos]

        courses.append(course)

    df_all = pd.DataFrame(data=courses)

    # find slot of core courses
    unavailable_slots = (
        df_all[df_all["Course Code"].isin(core_course_codes)]["Slot"].unique().tolist()
    )

    all_unavailable_slots = find_all_unavailable_slots(unavailable_slots)

    # get depth courses
    df_all = df_all[df_all["Course Code"].isin(df_depths["Course Code"])]

    # remove courses with unavailable slots
    df_all = df_all[~df_all["Slot"].isin(all_unavailable_slots)]

    df_all.set_index("Course Code", inplace=True)

    # save available electives
    if create_file:
        with open("available_depths.txt", "w") as f:
            f.write(tabulate(df_all, headers="keys", tablefmt="fancy_grid"))
        print("Available depths saved to available_depths.txt")
    else:
        return df_all.to_csv(index=False)
       
def save_breadths(response :tuple, create_file:bool =True):
    """
    Workflow:
            - Check breadth list to get all breadth electives
            - Similar to save_depths, find unavailable slots and filter breadth electives

    Parameters:
        response (tuple): Tuple containing three elements of requests.Response objects.
        create_file (bool): Flag to create a file or return the data as a string. Default is True.
        
    Returns:
        None or str: If create_file is False, returns the CSV string of available breadth electives.
    """

    soup = bs(response[0].text, "html.parser")

    with open("minors.json", "r") as f:
        minors = json.load(f)

    # each "tr" contains a course
    rows = soup.find_all("tr")

    courses = []

    for row in rows:
        # Extract the data within the 'td' tags
        cells = row.find_all("td")
        if len(cells) >= 8:
            course = {}
            course_code_input = cells[0].find("input", {"name": "subno"})
            course_code = course_code_input["value"]
            course["Course Code"] = course_code.strip()
            course["Name"] = cells[1].text.strip()

            course["LTP"] = cells[2].text.strip()

            prereq_str = ""
            for i in range(3, 6):
                if cells[i].text.strip() != "":
                    prereq_str += cells[i].text.strip() + ", "

            # remove trailing comma and space
            if prereq_str != "":
                course["Prerequisites"] = prereq_str[:-2]
            else:
                course["Prerequisites"] = "No prerequisites"

            dep_input = cells[0].find("input", {"name": "dept"})
            dep = dep_input["value"]
            course["Department"] = dep.strip()

            # adding which minor the course helps you get
            course["Minor"] = "-"
            course_list = list(minors.keys())
            code_list = list(minors.values())
            for lst in code_list:
                pos = code_list.index(lst)
                for ele in lst:
                    if course_code.strip() == ele:
                        course["Minor"] = course_list[pos]

            # slots is of the form {X}, we need just X
            if cells[7].text.strip() == "":
                course["Slot"] = "Not alloted yet"
            else:
                course["Slot"] = cells[7].text.strip()[1:-1]

            if cells[8].text.strip() == "":
                course["Venue"] = "Not alloted yet"
            else:
                course["Venue"] = cells[8].text.strip()

            courses.append(course)

    # Create a pandas DataFrame with the scraped data
    df = pd.DataFrame(data=courses)

    # for some reason, some empty slots are not being replaced
    df["Slot"].replace("", "Not alloted yet", inplace=True)

    core_course_codes = find_core_courses(response[2])

    # * find unavailable slots
    soup = bs(response[1].text, "html.parser")

    # Extract course information from the table rows
    courses = []
    parentTable = soup.find("table", {"id": "disptab"})
    rows = parentTable.find_all("tr")

    for row in rows[1:]:
        if "bgcolor" in row.attrs:
            continue
        cells = row.find_all("td")
        course = {}
        course["Course Code"] = cells[0].text
        try:
            course["Slot"] = cells[5].text
        except:
            course["Slot"] = None
        courses.append(course)

    df_all = pd.DataFrame(data=courses)

    # find slot of core courses
    unavailable_slots = (
        df_all[df_all["Course Code"].isin(core_course_codes)]["Slot"].unique().tolist()
    )

    all_unavailable_slots = find_all_unavailable_slots(unavailable_slots)

    # * remove courses with unavailable slots
    df = df[~df["Slot"].str.contains("|".join(all_unavailable_slots), na=False)]
    df.set_index("Course Code", inplace=True)
    # save available electives
    if create_file:
        with open("available_breadths.txt", "w") as f:
            f.write(tabulate(df, headers="keys", tablefmt="fancy_grid"))
        print("Available electives saved to available_breadths.txt")
    else:
        return df.to_csv(index=False)

def fetch_response(SESSION, SEMESTER, YEAR, ELECTIVE, DEPT, ssoToken) -> tuple[requests.Response, ...]:
    headers = {
        "timeout": "20",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
    }

    session = requests.Session()
    erp_utils.set_cookie(session, 'ssoToken', ssoToken)

    TIMETABLE_URL: str = f'https://erp.iitkgp.ac.in/Acad/view/dept_final_timetable.jsp?action=second&course={DEPT}&session={SESSION}&index={YEAR}&semester={SEMESTER}&dept={DEPT}'
    ERP_ELECTIVES_URL: str = "https://erp.iitkgp.ac.in/Acad/central_breadth_tt.jsp"
    
    if ELECTIVE == "depth":
        SUBJ_LIST_URL: str = f'https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&for_session={SESSION}&for_semester={SEMESTER}&dept={DEPT}'
        TIMETABLE_RESP: requests.Response = session.get(TIMETABLE_URL, headers=headers)
        ERP_ELECTIVES_RESP: requests.Response = None
    elif ELECTIVE == "breadth":
        SUBJ_LIST_URL: str = f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&dept={DEPT}"
        ERP_ELECTIVES_RESP: requests.Response = session.get(ERP_ELECTIVES_URL, headers=headers)
        TIMETABLE_RESP: requests.Response = None
    
    semester: int = 2 * YEAR - 1 if SEMESTER == "AUTUMN" else 2 * YEAR
    COURSES_URL: str = f"https://erp.iitkgp.ac.in/Academic/student_performance_details_ug.htm?semno={semester}"

    SUBJ_LIST_RESP: requests.Response = session.get(SUBJ_LIST_URL, headers=headers)
    COURSES_RESP: requests.Response = session.post(COURSES_URL, headers=headers)

    if ELECTIVE == "depth":
        return (TIMETABLE_RESP, SUBJ_LIST_RESP, COURSES_RESP)
    elif ELECTIVE == "breadth":
        return (ERP_ELECTIVES_RESP, SUBJ_LIST_RESP, COURSES_RESP)

def main():
    args = parse_args()
    
    session = requests.Session()
    headers = {
        "timeout": "20",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
    }

    if manual:
        _, ssoToken = erp.login(
            headers,
            session,
            LOGGING=True,
            SESSION_STORAGE_FILE=".session"
        )
        if erp.ROLL_NUMBER:
            DEPT = erp.ROLL_NUMBER[2:4]
        else:
            DEPT = input("Enter your department code: ")
    else:
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

    SESSION = args.session
    SEMESTER = args.semester
    YEAR = args.year -1
    ELECTIVE = args.electives

    if args.electives == "breadth":
        responses = fetch_response(SESSION, SEMESTER, YEAR, ELECTIVE, DEPT, ssoToken)
        save_breadths(responses)
        depth = input("Do you want to get depth also? (y/N) [Default: no]: ").lower()
        if depth == 'y':
            ELECTIVE = "depth"
            response = fetch_response(args_dict, session)
            save_depths(responses)

    elif args.electives == "depth":
        responses = fetch_response(SESSION, SEMESTER, YEAR, ELECTIVE, DEPT, ssoToken)
        save_depths(responses)
        breadth = input("Do you want to get breadth also? (y/N) [Default: no]: ").lower()
        if breadth == 'y':
            ELECTIVE = "breadth"
            responses = fetch_response(SESSION, SEMESTER, YEAR, ELECTIVE, DEPT, ssoToken)
            save_breadths(responses)

    else:
        print("Invalid electives type. Choose from 'breadth' or 'depth'")

if __name__ == "__main__":
    main()