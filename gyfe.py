# scrape depth electives
import uuid
import requests
import iitkgp_erp_login.erp as erp
import iitkgp_erp_login.utils as erp_utils
from bs4 import BeautifulSoup as bs
import pandas as pd
import argparse
from tabulate import tabulate
import re
import json
from typing import Literal

DEPT: str = None

try:
    import erpcreds  # type: ignore

    DEPT = erpcreds.ROLL_NUMBER[2:4]
    manual = False
except Exception:
    manual = True


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
    # Get code of core courses
    try:
        core_courses = response.json()
    except Exception:
        core_courses = {}

    return [
        course["subno"]
        for course in core_courses
        if course["subtype"] == "Depth CORE"
    ]


def find_all_unavailable_slots(unavailable_slots: list[str]) -> list[str]:
    all_unavailable_slots: list = []

    # overlappings between lab and theory slots
    with open("overlaps.json", "r") as f:
        overlaps = json.load(f)

    # some have more than 1 slot, they are separated
    for slot in unavailable_slots:
        if "," in slot:
            unavailable_slots.extend(s.strip() for s in slot.split(","))
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
                all_unavailable_slots.extend(
                    (slot[0] + "2", slot[0] + "3", slot[0] + "4")
                )
            except Exception:
                pass

            # check if there are any lab slots overlapping with it
            all_unavailable_slots.extend(
                parent for parent, slots in overlaps.items() if slot in slots
            )
    return list(set(all_unavailable_slots))


def save_depths(
    response: tuple,
    save_file: bool = True,
    file_type: Literal["txt", "csv", "xlsx"] = "txt",
):
    """
    Workflow:
            - Check DeptWise timetable and scrape subjects
            - Make sure those subjects are not overlapping with core courses
                    - Subtask: find core courses
            - Go to Deptwise subject list to additionally scrape prof name and slot

    Parameters:
        response (tuple): Tuple containing three elements of requests.Response objects.
        save_file (bool): Flag to create a file or return the data. Default is True.
        file_type (Literal["txt", "csv", "xlsx"]): Flag to set the file type. Default is txt
    Returns:
        None or str: If save_file is False, returns the string of available depth electives.
        For xlsx, reutrns the file name.
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
            except Exception:
                matches = []
            if len(matches) > 1:
                course_code = matches[0]
                depth_course_codes.append(course_code)

    data = {"Course Code": depth_course_codes}
    df_depths = pd.DataFrame(data=data)
    df_depths = df_depths.drop_duplicates(subset=["Course Code"])

    # * Get code of core courses
    core_course_codes = find_core_courses(response[2])

    # * Remove core courses from depths
    df_depths = df_depths[~df_depths["Course Code"].isin(core_course_codes)]

    # * Now get prof names and slots
    soup = bs(response[1].text, "html.parser")

    # * Extract course information from the table rows
    courses = []
    parentTable = soup.find("table", {"id": "disptab"})
    rows = parentTable.find_all("tr")

    try:
        cc = course_code.strip()
    except Exception:
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
            "Minor": "-",
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
    if file_type == "xlsx":
        filename = uuid.uuid4().hex
        writer = pd.ExcelWriter(f"{filename}.xlsx", engine="xlsxwriter")
        df_all.to_excel(writer, sheet_name="Sheet1")
        writer.close()
        return filename

    elif save_file and file_type == "txt":
        with open("available_depths.txt", "w") as f:
            f.write(tabulate(df_all, headers="keys", tablefmt="fancy_grid"))
        print("Available electives saved to available_depths.txt")
        return

    else:
        if save_file:
            df_all.to_csv(f"available_depths.csv", index=False)
            return
        return df_all.to_csv(index=False)


def save_breadths(
    response: tuple,
    save_file: bool = True,
    file_type: Literal["txt", "csv", "xlsx"] = "txt",
):
    """
    Workflow:
            - Check breadth list to get all breadth electives
            - Similar to save_depths, find unavailable slots and filter breadth electives

    Parameters:
        response (tuple): Tuple containing three elements of requests.Response objects.
        save_file (bool): Flag to create a file or return the data. Default is True.
        file_type (Literal["txt", "csv", "xlsx"]): Flag to set the file type. Default is txt
    Returns:
        None or str: If save_file is False, returns the string of available breadth electives.
        For xlsx, reutrns the file name.
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

            if prereq_str := "".join(
                cells[i].text.strip() + ", "
                for i in range(3, 6)
                if cells[i].text.strip() != ""
            ):
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
        except Exception:
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

    if file_type == "xlsx":
        file_name = uuid.uuid4().hex
        writer = pd.ExcelWriter(f"{file_name}.xlsx", engine="xlsxwriter")
        df.to_excel(writer, sheet_name="Sheet1")
        writer.close()
        return file_name

    elif save_file and file_type == "txt":
        with open("available_breadths.txt", "w") as f:
            f.write(tabulate(df, headers="keys", tablefmt="fancy_grid"))
        print("Available electives saved to available_breadths.txt")
        return
    else:
        return df.to_csv(index=False)


