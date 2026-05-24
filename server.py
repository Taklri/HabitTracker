from flask import Flask, request, render_template, session
app = Flask(__name__)
app.secret_key = "HabitUpKey"

from models.user import User

@app.route('/')
def index():
    return render_template("login.html")

@app.route("/login")
def loginPage():
    return render_template("login.html")

@app.route("/login/process", methods=["POST"])
def loginProcess():
    user_data = {
        "username": request.form["username"],
        "password": request.form["password"]
    }
    user = User.loginUser(user_data)
    if user:
        session["user_id"] = user.id
        session["username"] = user.username
        return render_template("dashboard.html")
    else:
        return render_template("login.html", error="Invalid credentials")

@app.route("/signup")
def signupPage():
    return render_template("signup.html")

@app.route("/signup/process", methods=["POST"])
def signupProcess():
    newUser={
        "username": request.form["username"],
        "password": request.form["password"],
        "reenterpass": request.form["reenterpass"]
    }
    if newUser["password"] != newUser["reenterpass"]:
        return "Passwords do not match"
    else:
        User.insertUser(newUser)
    return render_template("login.html")
    
if __name__ == "__main__":
    app.run(debug=True)