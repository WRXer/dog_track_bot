import gspread, os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


def get_google_sheet():
    """Google API"""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.getenv('SPREADSHEET_ID')).sheet1
    return sheet

def save_to_google_sheet(data):
    """Сохранение данных в таблицу"""
    sheet = get_google_sheet()
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data['fio'],
        data['phone'],
        data['address'],
        data['animal_count'],
        data['description'],
        data.get('photo_url', '')
    ]
    sheet.append_row(row)