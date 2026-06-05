from datetime import date
import os

from flask import Flask, url_for, request, render_template, session, redirect, flash, send_from_directory
app = Flask(__name__)
app.secret_key = "HabitUpKey"

from models.user import User
from models.habit import Habit
from models.goal import Goal

AVATAR_FOLDER = os.path.join(app.root_path, "avatars")

def allowedAvatars():
    return sorted(User.ALLOWED_AVATARS)

def checkAvatar(value):
    return User.normalizeAvatar(value)


@app.route("/avatars/<avatar_name>.png")
def serveAvatar(avatar_name):
    avatar = checkAvatar(avatar_name)
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
        session["avatar"] = checkAvatar(user.avatar)
        return redirect(url_for('dashboard'))
    else:
        return render_template("login.html", error="Invalid credentials")
    
@app.route("/signup")
def signupPage():
    return render_template(
        "signup.html",
        allowed_avatars=allowedAvatars(),
        default_avatar=User.DEFAULT_AVATAR,
    )

@app.route("/signup/process", methods=["POST"])
def signupProcess():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    reenterpass = request.form.get("reenterpass", "")
    selectedAvatar = checkAvatar(request.form.get("avatar"))

    newUser={
        "username": username,
        "password": password,
        "reenterpass": reenterpass,
        "avatar": selectedAvatar,
    }
    if not username:
        return render_template(
            "signup.html",
            error="Username cannot be blank",
            allowed_avatars=allowedAvatars(),
            default_avatar=selectedAvatar,
        )

    if User.usernameExists(username):
        return render_template(
            "signup.html",
            error="Username already exists",
            allowed_avatars=allowedAvatars(),
            default_avatar=selectedAvatar,
        )

    if len(password) < User.MIN_PASSWORD_LENGTH:
        return render_template(
            "signup.html",
            error=f"Password must be at least {User.MIN_PASSWORD_LENGTH} characters",
            allowed_avatars=allowedAvatars(),
            default_avatar=selectedAvatar,
        )

    if newUser["password"] != newUser["reenterpass"]:
        return render_template(
            "signup.html",
            error="Passwords do not match",
            allowed_avatars=allowedAvatars(),
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
        selected_avatar=checkAvatar(user.avatar),
        allowed_avatars=allowedAvatars(),
    )


@app.route("/update-avatar", methods=["POST"])
def updateAvatar():
    if "user_id" not in session:
        return redirect("/login")

    avatar = request.form.get("avatar")
    if not avatar:
        return redirect("/profile")

    res = User.updateAvatar({"id": session["user_id"], "avatar": avatar})
    if res is False:
        user = User.getUserById({"id": session["user_id"]})
        return render_template(
            "profile.html",
            username=user.username,
            selected_avatar=checkAvatar(user.avatar),
            allowed_avatars=allowedAvatars(),
            error="Failed to update avatar",
        )

    session["avatar"] = checkAvatar(avatar)
    user = User.getUserById({"id": session["user_id"]})
    return render_template(
        "profile.html",
        username=user.username,
        selected_avatar=checkAvatar (user.avatar),
        allowed_avatars=allowedAvatars(),
        success="Avatar updated",
    )


