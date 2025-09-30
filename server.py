from flask import Flask, render_template, request, redirect, url_for
from contextlib import contextmanager
import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor

pool = None

def setup_db_pool():
    global pool
    DATABASE_URL = os.environ['DATABASE_URL']
    print(f"Creating DB connection pool for {DATABASE_URL}")
    pool = ThreadedConnectionPool(1, 20, dsn=DATABASE_URL, sslmode='require')

@contextmanager
def get_db_connection():
    connection = pool.getconn()
    try:
        yield connection
    finally:
        pool.putconn(connection)

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            yield cur
            if commit:
                conn.commit()
        finally:
            cur.close()
app = Flask(__name__)

setup_db_pool()

@app.route('/', methods=["GET", "POST"])
def guest_list():
    if request.method == "POST":
        name = request.form.get("name")
        message = request.form.get("message")
        if name and message:
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO guest_list (name, message) VALUES (%s, %s);",
                    (name, message)
                )
        return redirect(url_for("guest_list"))

    with get_db_cursor() as cur:
        cur.execute("SELECT name, message FROM guest_list ORDER BY id DESC;")
        guests = cur.fetchall()

    return render_template("hello.html", guest_list=guests)


