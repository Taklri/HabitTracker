from mysqlconnection import MysqlConnection

class Goal:
    def __init__(self, data):
        self.id = data["id"]
        self.userId = data["userId"]
        self.goalName = data["goalName"]
        self.goalDescription = data["goalDescription"]
        self.goalCategory = data["goalCategory"]
        self.goalStatus = data["goalStatus"]
        self.targetDate = data["targetDate"]
        self.progress = data["progress"]
        self.goalIcon = data.get("goalIcon", "🎯")

    @classmethod
    def createGoal(cls, data):
        query = """INSERT INTO goals (userId, goalName, goalDescription, goalCategory, goalStatus, targetDate, progress, goalIcon) 
        VALUES (%(userId)s, %(goalName)s, %(goalDescription)s, %(goalCategory)s, %(goalStatus)s, %(targetDate)s, %(progress)s, %(goalIcon)s);"""
        return MysqlConnection("habitUp").query_start(query, data)

    @classmethod
    def getGoalsByUser(cls, user_id):
        query = """SELECT * FROM goals WHERE userId = %(user_id)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"user_id": user_id})
        goals = []
        if len(result) > 0:
            for row in result:
                goals.append(cls(row))
        return goals

    @classmethod
    def updateGoal(cls, data):
        query = """UPDATE goals SET goalName = %(goalName)s, goalDescription = %(goalDescription)s, goalCategory = %(goalCategory)s, 
        goalStatus = %(goalStatus)s, targetDate = %(targetDate)s, progress = %(progress)s, goalIcon = %(goalIcon)s WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, data)

    @classmethod
    def deleteGoal(cls, goal_id):
        query = """DELETE FROM goals WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, {"id": goal_id})

    @classmethod
    def getGoalById(cls, goal_id):
        query = """SELECT * FROM goals WHERE id = %(id)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"id": goal_id})
        if len(result) > 0:
            return cls(result[0])
        return None
    
    @classmethod
    def filterGoalsByCategory(cls, user_id, category):
        query = """SELECT * FROM goals WHERE userId = %(user_id)s AND goalCategory = %(category)s;"""
        result = MysqlConnection("habitUp").query_start(query, {"user_id": user_id, "category": category})
        goals = []
        if len(result) > 0:
            for row in result:
                goals.append(cls(row))
        return goals

    @classmethod
    def goalNameExists(cls, user_id, goal_name, exclude_goal_id=None):
        params = {
            "user_id": user_id,
            "goalName": str(goal_name or "").strip().lower(),
        }
        query = """
        SELECT id FROM goals
        WHERE userId = %(user_id)s
          AND LOWER(goalName) = %(goalName)s
        """

        if exclude_goal_id is not None:
            query += " AND id != %(exclude_goal_id)s"
            params["exclude_goal_id"] = exclude_goal_id

        query += " LIMIT 1;"
        result = MysqlConnection("habitUp").query_start(query, params)
        return len(result) > 0