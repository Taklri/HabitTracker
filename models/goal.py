from mysqlconnection import MysqlConnection

class Goal:
    def __init__(self, data):
        self.id = data["id"]
        self.userId = data["userId"]
        self.goalName = data["goalName"]
        self.goalDescription = data["goalDescription"]
        self.goalCategory = data["goalCategory"]
        self.goalStatus = data["goalStatus"]
        self.targetDate = data.get("targetDate")
        self.progress = data.get("progress")
        self.goalIcon = data.get("goalIcon")

    @classmethod
    def createGoal(cls, data):
        query = """INSERT INTO goals (userId, goalName, goalDescription, goalCategory, goalStatus, targetDate, goalIcon) 
        VALUES (%(userId)s, %(goalName)s, %(goalDescription)s, %(goalCategory)s, %(goalStatus)s, %(targetDate)s, %(goalIcon)s);"""
        return MysqlConnection("habitUp").query_start(query, data)

    @classmethod
    def getGoalsByUser(cls, userId):
        query = """SELECT * FROM goals WHERE userId = %(userId)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"userId": userId})
        goals = []
        if len(result) > 0:
            for row in result:
                goals.append(cls(row))
        return goals

    @classmethod
    def updateGoal(cls, data):
        query = """UPDATE goals SET goalName = %(goalName)s, goalDescription = %(goalDescription)s, goalCategory = %(goalCategory)s, 
        goalStatus = %(goalStatus)s, targetDate = %(targetDate)s, goalIcon = %(goalIcon)s WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, data)

    @classmethod
    def deleteGoal(cls, goalId):
        query = """DELETE FROM goals WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, {"id": goalId})

    @classmethod
    def getGoalById(cls, goalId):
        query = """SELECT * FROM goals WHERE id = %(id)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"id": goalId})
        if len(result) > 0:
            return cls(result[0])
        return None
    
    @classmethod
    def filterGoalsByCategory(cls, userId, category):
        query = """SELECT * FROM goals WHERE userId = %(userId)s AND goalCategory = %(category)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"userId": userId, "category": category})
        goals = []
        if len(result) > 0:
            for row in result:
                goals.append(cls(row))
        return goals

    @classmethod
    def goalNameExists(cls, userId, goalName, exclude_goal_id=None):
        params = {
            "userId": userId,
            "goalName": str(goalName or "").strip().lower(),
        }
        query = """
        SELECT id FROM goals
        WHERE userId = %(userId)s
          AND LOWER(goalName) = %(goalName)s
        """

        if exclude_goal_id is not None:
            query += " AND id != %(exclude_goal_id)s"
            params["exclude_goal_id"] = exclude_goal_id

        query += " LIMIT 1;"
        result = MysqlConnection("habitUp").query_start(query, params)
        return len(result) > 0