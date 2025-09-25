from flask import Flask, render_template, request, redirect
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)

@app.route('/', methods=['GET', 'POST'])
def home():
    name = request.args.get('name')

    if request.method == 'POST':
        form_name = request.form.get('name')
        message = request.form.get('message')

        if form_name and message:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO guest_list (name, message) VALUES (%s, %s)",
                    (form_name, message)
                )
                conn.commit()
        return redirect('/')

    with conn.cursor() as cur:
        cur.execute("SELECT name, message FROM guest_list ORDER BY id ASC")
        rows = cur.fetchall()

    guests = [{'name': r[0], 'message': r[1]} for r in rows]

    return render_template('hello.html', guests=guests, name=name)

if __name__ == '__main__':
    app.run(debug=True)
