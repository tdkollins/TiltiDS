import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
import pandas
import pygsheets
from datetime import datetime

api_url = "https://tiltify.com/api/v3/"
with open("setup.json", "r") as setup_file:
    setup = json.loads(setup_file.read())

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

camp_list = setup["campaignList"]
token = setup["token"]
sheet_name = setup["sheetName"]
wks_index = setup["wksIndex"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

def don_vs_time(start, data, df_len):
    donation_total = []
    time = start
    donation_dataframe = pandas.DataFrame(data)
    donation_dataframe = donation_dataframe.iloc[::-1]
    # print(donation_dataframe)
    donation_total = []
    cutoff = start
    donation_index = 0
    total = 0
    donation_dataframe_len = len(donation_dataframe)
    don_time = donation_dataframe["completedAt"].iloc[0] // 1000

    for dataframe_index in range(df_len):
        if (donation_index == donation_dataframe_len):
            donation_total.append(total)
            continue
        while (don_time < cutoff):
            total += donation_dataframe["amount"].iloc[donation_index]
            donation_index += 1
            if (donation_index == donation_dataframe_len):
                break
            don_time = donation_dataframe["completedAt"].iloc[donation_index] // 1000
        cutoff += 1800
        donation_total.append(total)

    return donation_total


def get_hours(duration):
    hour_col = []
    for hour in range(duration):
        hour_col.append("{:02}:00:00".format(hour))
        hour_col.append("{:02}:30:00".format(hour))
    hour_col.append("{:02}:00:00".format(duration))
    return hour_col


def tiltify_request(url, params=None):
    response = requests.get(url = url,
                            headers = {"Authorization": "Bearer {}".format(token)},
                            params = params)
    return response

def main():
    max_duration = 0
    gc = pygsheets.authorize(service_file='creds.json')
    sh = gc.open(sheet_name)
    wks = sh[wks_index]
    cur_col = 2

    for camp in camp_list:
        camp_id = camp["id"]
        camp_url = api_url + "campaigns/" + camp_id
        camp_data = json.loads(tiltify_request(camp_url).text)["data"]
        camp_name = camp_data["name"]
        start_timestamp = camp["startTimestamp"] # epoch timestamp
        end_timestamp = camp["endTimestamp"]
        start_datetime = datetime.fromtimestamp(start_timestamp)
        end_datetime = datetime.fromtimestamp(end_timestamp)
        duration = int((end_datetime - start_datetime).total_seconds() // 3600)
        print("Campaign: {}".format(camp_name))
        print("Started: {}".format(start_datetime))
        print("Ended: {}".format(end_datetime))
        print("Duration in Hours: {}".format(duration))

        dataframe = pandas.DataFrame()
        dataframe["Marathon Time"] = get_hours(duration)

        donation_url = api_url + "campaigns/" + camp_id + "/donations/"
        donation_data = json.loads(tiltify_request(donation_url, {"count": 1000000}).text)["data"]
        dataframe["Donation Total"] = don_vs_time(start_timestamp, donation_data, len(dataframe))
        print(dataframe)

        time_df = pandas.DataFrame()
        time_df["Marathon Time"] = dataframe["Marathon Time"]
        donation_df = pandas.DataFrame()
        donation_df[camp_name] = dataframe["Donation Total"]

        if duration > max_duration:
            duration = max_duration
            wks.set_dataframe(time_df,(1, 1))
        wks.set_dataframe(donation_df, (1, cur_col))
        cur_col += 1


main()
