import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import pytz

st.set_page_config(page_title="ContestRadar", layout="wide")

TIMEZONE = pytz.timezone("Asia/Kolkata")

def format_time(utc_time_str, fmt="%b/%d/%Y %H:%M"):
    try:
        dt = datetime.strptime(utc_time_str, fmt)
        dt = pytz.utc.localize(dt).astimezone(TIMEZONE)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return utc_time_str

def get_codeforces():
    try:
        url = "https://codeforces.com/api/contest.list"
        r = requests.get(url)
        data = r.json()

        upcoming = [c for c in data["result"] if c["phase"] == "BEFORE"]
        if not upcoming:
            return []

        contest = upcoming[0]
        start = datetime.utcfromtimestamp(contest["startTimeSeconds"]).replace(tzinfo=pytz.utc).astimezone(TIMEZONE)

        return [{
            "Platform": "Codeforces",
            "Contest Name": contest["name"],
            "Start Time": start.strftime("%Y-%m-%d %H:%M"),
            "Duration": f"{contest['durationSeconds']//3600}h {(contest['durationSeconds']%3600)//60}m",
            "Link": f"https://codeforces.com/contest/{contest['id']}"
        }]
    except Exception as e:
        st.error(f"❌ Codeforces error: {e}")
        return []


def get_atcoder():
    try:
        url = "https://atcoder.jp/contests/"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        contests = []
        table = soup.find("div", id="contest-table-upcoming")
        if not table:
            st.warning("⚠️ AtCoder structure changed.")
            return []
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                name_tag = cols[1].find("a")
                name = name_tag.text.strip()
                link = "https://atcoder.jp" + name_tag["href"]
                time = cols[0].text.strip()
                duration = cols[2].text.strip()
                contests.append({
                    "Platform": "AtCoder",
                    "Contest Name": name,
                    "Start Time": time,
                    "Duration": duration,
                    "Link": link
                })
        return contests[:1] if contests else []
    except Exception as e:
        st.error(f"❌ AtCoder error: {e}")
        return []

def get_codechef():
    try:
        url = "https://www.codechef.com/api/list/contests/all"
        r = requests.get(url)
        data = r.json()

        upcoming = data.get("future_contests", [])
        if not upcoming:
            return []

        contest = upcoming[0]
        return [{
            "Platform": "CodeChef",
            "Contest Name": contest["contest_name"],
            "Start Time": contest["contest_start_date"],
            "Duration": f"Until {contest['contest_end_date']}",
            "Link": f"https://www.codechef.com/{contest['contest_code']}"
        }]
    except Exception as e:
        st.error(f"❌ CodeChef error: {e}")
        return []


def get_gfg():
    try:
        url = "https://practiceapi.geeksforgeeks.org/api/v1/events/?page=1"
        r = requests.get(url)
        data = r.json()

        events = data.get("results", [])
        if not events:
            return []

        event = events[0]
        return [{
            "Platform": "GeeksforGeeks",
            "Contest Name": event["title"],
            "Start Time": event["start_date"].replace("T", " ").split("+")[0],
            "Duration": "-",
            "Link": event["url"]
        }]
    except Exception as e:
        st.error(f"❌ GFG error: {e}")
        return []


def get_leetcode():
    try:
        url = "https://leetcode.com/graphql"
        headers = {"Content-Type": "application/json"}
        payload = {
            "query": """
                query {
                  upcomingContests {
                    title
                    titleSlug
                    startTime
                    duration
                  }
                }
            """
        }

        r = requests.post(url, headers=headers, json=payload)
        data = r.json()["data"]["upcomingContests"]
        if not data:
            return []

        contest = data[0]
        start = datetime.fromtimestamp(contest["startTime"], pytz.utc).astimezone(TIMEZONE)
        return [{
            "Platform": "LeetCode",
            "Contest Name": contest["title"],
            "Start Time": start.strftime("%Y-%m-%d %H:%M"),
            "Duration": f"{contest['duration']//3600}h {(contest['duration']%3600)//60}m",
            "Link": f"https://leetcode.com/contest/{contest['titleSlug']}/"
        }]
    except Exception as e:
        st.error(f"❌ LeetCode error: {e}")
        return []


def get_all_contests():
    contests = []
    contests.extend(get_codeforces())
    contests.extend(get_atcoder())
    contests.extend(get_leetcode())
    contests.extend(get_codechef())
    contests.extend(get_gfg())
    return contests

# ------------------------ STREAMLIT APP ------------------------

st.title("🚀 ContestRadar – Next Coding Contest on Each Platform")
st.info("🕒 All times shown in **IST (Asia/Kolkata)**")

with st.spinner("Fetching upcoming contests..."):
    all_data = get_all_contests()

if not all_data:
    st.error("No upcoming contests found. Please try again later.")
else:
    for contest in all_data:
        with st.container():
            st.markdown(f"### [{contest['Contest Name']}]({contest['Link']})")
            st.markdown(f"**Platform**: {contest['Platform']}  \n"
                        f"**Start Time**: {contest['Start Time']}  \n"
                        f"**Duration**: {contest['Duration']}")
            st.markdown("---")

    st.caption("Last Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
