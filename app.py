from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ==========================
# DATABASE SETUP
# ==========================
conn = sqlite3.connect('gym.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    plan TEXT,
    join_date TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    amount INTEGER,
    due_date TEXT,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY(member_id) REFERENCES members(id)
)
''')

conn.commit()
conn.close()

# ==========================
# PUBLIC PAGES
# ==========================
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

# ==========================
# MEMBERS
# ==========================
@app.route('/members')
def members():
    conn = sqlite3.connect('gym.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members")
    data = cursor.fetchall()
    conn.close()
    return render_template("members.html", members=data)

@app.route('/add_member', methods=['GET','POST'])
def add_member():
    if request.method=='POST':
        name = request.form['name']
        phone = request.form['phone']
        plan = request.form['plan']
        join_date = request.form['join_date']

        conn = sqlite3.connect('gym.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO members (name, phone, plan, join_date) VALUES (?,?,?,?)",
                       (name, phone, plan, join_date))
        conn.commit()
        conn.close()
        return redirect('/members')
    return render_template("add_member.html")


@app.route('/delete_member/<int:member_id>')
def delete_member(member_id):
    conn = sqlite3.connect('gym.db')
    cursor = conn.cursor()

    # Optional: delete related fees
    cursor.execute("DELETE FROM fees WHERE member_id=?", (member_id,))
    cursor.execute("DELETE FROM members WHERE id=?", (member_id,))

    conn.commit()
    conn.close()
    return redirect('/members')

# ==========================
# FEES
# ==========================
@app.route('/add_fee', methods=['GET','POST'])
def add_fee():
    conn = sqlite3.connect('gym.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM members")
    members_list = cursor.fetchall()
    conn.close()

    if request.method=='POST':
        member_id = request.form['member_id']
        amount = request.form['amount']
        due_date = request.form['due_date']

        conn = sqlite3.connect('gym.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO fees (member_id, amount, due_date) VALUES (?,?,?)",
                       (member_id, amount, due_date))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    return render_template("add_fee.html", members=members_list)

# ==========================
# ADMIN DASHBOARD
# ==========================
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('gym.db')
    cursor = conn.cursor()

    # Total members
    try:
        cursor.execute("SELECT COUNT(*) FROM members")
        total_members = cursor.fetchone()[0]
    except:
        total_members = 0

    # New members this month
    try:
        cursor.execute("SELECT COUNT(*) FROM members WHERE strftime('%m', join_date) = strftime('%m','now')")
        new_members = cursor.fetchone()[0]
    except:
        new_members = 0

    # Plan distribution
    try:
        cursor.execute("SELECT plan, COUNT(*) FROM members GROUP BY plan")
        plans = cursor.fetchall()
    except:
        plans = []

    # Pending fees
    try:
        cursor.execute("""
            SELECT fees.id, members.name, fees.amount, fees.due_date
            FROM fees
            JOIN members ON fees.member_id = members.id
            WHERE fees.status='Pending'
        """)
        pending_fees = cursor.fetchall()
    except:
        pending_fees = []

    conn.close()
    # ✅ Pass datetime to template to fix Jinja error
    return render_template("admin_dashboard.html",
                           total_members=total_members,
                           new_members=new_members,
                           plans=plans,
                           pending_fees=pending_fees,
                           datetime=datetime)  # <- added

# ==========================
# MARK FEE AS PAID
# ==========================
@app.route('/mark_paid/<int:fee_id>')
def mark_paid(fee_id):
    conn = sqlite3.connect('gym.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE fees SET status='Paid' WHERE id=?", (fee_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ==========================
# RUN APP
# ==========================
if __name__=="__main__":
    app.run(debug=True)