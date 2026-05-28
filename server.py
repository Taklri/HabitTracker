from flask import Flask, url_for, request, render_template, session, redirect
app = Flask(__name__)
app.secret_key = "HabitUpKey"

from models.user import User
from models.habit import Habit

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
        return redirect(url_for('dashboard'))
    else:
        return render_template("login.html", error="Invalid credentials")
    
@app.route("/add-habit", methods=["POST", "GET"])
def addHabit():
    if request.method == "GET":
        return render_template("addHabitSample.html")
    if "user_id" not in session:
        return render_template("login.html", error="Please log in to add a habit")
    else:
        user_id = session["user_id"]
    
    habitFrequency = request.form.get("habitFrequency")
    weekly_days = request.form.getlist("weeklyDays")
    monthly_day = request.form.get("monthlyDay")
    
    weekly_days = None
    monthly_day = None


    if habitFrequency == "weekly":
        weekly_days = ",".join(request.form.getlist("weeklyDays")) or None
    elif habitFrequency == "monthly":
        monthly_day = request.form.get("monthlyDay") or None

    habit_data = {
        "userId": user_id,
        "habitName": request.form.get("habitName"),
        "habitCategory": request.form.get("habitCategory"),
        "habitDescription": request.form.get("habitDescription"),
        "habitFrequency": habitFrequency,
        "habitWeekly": weekly_days,
        "habitMonthly": monthly_day,
    }

    Habit.insertHabit(habit_data)
    return render_template("dashboardSample.html")

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

# here yung added para makita sa dashboard and delete
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    habits = Habit.getHabitsByUser(user_id)
    return render_template("dashboardSample.html", username=session["username"], habits=habits)

@app.route("/delete-habit/<int:habit_id>", methods=["POST"])
def deleteHabit(habit_id):
    if "user_id" not in session:
        return redirect("/login")
    
    Habit.deleteHabit(habit_id)
    return redirect("/dashboard")

@app.route("/edit-habit/<int:habit_id>", methods=["GET", "POST"])
def editHabit(habit_id):
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "GET":
        habit = Habit.getHabitById(habit_id)
        if not habit:
            return redirect("/dashboard")
        return render_template("editPageSample.html", habit=habit)

    habitFrequency = request.form.get("habitFrequency")
    weekly_days = None
    monthly_day = None

    if habitFrequency == "weekly":
        weekly_days = ",".join(request.form.getlist("weeklyDays")) or None
    elif habitFrequency == "monthly":
        monthly_day = request.form.get("monthlyDay") or None

    habit_data = {
        "id": habit_id,
        "userId": session["user_id"],
        "habitName": request.form.get("habitName"),
        "habitCategory": request.form.get("habitCategory"),
        "habitDescription": request.form.get("habitDescription"),
        "habitFrequency": habitFrequency,
        "habitWeekly": weekly_days,
        "habitMonthly": monthly_day,
    }

    Habit.updateHabit(habit_data)
    return redirect("/dashboard")

if __name__ == "__main__":
    app.run(debug=True)