from mysqlconnection import MysqlConnection

class Habit:
    # constructor
    def __init__(self, data):
        self.id = data["id"]
        self.userId = data["userId"]
        self.habitName = data["habitName"]
        self.habitCategory = data["habitCategory"]
        self.habitDescription = data["habitDescription"]
        self.habitFrequency = data["habitFrequency"]
        self.habitWeekly = data["habitWeekly"]
        self.habitMonthly = data["habitMonthly"]
        self.habitStatus = data.get("habitstatus") or data.get("habitStatus")
        self.habitIcon = data.get("habitIcon")
        self.created_at = data.get("created_at") or data.get("createdAt")

    # methods
    @classmethod
    def insertHabit(cls, data):
        query = """INSERT INTO habit (userId, habitName, habitCategory, habitDescription, habitFrequency, habitWeekly, habitMonthly, habitIcon) 
        VALUES (%(userId)s, %(habitName)s, %(habitCategory)s, %(habitDescription)s, %(habitFrequency)s, %(habitWeekly)s, %(habitMonthly)s, %(habitIcon)s);"""
        return MysqlConnection("habitUp").query_start(query, data)
    
    @classmethod
    def getHabitsByUser(cls, userId):
        query = """SELECT * FROM habit WHERE userId = %(userId)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"userId": userId})
        habits = []
        if len(result) > 0:
            for row in result:
                habits.append(cls(row))
        return habits

    @classmethod
    def getHabitById(cls, habitId):
        query = """SELECT * FROM habit WHERE id = %(id)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"id": habitId})
        if len(result) > 0:
            return cls(result[0])
        return None

    @classmethod
    def deleteHabit(cls, habitId):
        query = """DELETE FROM habit WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, {"id":habitId})
    
    @classmethod
    def editHabit(cls, data):
        query = """UPDATE habit SET habitName = %(habitName)s, habitCategory = %(habitCategory)s, habitDescription = %(habitDescription)s, habitFrequency = %(habitFrequency)s, habitWeekly = %(habitWeekly)s, habitMonthly = %(habitMonthly)s, habitIcon = %(habitIcon)s, habitstatus = %(habitStatus)s WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, data)

    @classmethod
    def updateHabit(cls, data):
        return cls.editHabit(data)
    
    @classmethod
    def filterHabitsByCategory(cls, userId, category):
        query = """SELECT * FROM habit WHERE userId = %(userId)s AND habitCategory = %(category)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"userId": userId, "category": category})
        habits = []
        if len(result) > 0:
            for row in result:
                habits.append(cls(row))
        return habits

    @classmethod
    def habitNameExists(cls, userId, habitName, exclude_habit_id=None):
        params = {
            "userId": userId,
            "habitName": str(habitName or "").strip().lower(),
        }
        query = """SELECT id FROM habit WHERE userId = %(userId)s AND LOWER(habitName) = %(habitName)s"""

        if exclude_habit_id is not None:
            query += " AND id != %(exclude_habit_id)s"
            params["exclude_habit_id"] = exclude_habit_id

        query += " LIMIT 1;"
        result = MysqlConnection("habitUp").query_start(query, params)
        return len(result) > 0
    
    @classmethod
    def searchHabits(cls, userId, search):
        normalized_search = str(search or "").lower()
        normalized_search = "".join(ch for ch in normalized_search if ch.isalnum())

        all_habits = cls.getHabitsByUser(userId)
        habits = []

        for habit in all_habits:
            normalized_name = "".join(ch for ch in str(habit.habitName or "").lower() if ch.isalnum())
            if normalized_search in normalized_name:
                habits.append(habit)

        return habits