def fetch_response(
    acad_session: str, semester: str, year: int, elective: str, DEPT: str, ssoToken: str
) -> tuple[requests.Response, ...]:
    headers = {
        "timeout": "20",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
    }

    session = requests.Session()
    erp_utils.set_cookie(session, "ssoToken", ssoToken)

    TIMETABLE_URL: str = (
        f"https://erp.iitkgp.ac.in/Acad/view/dept_final_timetable.jsp?action=second&course={DEPT}&session={acad_session}&index={year}&semester={semester}&dept={DEPT}"
    )
    ERP_ELECTIVES_URL: str = "https://erp.iitkgp.ac.in/Acad/central_breadth_tt.jsp"

    if elective == "depth":
        SUBJ_LIST_URL: str = (
            f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&for_session={acad_session}&for_semester={semester}&dept={DEPT}"
        )
        TIMETABLE_RESP: requests.Response = session.get(TIMETABLE_URL, headers=headers)
        ERP_ELECTIVES_RESP: requests.Response = None
    elif elective == "breadth":
        SUBJ_LIST_URL: str = (
            f"https://erp.iitkgp.ac.in/Acad/timetable_track.jsp?action=second&dept={DEPT}"
        )
        ERP_ELECTIVES_RESP: requests.Response = session.get(
            ERP_ELECTIVES_URL, headers=headers
        )
        TIMETABLE_RESP: requests.Response = None

    sem: int = 2 * year - 1 if semester == "AUTUMN" else 2 * year
    COURSES_URL: str = (
        f"https://erp.iitkgp.ac.in/Academic/student_performance_details_ug.htm?semno={sem}"
    )

    SUBJ_LIST_RESP: requests.Response = session.get(SUBJ_LIST_URL, headers=headers)
    COURSES_RESP: requests.Response = session.post(COURSES_URL, headers=headers)

    if elective == "depth":
        return (TIMETABLE_RESP, SUBJ_LIST_RESP, COURSES_RESP)
    elif elective == "breadth":
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
            headers, session, LOGGING=True, SESSION_STORAGE_FILE=".session"
        )
        DEPT = (
            erp.ROLL_NUMBER[2:4]
            if erp.ROLL_NUMBER
            else input("Enter your department code: ")
        )
    elif args.notp:
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

    acad_session = args.session
    semester = args.semester
    year = args.year - 1
    elective = args.electives

    if args.electives == "breadth":
        responses = fetch_response(
            acad_session, semester, year, elective, DEPT, ssoToken
        )
        save_breadths(responses)
        depth = input("Do you want to get depth also? (y/N) [Default: no]: ").lower()
        if depth == "y":
            elective = "depth"
            responses = fetch_response(
                acad_session, semester, year, elective, DEPT, ssoToken
            )
            save_depths(responses)

    elif args.electives == "depth":
        responses = fetch_response(
            acad_session, semester, year, elective, DEPT, ssoToken
        )
        save_depths(responses)
        breadth = input(
            "Do you want to get breadth also? (y/N) [Default: no]: "
        ).lower()
        if breadth == "y":
            elective = "breadth"
            responses = fetch_response(
                acad_session, semester, year, elective, DEPT, ssoToken
            )
            save_breadths(responses)

    else:
        print("Invalid electives type. Choose from 'breadth' or 'depth'")


if __name__ == "__main__":
    main()
