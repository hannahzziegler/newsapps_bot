# this is a working scraper that only pulls down the state employee vacancies,
# rather than all of the data. so we have *something* to work with!!!!
# the main thing I wanted to figure out here was making it so I don't have to
# hard-code the number of x15 multiples

import csv
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from slack import WebClient
from slack.errors import SlackApiError
import datetime
from datetime import date, timedelta
import filecmp


def check_vacancies():
    try:
        with open('last_checked.txt', 'r') as f:
            last_checked_date = f.read().strip()
    except FileNotFoundError:
        with open('last_checked.txt', 'w') as f:
            last_checked_date = '2023-03-30'  # default date if file doesn't exist
            f.write(last_checked_date)

    page = 0
    table_data = []
    while page <= 330:
        url = f"https://www.doit.state.md.us/phonebook/IndListing.asp?FirstLetter=vacant&Submit=Search&offset={page}"
        response = requests.get(url)
        html = response.content
        soup = BeautifulSoup(html, features="html.parser")
        table = soup.find('table')
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 4:
                employee_name = cells[0].get_text().strip()
                agency_name = cells[1].get_text().strip()
                office = cells[2].get_text().strip()
                phone = cells[3].get_text().strip()
                table_data.append([employee_name, agency_name, office, phone])
        page = page + 15

    # print(table_data)

    df = pd.DataFrame(table_data, columns=[
        'employee_name', 'agency_name', 'office', 'phone_number'])
    print("this should be today's data")
    print(df)
    total_vacancies = len(df. index)

    csv_file = open("md_employees" + (time.strftime('%Y_%m_%d')) + ".csv", "w")
    writer = csv.writer(csv_file)
    writer.writerow(["employee_name", "agency_name", "office", "phone"])
    writer.writerows(table_data)

    # write a file that writes over itself each time the scraper runs so that
    # we can see what has changed in GitHub.
    with open(f"md_employees_total.csv", "w") as output_file:
        csvfile = csv.writer(output_file)
        csvfile.writerow(["employee_name", "agency_name", "office", "phone"])
        csvfile.writerows(table_data)

    today = date.today()
    yesterday = today - timedelta(days=1)

    print("this should be yesterday's data")
    yesterday_csv = pd.read_csv(
        "md_employees" + (yesterday.strftime('%Y_%m_%d')) + ".csv")
    print(yesterday_csv)

    total_vacancies = len(df. index)
    yesterday_vacancies = len(yesterday_csv. index)

    slack_token = os.environ.get('SLACK_API_TOKEN')
    client = WebClient(token=slack_token)

    msg = f"Hello from VacancyBot! There are currently {total_vacancies} state employee vacancies.\n"
    if total_vacancies < yesterday_vacancies:
        print("Vacancies have decreased.")
        msg += f"Vacancies have increased since {yesterday}, when there were {yesterday_vacancies}.\n"
        msg += f"Find an updated file of state employees vacancies here: https://github.com/hannahzziegler/newsapps_bot/blob/main/md_employees{today.strftime('%Y_%m_%d')}.csv \nSee any changes in vacancies in this master file: https://github.com/hannahzziegler/newsapps_bot/commits/30dc35f7f5a3eb6534f454a04377553815459a68/md_employees_total.csv \nCheck out the Maryland state employees database: https://www.doit.state.md.us/phonebook/indlisting.asp"
    elif total_vacancies > yesterday_vacancies:
        print(f"Vacancies have increased.")
        msg += f"Vacancies have increased since {yesterday}, when there were {yesterday_vacancies}.\n"
        msg += f"Find an updated file of state employees vacancies here: https://github.com/hannahzziegler/newsapps_bot/blob/main/md_employees{today.strftime('%Y_%m_%d')}.csv \nSee any changes in vacancies in this master file: https://github.com/hannahzziegler/newsapps_bot/commits/30dc35f7f5a3eb6534f454a04377553815459a68/md_employees_total.csv \nCheck out the Maryland state employees database: https://www.doit.state.md.us/phonebook/indlisting.asp"
    elif total_vacancies == yesterday_vacancies:
        print("The number of vacancies has not changed.")
        msg += f"The number of vacancies has not changed since yesterday's update.\nFind the most recent file of state employees vacancies here: https://github.com/hannahzziegler/newsapps_bot/blob/main/md_employees{today.strftime('%Y_%m_%d')}.csv"
    print(msg)
    try:
        response = client.chat_postMessage(
            channel="slack-bots",
            text=msg,
            unfurl_links=True,
            unfurl_media=True
        )
        print("success!")
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]
        print(f"Got an error: {e.response['error']}")


check_vacancies()

# tomorrow -- try to make a base file that updates as changes occur so that
# it's easier to figure out
