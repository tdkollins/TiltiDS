import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
import pandas
import pygsheets
from datetime import datetime

api_url = 'https://tiltify.com/api/v3/'
camp_id_list = [""]

scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

token = ""
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)


def tiltify_request(url, params=None):
    response = requests.get(url = url,
                            headers = {'Authorization': 'Bearer {}'.format(token)},
                            params = params)
    return response

def main():
    for camp_id in camp_id_list:
        campaign_url = api_url + 'campaigns/' + camp_id
        campaign_data = json.loads(tiltify_request(campaign_url).text)['data']
        campaign_name = campaign_data['name']
        print("Enter the start time for " + campaign_name + " in epoch timestamp")
        #start_timestamp = int(input())
        start_timestamp = 1501502400
        print("Enter the end time for " + campaign_name + " in epoch timestamp")
        #end_timestamp = int(input())
        end_timestamp = 1501801200
        start_datetime = datetime.fromtimestamp(start_timestamp)
        end_datetime = datetime.fromtimestamp(end_timestamp)
        duration = int((end_datetime - start_datetime).total_seconds() // 3600)
        print("Started: {}".format(start_datetime))
        print("Ended: {}".format(end_datetime))
        print("Duration in Hours: {}".format(duration))

        dataframe = pandas.DataFrame()
        hour_col = []
        for hour in range(duration):
            hour_col.append('{:02}:00:00'.format(hour))
            hour_col.append('{:02}:30:00'.format(hour))
        hour_col.append('{:02}:00:00'.format(duration))
        dataframe['Marathon Time'] = hour_col

        donation_url = api_url + 'campaigns/' + camp_id + '/donations/'
        donation_data = json.loads(tiltify_request(donation_url, {'count': 1000000}).text)['data']
        print(pandas.DataFrame(donation_data))


main()
