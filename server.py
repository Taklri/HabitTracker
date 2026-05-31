from datetime import date

from flask import Flask, url_for, request, render_template, session, redirect, flash
app = Flask(__name__)
app.secret_key = "HabitUpKey"

from models.user import User
from models.habit import Habit
from models.goal import Goal

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


def _parse_csv_values(value):
    if not value:
        return set()
    return {item.strip().lower() for item in str(value).split(",") if item.strip()}


def _habit_is_for_today(habit, today):
    frequency = (getattr(habit, "habitFrequency", "") or "").lower()

    if frequency == "daily":
        return True

    if frequency == "weekly":
        return today.strftime("%A").lower() in _parse_csv_values(getattr(habit, "habitWeekly", None))

    if frequency == "monthly":
        habit_day = getattr(habit, "habitMonthly", None)
        try:
            return int(habit_day) == today.day
        except (TypeError, ValueError):
            return False

    return False


def _habit_created_today(habit, today):
    created_value = getattr(habit, "created_at", None) or getattr(habit, "createdAt", None)
    if not created_value:
        return False

    created_text = str(created_value)
    return created_text[:10] == today.isoformat()


def _goal_is_for_today(goal, today):
    return str(getattr(goal, "targetDate", "") or "")[:10] == today.isoformat()


def _habit_schedule_label(habit):
    frequency = (getattr(habit, "habitFrequency", "") or "").lower()

    if frequency == "daily":
        return "Every day"

    if frequency == "weekly":
        days = [day.strip().title() for day in str(getattr(habit, "habitWeekly", "") or "").split(",") if day.strip()]
        return "Weekly: " + ", ".join(days) if days else "Weekly"

    if frequency == "monthly":
        day = getattr(habit, "habitMonthly", None)
        return f"Monthly: Day {day}" if day else "Monthly"

    return frequency.title() if frequency else "Unspecified"

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    today = date.today()

    habits = Habit.getHabitsByUser(user_id)
    goals = Goal.getGoalsByUser(user_id)

    todays_habits = [
        habit for habit in habits
        if _habit_is_for_today(habit, today) or _habit_created_today(habit, today)
    ]
    todays_goals = [goal for goal in goals if _goal_is_for_today(goal, today)]

    return render_template(
        "dashboardSample.html",
        username=session["username"],
        today=today,
        today_label=today.strftime("%A, %B %d, %Y"),
        habits=todays_habits,
        all_habits=habits,
        goals=todays_goals,
        habit_schedule_label=_habit_schedule_label,
    )

#habits
@app.route("/add-habit")
def addHabit():
    return render_template("addHabitSample.html")

@app.route("/add-habit/process", methods=["POST"])
def addHabitProcess():
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
    return redirect("/dashboard")

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

#goals
@app.route("/add-goal", methods=["GET", "POST"])
def addGoal():
    if request.method == "GET":
        return render_template("addGoal.html")
    
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    goal_data = {
        "userId": user_id,
        "goalName": request.form.get("goalName"),
        "goalDescription": request.form.get("goalDescription"),
        "goalCategory": request.form.get("goalCategory"),
        "goalStatus": "not started",
        "targetDate": request.form.get("targetDate"),
        "progress": 0,
    }
    
    Goal.createGoal(goal_data)
    return redirect("/dashboard")

@app.route("/delete-goal/<int:goal_id>", methods=["POST"])
def deleteGoal(goal_id):
    if "user_id" not in session:
        return redirect("/login")
    
    Goal.deleteGoal(goal_id)
    return redirect("/dashboard")

@app.route("/edit-goal/<int:goal_id>", methods=["GET", "POST"])
def editGoal(goal_id):
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "GET":
        goal = Goal.getGoalById(goal_id)
        return render_template("editGoal.html", goal=goal)
    
    user_id = session["user_id"]
    goal_data = {
        "id": goal_id,
        "userId": user_id,
        "goalName": request.form.get("goalName"),
        "goalDescription": request.form.get("goalDescription"),
        "goalCategory": request.form.get("goalCategory"),
        "goalStatus": request.form.get("goalStatus"),
        "targetDate": request.form.get("targetDate"),
        "progress": int(request.form.get("progress", 0)),
    }
    
    Goal.updateGoal(goal_data)
    return redirect("/dashboard")
if __name__ == "__main__":
    app.run(debug=True)