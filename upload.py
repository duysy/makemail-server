import os
import requests
import json
import pymysql
from pymysql import Error

import json

key_value_store = {}
def set_key_value(key, value):
    key_value_store[key] = value
    save_to_json()
def get_value(key):
    key_value_store = load_from_json()
    return key_value_store.get(key, None)

def save_to_json():
    with open('key_value_store.json', 'w') as json_file:
        json.dump(key_value_store, json_file)
def load_from_json():
    try:
        with open('key_value_store.json', 'r') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return {}

def uploadDB(line):
    host = '64.176.223.xx'
    port = 33333 
    database = 'mailxx'
    user = 'root'
    password = 'xxxx'

    try:
        connection = pymysql.connect(host=host, port=port, database=database, user=user, password=password)
        with connection.cursor() as cursor:
            sql = "INSERT INTO `mail` (`message_content`) VALUES (%s)"
            cursor.execute(sql, (line,))
            connection.commit()

    except Error as e:
        pass

    finally:
        try:
            if connection and connection.open:
                connection.close()
        except:
            pass

headers = {'Content-Type': 'application/json', 'X-API-KEY': 'makemai1111111111111111hack'}
BASE_DOMAIN = "http://64.176.223.99:5000"
def ensure_file(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.isfile(file_path):
        with open(file_path, 'w'): pass

def tableToPath(database):
    database_to_path = {
        "inputyahoo": "data/inputYahoo.txt",
        "outputyahoosuccess": "data/outputYahooSuccess.txt",
        "outputyahoofail": "data/outputYahooFail.txt",
        "output": "data/output.txt",
        "hotmail": "data/hotmail.txt",
        "keyapi": "data/key_api_gologin.txt"
    }
    return database_to_path.get(database, "")

def update_file(file_path, lines):
    with open(file_path, 'w') as file_:
        file_.write("\n".join(lines))

database_options = {
    1: "inputyahoo",
    2: "outputyahoosuccess",
    3: "outputyahoofail",
    4: "output",
    5: "hotmail",
    6: "keyapi"
}
mode = int(input(f"HAY CHON CHINH XAC ** Chon mode 1 local to server, 2 server to local, 3 auto: "))
if mode == 1:
    optionWriteFile = int(input(f"{mode} - HAY CHON CHINH XAC ** Chon option {database_options}: "))
    database = database_options.get(optionWriteFile)

    if not database:
        print("Vui long chon lua chinh xac.")
    else:
        file_path = tableToPath(database)
        ensure_file(file_path)

        with open(file_path, "r") as file_:
            emails = file_.read().strip().split("\n")

        url = f"{BASE_DOMAIN}/add/{database}"
        while emails:
            email_chunks = emails[:5]
            data = []
            for result in email_chunks:
                data.append({"data":result})
            payload = json.dumps(data)
            response = requests.request("POST", url, headers=headers, json=data)
            print(response.text)
            emails = emails[5:]
            update_file(file_path, emails)
elif mode == 2:
    optionReadFile = int(input(f"{mode} -HAY CHON CHINH XAC ** Chon option {database_options}: "))
    database = database_options.get(optionReadFile)
    if not database:
        print("Vui long chon lua chinh xac.")
    else:
        lastStatus = 200
        while lastStatus== 200:
            url = f"{BASE_DOMAIN}/pop/{database}"
            payload = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            lastStatus = response.status_code
            if lastStatus == 200:
                print(response.json())
                line = response.json().get("data")
                file_path = tableToPath(database)
                with open(file_path, "a+") as file_:
                    file_.write(f"{line}\n")
            else:
                print("co loi hay check lai")
elif mode == 3:
    ensure_file("data/manual_solve.txt")
    database = database_options.get(4)
    lastStatus = 200
    while lastStatus== 200:
        url = f"{BASE_DOMAIN}/pop/{database}"
        payload = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        lastStatus = response.status_code
        if lastStatus == 200:
            line = response.json().get("data")
            lineArr = str(line).split("|")
            if lineArr[0] != "None" and  lineArr[1] != "None" and  lineArr[2] != "None" and  lineArr[3] != "None" and  lineArr[4] != "None" and  lineArr[5] != "None" and  lineArr[6] != "None":
                file_path = tableToPath(database)
                print(f"====>{database}",line)
                uploadDB(line)
                with open(file_path, "a+") as file_:
                    file_.write(f"{line}\n")
            else:
                yahooMail = lineArr[0]
                countRetry = get_value(yahooMail)
                if countRetry == None:
                    set_key_value(yahooMail, 1)
                else:
                    set_key_value(yahooMail, countRetry + 1)
                countRetry = get_value(yahooMail)
                if countRetry < 5:
                    for _ in range(3):
                        try:
                            database_outputyahoosuccess = database_options.get(2)
                            url = f"{BASE_DOMAIN}/add/{database_outputyahoosuccess}"
                            payload = json.dumps([{"data":line}])
                            response = requests.request("POST", url, headers=headers, data=payload)
                            print(f"====>UPLOAD_{database_outputyahoosuccess}",line)
                            break
                        except:
                            print(f"====> RETRY_UPLOAD_{database_outputyahoosuccess}",line)
                else:
                    with open("data/manual_solve.txt", "a+") as file_:
                        file_.write(f"{line}\n")
        else:
            print("co loi hay check lai")
else:
    print("Vui long chon lua chinh xac.")


input("Xong roi nhe")