@app.route("/profile/process", methods=["POST"])
def profileProcess():
    if "user_id" not in session:
        return redirect("/login")

    username = request.form.get("username", "").strip()
    new_password = request.form.get("password", "")
    reenter_password = request.form.get("reenterpass", "")
    avatar = checkAvatar(request.form.get("avatar"))

    if not username:
        user = User.getUserById({"id": session["user_id"]})
        return render_template(
            "profile.html",
            username=session.get("username"),
            selected_avatar=avatar,
            allowed_avatars=allowedAvatars(),
            error="Username cannot be blank",
        )

    if User.usernameExists(username, exclude_user_id=session["user_id"]):
        return render_template(
            "profile.html",
            username=username,
            selected_avatar=avatar,
            allowed_avatars=allowedAvatars(),
            error="Username already exists",
        )

    if new_password and len(new_password) < User.MIN_PASSWORD_LENGTH:
        return render_template(
            "profile.html",
            username=username,
            selected_avatar=avatar,
            allowed_avatars=allowedAvatars(),
            error=f"Password must be at least {User.MIN_PASSWORD_LENGTH} characters",
        )

    if new_password and new_password != reenter_password:
        return render_template(
            "profile.html",
            username=username,
            selected_avatar=avatar,
            allowed_avatars=allowedAvatars(),
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


def parseCsvValues(value):
    if not value:
        return set()
    return {item.strip().lower() for item in str(value).split(",") if item.strip()}


def habitIsForToday(habit, today):
    frequency = (getattr(habit, "habitFrequency", "") or "").lower()

    if frequency == "daily":
        return True

    if frequency in {"weekly", "multiday"}:
        return today.strftime("%A").lower() in parseCsvValues(getattr(habit, "habitWeekly", None))

    if frequency == "monthly":
        habit_day = getattr(habit, "habitMonthly", None)
        try:
            return int(habit_day) == today.day
        except (TypeError, ValueError):
            return False

    return False


def habitCreatedToday(habit, today):
    created_value = getattr(habit, "created_at", None) or getattr(habit, "createdAt", None)
    if not created_value:
        return False

    created_text = str(created_value)
    return created_text[:10] == today.isoformat()


def goalIsForToday(goal, today):
    return str(getattr(goal, "targetDate", "") or "")[:10] == today.isoformat()


def habitScheduleLabel(habit):
    frequency = (getattr(habit, "habitFrequency", "") or "").lower()

    if frequency == "daily":
        return "Every day"

    if frequency == "weekly":
        days = [day.strip().title() for day in str(getattr(habit, "habitWeekly", "") or "").split(",") if day.strip()]
        return "Weekly: " + ", ".join(days) if days else "Weekly"

    if frequency == "multiday":
        days = [day.strip().title() for day in str(getattr(habit, "habitWeekly", "") or "").split(",") if day.strip()]
        return "Multiple days: " + ", ".join(days) if days else "Multiple days"

    if frequency == "monthly":
        day = getattr(habit, "habitMonthly", None)
        return f"Monthly: Day {day}" if day else "Monthly"

    return frequency.title() if frequency else "Unspecified"


def habitSortKey(habit):
    created_value = getattr(habit, "created_at", None) or getattr(habit, "createdAt", None)
    if created_value:
        return str(created_value)
    return str(getattr(habit, "id", 0))


def goalSortKey(goal):
    return str(getattr(goal, "targetDate", "") or "")


def habitIsCompleted(habit):
    status = str(getattr(habit, "habitStatus", "") or "").strip().lower()
    return status in {"done", "completed"}


def goalIsCompleted(goal):
    status = str(getattr(goal, "goalStatus", "") or "").strip().lower()
    return status == "completed"


def sortedHabits(user_id):
    habits = Habit.getHabitsByUser(user_id)
    return sorted(habits, key=habitSortKey)


def sortedGoals(user_id):
    goals = Goal.getGoalsByUser(user_id)
    return sorted(goals, key=goalSortKey)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    today = date.today()

    selected_habit_category = request.args.get("habit_category", "").strip() or None
    selected_goal_category = request.args.get("goal_category", "").strip() or None

    if selected_habit_category:
        all_habits = sorted(Habit.filterHabitsByCategory(user_id, selected_habit_category), key=habitSortKey)
    else:
        all_habits = sortedHabits(user_id)

    if selected_goal_category:
        all_goals = sorted(Goal.filterGoalsByCategory(user_id, selected_goal_category), key=goalSortKey)
    else:
        all_goals = sortedGoals(user_id)

    todays_habits = [
        habit for habit in all_habits
        if (habitIsForToday(habit, today) or habitCreatedToday(habit, today)) and not habitIsCompleted(habit)
    ]
    todays_goals = [goal for goal in all_goals if goalIsForToday(goal, today) and not goalIsCompleted(goal)]

    return render_template(
        "dashboardSample.html",
        username=session["username"],
        avatar=checkAvatar(session.get("avatar")),
        today=today,
        today_label=today.strftime("%A, %B %d, %Y"),
        habits=todays_habits,
        all_habits=all_habits,
        goals=todays_goals,
        all_goals=all_goals,
        habit_schedule_label=habitScheduleLabel,
        selected_habit_category=selected_habit_category,
        selected_goal_category=selected_goal_category,
    )


@app.route("/all-habits")
def allHabits():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]

    # fetch all and then apply optional filters from query params
    habits = sortedHabits(user_id)

    search = (request.args.get("search") or "").strip().lower()
    frequency = (request.args.get("frequency") or "").strip().lower()
    category = (request.args.get("category") or "").strip().lower()

    def match(h):
        if search:
            if search not in (str(getattr(h, "habitName", "") or "").lower()):
                return False
        if frequency:
            if (getattr(h, "habitFrequency", "") or "").lower() != frequency:
                return False
        if category:
            if (str(getattr(h, "habitCategory", "") or "").lower() != category):
                return False
        return True

    filtered = [h for h in habits if match(h)]
    # build category list for dropdown
    habit_categories = sorted({(h.habitCategory or "").strip() for h in habits if (h.habitCategory or "").strip()})

    return render_template(
        "allHabit.html",
        username=session["username"],
        avatar=checkAvatar(session.get("avatar")),
        habits=filtered,
        habit_schedule_label=habitScheduleLabel,
        habit_categories=habit_categories,
    )

