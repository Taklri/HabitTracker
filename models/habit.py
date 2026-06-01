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
        self.habitIcon = data.get("habitIcon", "📋") 

    # methods exclusive for habit schema
    @classmethod
    def insertHabit(cls, data):
        query = """INSERT INTO habit (userId, habitName, habitCategory, habitDescription, habitFrequency, habitWeekly, habitMonthly, habitIcon) 
        VALUES (%(userId)s, %(habitName)s, %(habitCategory)s, %(habitDescription)s, %(habitFrequency)s, %(habitWeekly)s, %(habitMonthly)s, %(habitIcon)s);"""
        return MysqlConnection("habitUp").query_start(query, data)
    
    @classmethod
    def getHabitsByUser(cls, user_id):
        query = """SELECT * FROM habit WHERE userId = %(userId)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"userId": user_id})
        habits = []
        if len(result) > 0:
            for row in result:
                habits.append(cls(row))
        return habits

    @classmethod
    def getHabitById(cls, habit_id):
        query = """SELECT * FROM habit WHERE id = %(id)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"id": habit_id})
        if len(result) > 0:
            return cls(result[0])
        return None

    @classmethod
    def deleteHabit(cls, habit_id):
        query = """DELETE FROM habit WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, {"id": habit_id})
    
    @classmethod
    def editHabit(cls, data):
        query = """UPDATE habit SET habitName = %(habitName)s, habitCategory = %(habitCategory)s, habitDescription = %(habitDescription)s, habitFrequency = %(habitFrequency)s, habitWeekly = %(habitWeekly)s, habitMonthly = %(habitMonthly)s, habitIcon = %(habitIcon)s WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, data)

    @classmethod
    def updateHabit(cls, data):
        return cls.editHabit(data)
    
    @classmethod
    def filterHabitsByCategory(cls, user_id, category):
        query = """SELECT * FROM habit WHERE userId = %(userId)s AND habitCategory = %(category)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"userId": user_id, "category": category})
        habits = []
        if len(result) > 0:
            for row in result:
                habits.append(cls(row))
        return habits

    @classmethod
    def habitNameExists(cls, user_id, habit_name, exclude_habit_id=None):
        params = {
            "userId": user_id,
            "habitName": str(habit_name or "").strip().lower(),
        }
        query = """
        SELECT id FROM habit
        WHERE userId = %(userId)s
          AND LOWER(habitName) = %(habitName)s
        """

        if exclude_habit_id is not None:
            query += " AND id != %(exclude_habit_id)s"
            params["exclude_habit_id"] = exclude_habit_id

        query += " LIMIT 1;"
        result = MysqlConnection("habitUp").query_start(query, params)
        return len(result) > 0