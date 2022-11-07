import psycopg2
import shutil
import threading
import time
import psutil as psutil
from flask import Flask
from datetime import datetime
from datetime import timedelta

app = Flask(__name__)


# returns the time before 5 minutes of the current time
def get_time():
    current_time = datetime.now()
    future_time = current_time - timedelta(minutes=5)
    return future_time


# function to return the connection to the database
def connect_database():
    conn = psycopg2.connect(host='localhost', port="5432", database='postgres', user="postgres",
                            password="postgres")
    return conn


def get_data(dev):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute(f"select AVG({dev}_usage) from info.{dev} where read_time > CURRENT_TIME - INTERVAL '5 minutes' ")
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return result[0]


@app.route("/")
def home():
    cpu_average = get_data("cpu")
    return {"cpu_average": cpu_average}


@app.route("/cpu")
def cpu():
    cpu_average = get_data("cpu")
    return {"cpu_average": cpu_average}


@app.route("/memory")
def memory():
    memory_average = get_data("memory")
    return {"memory_average": memory_average}


@app.route("/disk")
def disk():
    disk_average = get_data("disk")
    return {"disk_average": disk_average}


# function to store the info of cpu,disk ,memory usages in the database each 10 seconds
def checker_thread():
    while True:
        # calculating the disk usage
        total, used, free = shutil.disk_usage("/")
        perc = (used / total) * 100
        # reading the current date and time
        now = datetime.now()
        conn = connect_database()
        cur = conn.cursor()

        cur.execute("insert into info.cpu (read_time,cpu_usage) values(%s,%s)", (now, psutil.cpu_percent()))
        cur.execute("insert into info.disk (read_time,disk_usage) values(%s,%s)", (now, perc))
        cur.execute("insert into info.memory (read_time,memory_usage) values(%s,%s)",
                    (now, psutil.virtual_memory().percent))
        conn.commit()
        cur.close()
        conn.close()
        # function will sleep for 10 seconds and run again
        time.sleep(10)


if __name__ == '__main__':
    x = threading.Thread(target=checker_thread)
    x.start()
    app.run(debug=True)
