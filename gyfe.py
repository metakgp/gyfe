# scrape depth electives
import requests
import erpcreds
import iitkgp_erp_login.erp as erp
from bs4 import BeautifulSoup as bs
import pandas as pd
import argparse
from tabulate import tabulate
import re
import json

DEPT = erpcreds.ROLL_NUMBER[2:4]


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


def find_core_courses(headers, session, args):

    semester = 2 * args.year - 1 if args.semester == "AUTUMN" else 2 * args.year
    COURSES_URL = f"https://erp.iitkgp.ac.in/Academic/student_performance_details_ug.htm?semno={semester}"

    # * Get code of core courses
    core_course_codes = []
    response = session.post(COURSES_URL, headers=headers)
    core_courses = response.json()
    
    for course in core_courses:
        if course['subtype'] == 'Depth CORE':
            core_course_codes.append(course['subno'])
    
    return core_course_codes


def find_all_unavailable_slots(unavailable_slots):
    all_unavailable_slots = []

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


def save_depths(args):
    """
    Workflow:
            - Check DeptWise timetable and scrape subjects
            - Make sure those subjects are not overlapping with core courses
                    - Subtask: find core courses
            - Go to Deptwise subject list to additionally scrape prof name and slot
    """

    headers = {
        "timeout": "20",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
    }

    session = requests.Session()

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

    TIMETABLE_URL = f"https://erp.iitkgp.ac.in/Acad/view/dept_final_timetable.jsp?action=second&course={DEPT}&session={args.session}&index={args.year}&semester={args.semester}&dept={DEPT}"
    SUBJ_LIST_URL = f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&for_session={args.session}&for_semester={args.semester}&dept={DEPT}"


    # *First get list of depths
    response = session.get(TIMETABLE_URL, headers=headers)
    soup = bs(response.text, "html.parser")

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
            matches = a_tag.find_all(string=True)
            if len(matches) > 1:
                course_code = matches[0]
                depth_course_codes.append(course_code)

    data = {"Course Code": depth_course_codes}
    df_depths = pd.DataFrame(data=data)
    df_depths.drop_duplicates(subset=["Course Code"], inplace=True)

    # * Get code of core courses
    core_course_codes = find_core_courses(headers, session, args)

    #* Remove core courses from depths
    df_depths = df_depths[~df_depths["Course Code"].isin(core_course_codes)]

    # * Now get prof names and slots
    response = session.get(SUBJ_LIST_URL, headers=headers)
    soup = bs(response.text, "html.parser")

    #* Extract course information from the table rows
    courses = []
    parentTable = soup.find("table", {"id": "disptab"})
    rows = parentTable.find_all("tr")
    
    try:
        codes = course_code.strip()
    except:
        codes = "NIL"
    
    for row in rows[1:]:
        if "bgcolor" in row.attrs:
            continue
        cells = row.find_all("td")
        course = {}
        if len(cells) > 6:
            course["Course Code"] = cells[0].text
            course["Name"] = cells[1].text
            course["Faculty"] = cells[2].text
            course["LTP"] = cells[3].text
            course["Slot"] = cells[5].text
            course["Room"] = cells[6].text
        else:
            course["Course Code"] = "NIL"
            course["Name"] = "NIL"
            course["Faculty"] = "NIL"
            course["LTP"] = "NIL"
            course["Slot"] = "NIL"
            course["Room"] = "NIL"

        # adding which minor the course helps you get
        course["Minor"] = "-"
        course_list = list(minors.keys())
        code_list = list(minors.values())
        for lst in code_list:
            pos = code_list.index(lst)
            for ele in lst:
                if codes == ele:
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
    with open("available_depths.txt", "w") as f:
        f.write(tabulate(df_all, headers="keys", tablefmt="fancy_grid"))

    print("Available depths saved to available_depths.txt")


def save_breadths(args):
    """
    Workflow:
            - Check breadth list to get all breadth electives
            - Similar to save_depths, find unavailable slots and filter breadth electives
    """

    headers = {
        "timeout": "20",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
    }

    session = requests.Session()

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

    ERP_ELECTIVES_URL = "https://erp.iitkgp.ac.in/Acad/central_breadth_tt.jsp"
    SUBJ_LIST_URL = (
        f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&dept={DEPT}"
    )

    response = session.get(ERP_ELECTIVES_URL, headers=headers)

    soup = bs(response.text, "html.parser")

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

    core_course_codes = find_core_courses(headers, session, args)

    # * find unavailable slots
    response = session.get(SUBJ_LIST_URL, headers=headers)
    soup = bs(response.text, "html.parser")

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
        course["Slot"] = cells[5].text
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
    with open("available_breadths.txt", "w") as f:
        f.write(tabulate(df, headers="keys", tablefmt="fancy_grid"))

    print("Available electives saved to available_breadths.txt")


def main():
    args = parse_args()
    if args.electives == "breadth":
        save_breadths(args)
    elif args.electives == "depth":
        save_depths(args)
    else:
        print("Invalid electives type. Choose from 'breadth' or 'depth'")


if __name__ == "__main__":
    main()
