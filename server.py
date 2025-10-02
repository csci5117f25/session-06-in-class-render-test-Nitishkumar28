from flask import Flask, render_template, request, redirect, url_for, session
from contextlib import contextmanager
import os
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv

pool = None

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
    
    
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
app.secret_key = env.get("APP_SECRET_KEY")

setup_db_pool()

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect(url_for("hello"))


# 👆 We're continuing from the steps above. Append this to your server.py file.

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("hello", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

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

@app.route('/simple', methods=["GET"])
def simple():
    return render_template("simple.html")


