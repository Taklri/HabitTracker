from datetime import date
import os

from flask import Flask, url_for, request, render_template, session, redirect, flash, send_from_directory
app = Flask(__name__)
app.secret_key = "HabitUpKey"

from models.user import User
from models.habit import Habit
from models.goal import Goal

AVATAR_FOLDER = os.path.join(app.root_path, "avatars")


def _allowed_avatars():
    return sorted(User.ALLOWED_AVATARS)


def _sanitize_avatar(value):
    return User.normalizeAvatar(value)


@app.route("/avatars/<avatar_name>.png")
def serveAvatar(avatar_name):
    avatar = _sanitize_avatar(avatar_name)
    return send_from_directory(AVATAR_FOLDER, f"{avatar}.png")

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
        session["avatar"] = _sanitize_avatar(user.avatar)
        return redirect(url_for('dashboard'))
    else:
        return render_template("login.html", error="Invalid credentials")
    
@app.route("/signup")
def signupPage():
    return render_template(
        "signup.html",
        allowed_avatars=_allowed_avatars(),
        default_avatar=User.DEFAULT_AVATAR,
    )

@app.route("/signup/process", methods=["POST"])
def signupProcess():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    reenterpass = request.form.get("reenterpass", "")
    selected_avatar = _sanitize_avatar(request.form.get("avatar"))

    newUser={
        "username": username,
        "password": password,
        "reenterpass": reenterpass,
        "avatar": selected_avatar,
    }
    if not username:
        return render_template(
            "signup.html",
            error="Username cannot be blank",
            allowed_avatars=_allowed_avatars(),
            default_avatar=selected_avatar,
        )

    if User.usernameExists(username):
        return render_template(
            "signup.html",
            error="Username already exists",
            allowed_avatars=_allowed_avatars(),
            default_avatar=selected_avatar,
        )

    if len(password) < User.MIN_PASSWORD_LENGTH:
        return render_template(
            "signup.html",
            error=f"Password must be at least {User.MIN_PASSWORD_LENGTH} characters",
            allowed_avatars=_allowed_avatars(),
            default_avatar=selected_avatar,
        )

    if newUser["password"] != newUser["reenterpass"]:
        return render_template(
            "signup.html",
            error="Passwords do not match",
            allowed_avatars=_allowed_avatars(),
            default_avatar=newUser["avatar"],
        )
    else:
        User.insertUser(newUser)
    return render_template("login.html")


@app.route("/profile")
def profilePage():
    if "user_id" not in session:
        return redirect("/login")

    user = User.getUserById({"id": session["user_id"]})
    if not user:
        return redirect("/login")

    return render_template(
        "profile.html",
        username=user.username,
        selected_avatar=_sanitize_avatar(user.avatar),
        allowed_avatars=_allowed_avatars(),
    )


@app.route("/profile/process", methods=["POST"])
def profileProcess():
    if "user_id" not in session:
        return redirect("/login")

    username = request.form.get("username", "").strip()
    new_password = request.form.get("password", "")
    reenter_password = request.form.get("reenterpass", "")
    avatar = _sanitize_avatar(request.form.get("avatar"))

    if not username:
        user = User.getUserById({"id": session["user_id"]})
        return render_template(
            "profile.html",
            username=session.get("username"),
            selected_avatar=avatar,
            allowed_avatars=_allowed_avatars(),
            error="Username cannot be blank",
        )

    if User.usernameExists(username, exclude_user_id=session["user_id"]):
        return render_template(
            "profile.html",
            username=username,
            selected_avatar=avatar,
            allowed_avatars=_allowed_avatars(),
            error="Username already exists",
        )

    if new_password and len(new_password) < User.MIN_PASSWORD_LENGTH:
        return render_template(
            "profile.html",
            username=username,
            selected_avatar=avatar,
            allowed_avatars=_allowed_avatars(),
            error=f"Password must be at least {User.MIN_PASSWORD_LENGTH} characters",
        )

    if new_password and new_password != reenter_password:
        return render_template(
            "profile.html",
            username=username,
            selected_avatar=avatar,
            allowed_avatars=_allowed_avatars(),
            error="Passwords do not match",
        )

    profile_data = {
        "id": session["user_id"],
        "username": username,
        "avatar": avatar,
        "password": new_password or None,
    }

    User.updateProfile(profile_data)
    session["username"] = username
    session["avatar"] = avatar
    return redirect("/profile")


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


