from flask import Flask, render_template, request, redirect, make_response, session
import sqlite3

app = Flask(__name__)

app.secret_key = "fakecompany-secret"

employees = [
    {"id": 1, "name": "Diana Petrova", "role": "Security Analyst", "email": "diana@fakecompany.local"},
    {"id": 2, "name": "Alex Ivanov", "role": "System Administrator", "email": "alex@fakecompany.local"},
    {"id": 3, "name": "Maria Sokolova", "role": "HR Manager", "email": "maria@fakecompany.local"}
]

messages = []

users = {
    "guest":{
        "password":"guest123",
        "role":"guest"
    },

    "admin":{
        "password":"admin123",
        "role":"admin"
    }
}
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    return render_template("index.html")


@app.route("/login", methods=["GET","POST"])
def login():

    error=None

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        if username in users:

            if users[username]["password"]==password:

                session["user"]=username
                session["role"]=users[username]["role"]

                return redirect("/")

        error="Invalid credentials"

    return render_template("login.html",error=error)


@app.route("/employees")
def employee_list():

    if "user" not in session:
        return redirect("/login")

    return render_template("employees.html", employees=employees)


@app.route("/profile/<int:id>")
def profile(id):

    employee = None

    for e in employees:
        if e["id"] == id:
            employee = e

    return render_template(
        "profile.html",
        employee=employee
    )

@app.route("/admin")
def admin():

    if "role" not in session:
        return "Login required"

    if session["role"]!="admin":
        return "Access denied"

    return render_template("admin.html")

@app.route("/contact", methods=["GET","POST"])
def contact():

    if request.method == "POST":

        message = request.form["message"]
        messages.append(message)

    return render_template(
        "contact.html",
        messages=messages
    )


def get_db():
    conn = sqlite3.connect("fakecompany.db")
    return conn

@app.route("/search")
def search():

    if "role" not in session or session["role"] != "admin":
        return "Access denied"

    username = request.args.get("username")

    conn = sqlite3.connect("fakecompany.db")
    cursor = conn.cursor()

    query = f"SELECT * FROM users WHERE username = '{username}'"

    cursor.execute(query)
    result = cursor.fetchall()

    return {"result": result}
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)