@app.route("/all-goals")
def allGoals():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    goals = sortedGoals(user_id)

    search = (request.args.get("search") or "").strip().lower()
    category = (request.args.get("category") or "").strip().lower()
    due = (request.args.get("due") or "").strip()

    def match(g):
        if search:
            if search not in (str(getattr(g, "goalName", "") or "").lower()):
                return False
        if category:
            if (str(getattr(g, "goalCategory", "") or "").lower() != category):
                return False
        if due:
            # compare YYYY-MM-DD prefix
            if str(getattr(g, "targetDate", "") or "")[:10] != due:
                return False
        return True

    filtered = [g for g in goals if match(g)]
    # build category list for dropdown
    goal_categories = sorted({(g.goalCategory or "").strip() for g in goals if (g.goalCategory or "").strip()})

    return render_template(
        "allGoals.html",
        username=session["username"],
        avatar=checkAvatar(session.get("avatar")),
        goals=filtered,
        goal_categories=goal_categories,
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


    if habitFrequency in ("weekly", "multiday"):
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


@app.route("/done-habit/<int:habit_id>", methods=["POST"])
def doneHabit(habit_id):
    if "user_id" not in session:
        return redirect("/login")

    habit = Habit.getHabitById(habit_id)
    if not habit or habit.userId != session["user_id"]:
        return redirect("/dashboard")

    today = date.today()
    if not (habitIsForToday(habit, today) or habitCreatedToday(habit, today)):
        return redirect("/dashboard")

    Habit.updateHabit({
        "id": habit_id,
        "habitName": habit.habitName,
        "habitCategory": habit.habitCategory,
        "habitDescription": habit.habitDescription,
        "habitFrequency": habit.habitFrequency,
        "habitWeekly": habit.habitWeekly,
        "habitMonthly": habit.habitMonthly,
        "habitIcon": habit.habitIcon,
        "habitStatus": "done",
    })
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

    # load existing habit for POST and ensure ownership
    habit = Habit.getHabitById(habit_id)
    if not habit or habit.userId != session["user_id"]:
        return redirect("/dashboard")

    habitFrequency = request.form.get("habitFrequency")
    weekly_days = None
    monthly_day = None

    if habitFrequency in ("weekly", "multiday"):
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
        "habitStatus": getattr(habit, "habitStatus", None),
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
        "goalIcon": request.form.get("goalIcon"),
    }
    
    Goal.createGoal(goal_data)
    return redirect("/dashboard")