def _habit_sort_key(habit):
    created_value = getattr(habit, "created_at", None) or getattr(habit, "createdAt", None)
    if created_value:
        return str(created_value)
    return str(getattr(habit, "id", 0))


def _goal_sort_key(goal):
    return str(getattr(goal, "targetDate", "") or "")


def _sorted_habits_for_user(user_id):
    habits = Habit.getHabitsByUser(user_id)
    return sorted(habits, key=_habit_sort_key)


def _sorted_goals_for_user(user_id):
    goals = Goal.getGoalsByUser(user_id)
    return sorted(goals, key=_goal_sort_key)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    today = date.today()

    selected_habit_category = request.args.get("habit_category", "").strip() or None
    selected_goal_category = request.args.get("goal_category", "").strip() or None

    if selected_habit_category:
        all_habits = sorted(Habit.filterHabitsByCategory(user_id, selected_habit_category), key=_habit_sort_key)
    else:
        all_habits = _sorted_habits_for_user(user_id)

    if selected_goal_category:
        all_goals = sorted(Goal.filterGoalsByCategory(user_id, selected_goal_category), key=_goal_sort_key)
    else:
        all_goals = _sorted_goals_for_user(user_id)

    todays_habits = [
        habit for habit in all_habits
        if _habit_is_for_today(habit, today) or _habit_created_today(habit, today)
    ]
    todays_goals = [goal for goal in all_goals if _goal_is_for_today(goal, today)]

    return render_template(
        "dashboardSample.html",
        username=session["username"],
        avatar=_sanitize_avatar(session.get("avatar")),
        today=today,
        today_label=today.strftime("%A, %B %d, %Y"),
        habits=todays_habits,
        all_habits=all_habits,
        goals=todays_goals,
        all_goals=all_goals,
        habit_schedule_label=_habit_schedule_label,
        selected_habit_category=selected_habit_category,
        selected_goal_category=selected_goal_category,
    )


@app.route("/all-habits")
def allHabits():
    if "user_id" not in session:
        return redirect("/login")

    habits = _sorted_habits_for_user(session["user_id"])
    return render_template(
        "allHabit.html",
        username=session["username"],
        avatar=_sanitize_avatar(session.get("avatar")),
        habits=habits,
        habit_schedule_label=_habit_schedule_label,
    )


