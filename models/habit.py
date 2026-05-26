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

    # methods exclusive for habit schema
    @classmethod
    def insertHabit(cls, data):
        query = """INSERT INTO habit (userId, habitName, habitCategory, habitDescription, habitFrequency, habitWeekly, habitMonthly) 
        VALUES (%(userId)s, %(habitName)s, %(habitCategory)s, %(habitDescription)s, %(habitFrequency)s, %(habitWeekly)s, %(habitMonthly)s);"""
        return MysqlConnection("habitUp").query_start(query, data)