@app.route("/delete-goal/<int:goal_id>", methods=["POST"])
def deleteGoal(goal_id):
    if "user_id" not in session:
        return redirect("/login")
    
    Goal.deleteGoal(goal_id)
    return redirect("/dashboard")


@app.route("/done-goal/<int:goal_id>", methods=["POST"])
def doneGoal(goal_id):
    if "user_id" not in session:
        return redirect("/login")

    goal = Goal.getGoalById(goal_id)
    if not goal or goal.userId != session["user_id"]:
        return redirect("/dashboard")

    if not goalIsForToday(goal, date.today()):
        return redirect("/dashboard")

    Goal.updateGoal({
        "id": goal_id,
        "goalName": goal.goalName,
        "goalDescription": goal.goalDescription,
        "goalCategory": goal.goalCategory,
        "goalStatus": "completed",
        "targetDate": goal.targetDate,
        "goalIcon": goal.goalIcon,
    })
    return redirect("/dashboard")

@app.route("/edit-goal/<int:goalid>", methods=["GET", "POST"])
def editGoal(goalid):
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "GET":
        goal = Goal.getGoalById(goalid)
        return render_template("editGoal.html", goal=goal, min_date=date.today().isoformat())
    
    userId = session["user_id"]
    goalName = request.form.get("goalName", "").strip()
    target_date = request.form.get("targetDate", "").strip()

    if not goalName:
        goal = Goal.getGoalById(goalid)
        return render_template("editGoal.html", goal=goal, error="Goal name is required", min_date=date.today().isoformat())

    if Goal.goalNameExists(userId, goalName, exclude_goal_id=goalid):
        goal = Goal.getGoalById(goalid)
        return render_template("editGoal.html", goal=goal, error="Goal name already exists", min_date=date.today().isoformat())

    from datetime import datetime
    if target_date:
        try:
            target = datetime.strptime(target_date, "%Y-%m-%d").date()
            if target < date.today():
                goal = Goal.getGoalById(goalid)
                return render_template("editGoal.html", goal=goal, error="Target date cannot be in the past", min_date=date.today().isoformat())
        except ValueError:
            goal = Goal.getGoalById(goalid)
            return render_template("editGoal.html", goal=goal, error="Invalid date format", min_date=date.today().isoformat())

    goal_data = {
        "id": goalid,
        "userId": userId,
        "goalName": goalName,
        "goalDescription": request.form.get("goalDescription"),
        "goalCategory": request.form.get("goalCategory"),
        "goalStatus": request.form.get("goalStatus"),
        "targetDate": target_date,
        "goalIcon": request.form.get("goalIcon"),
    }
    
    Goal.updateGoal(goal_data)
    return redirect("/dashboard")

@app.route("/search-habits", methods=["GET", "POST"])
def searchHabits():
    if "user_id" in session:
        if request.method == "POST":
            search = (request.form.get("search") or "").strip()
            if search == "":
                return redirect("/all-habits")
            return redirect(url_for("searchHabits", search=search))

        if request.args.get("search") is None:
            allData = sortedHabits(session["user_id"])
        else:
            if request.args.get("search") == "":
                allData = sortedHabits(session["user_id"])
            else:
                searchData = request.args.get("search")
                allData = Habit.searchHabits(session["user_id"], searchData)
        return render_template(
            "allHabit.html",
            username=session["username"],
            avatar=checkAvatar(session.get("avatar")),
            habits=allData,
            habit_schedule_label=habitScheduleLabel,
            search_query=request.args.get("search"),
        )
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)