@app.route("/all-goals")
def allGoals():
    if "user_id" not in session:
        return redirect("/login")

    goals = _sorted_goals_for_user(session["user_id"])
    return render_template(
        "allGoals.html",
        username=session["username"],
        avatar=_sanitize_avatar(session.get("avatar")),
        goals=goals,
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

    habit_name = request.form.get("habitName", "").strip()
    if not habit_name:
        return render_template("addHabitSample.html", error="Habit name is required")

    if Habit.habitNameExists(user_id, habit_name):
        return render_template("addHabitSample.html", error="Habit name already exists")

    habit_data = {
        "userId": user_id,
        "habitName": habit_name,
        "habitCategory": request.form.get("habitCategory"),
        "habitDescription": request.form.get("habitDescription"),
        "habitFrequency": habitFrequency,
        "habitWeekly": weekly_days,
        "habitMonthly": monthly_day,
        "habitIcon": request.form.get("habitIcon", "📋"),
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

    habit_name = request.form.get("habitName", "").strip()
    if not habit_name:
        habit = Habit.getHabitById(habit_id)
        return render_template("editPageSample.html", habit=habit, error="Habit name is required")

    if Habit.habitNameExists(session["user_id"], habit_name, exclude_habit_id=habit_id):
        habit = Habit.getHabitById(habit_id)
        return render_template("editPageSample.html", habit=habit, error="Habit name already exists")

    habit_data = {
        "id": habit_id,
        "userId": session["user_id"],
        "habitName": habit_name,
        "habitCategory": request.form.get("habitCategory"),
        "habitDescription": request.form.get("habitDescription"),
        "habitFrequency": habitFrequency,
        "habitWeekly": weekly_days,
        "habitMonthly": monthly_day,
        "habitIcon": request.form.get("habitIcon", "📋"),
    }

    Habit.updateHabit(habit_data)
    return redirect("/dashboard")

#goals
@app.route("/add-goal", methods=["GET", "POST"])
def addGoal():
    if request.method == "GET":
        return render_template("addGoal.html", min_date=date.today().isoformat())
    
    if "user_id" not in session:
        return redirect("/login")
    
    goal_name = request.form.get("goalName", "").strip()
    goal_desc = request.form.get("goalDescription", "").strip()
    goal_cat = request.form.get("goalCategory", "").strip()
    target_date = request.form.get("targetDate", "").strip()

    if not goal_name:
        return render_template("addGoal.html", error="Goal name is required", min_date=date.today().isoformat())

    if Goal.goalNameExists(session["user_id"], goal_name):
        return render_template("addGoal.html", error="Goal name already exists", min_date=date.today().isoformat())

    from datetime import datetime
    if target_date:
        try:
            target = datetime.strptime(target_date, "%Y-%m-%d").date()
            if target < date.today():
                return render_template("addGoal.html", error="Target date cannot be in the past", min_date=date.today().isoformat())
        except ValueError:
            return render_template("addGoal.html", error="Invalid date format", min_date=date.today().isoformat())
    
    user_id = session["user_id"]
    goal_data = {
        "userId": user_id,
        "goalName": goal_name,
        "goalDescription": goal_desc,
        "goalCategory": goal_cat,
        "goalStatus": "not started",
        "targetDate": target_date,
        "progress": 0,
        "goalIcon": request.form.get("goalIcon", "🎯"),
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
        return render_template("editGoal.html", goal=goal, min_date=date.today().isoformat())
    
    user_id = session["user_id"]
    goal_name = request.form.get("goalName", "").strip()
    target_date = request.form.get("targetDate", "").strip()

    if not goal_name:
        goal = Goal.getGoalById(goal_id)
        return render_template("editGoal.html", goal=goal, error="Goal name is required", min_date=date.today().isoformat())

    if Goal.goalNameExists(user_id, goal_name, exclude_goal_id=goal_id):
        goal = Goal.getGoalById(goal_id)
        return render_template("editGoal.html", goal=goal, error="Goal name already exists", min_date=date.today().isoformat())

    from datetime import datetime
    if target_date:
        try:
            target = datetime.strptime(target_date, "%Y-%m-%d").date()
            if target < date.today():
                goal = Goal.getGoalById(goal_id)
                return render_template("editGoal.html", goal=goal, error="Target date cannot be in the past", min_date=date.today().isoformat())
        except ValueError:
            goal = Goal.getGoalById(goal_id)
            return render_template("editGoal.html", goal=goal, error="Invalid date format", min_date=date.today().isoformat())

    goal_data = {
        "id": goal_id,
        "userId": user_id,
        "goalName": goal_name,
        "goalDescription": request.form.get("goalDescription"),
        "goalCategory": request.form.get("goalCategory"),
        "goalStatus": request.form.get("goalStatus"),
        "targetDate": target_date,
        "progress": int(request.form.get("progress", 0)),
        "goalIcon": request.form.get("goalIcon", "🎯"),
    }
    
    Goal.updateGoal(goal_data)
    return redirect("/dashboard")

if __name__ == "__main__":
    app.run(debug=True)