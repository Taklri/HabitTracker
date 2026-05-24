from mysqlconnection import MysqlConnection

class User:
    # constructor
    def __init__(self, data):
        self.id = data["id"]
        self.username = data["username"]
        self.password = data["password"]
        
    # methods exclusive for user schema
    @classmethod
    def insertUser(cls, data):
        query = """INSERT INTO users (username, password) 
        VALUES (%(username)s, %(password)s);"""
        return MysqlConnection("habitUp").query_start(query, data)
    
    @classmethod
    def loginUser(cls, data):
        query = """SELECT * FROM users WHERE username = %(username)s AND password = %(password)s;"""
        result = MysqlConnection("habitUp").query_start(query, data)
        if len(result) > 0:
            return cls(result[0])
        else:
            return False