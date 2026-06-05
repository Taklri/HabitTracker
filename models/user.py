from mysqlconnection import MysqlConnection

class User:
    MIN_PASSWORD_LENGTH = 8
    DEFAULT_AVATAR = "panda"
    ALLOWED_AVATARS = {"chicken", "dog", "gorilla", "panda", "rabbit"}

    # constructor
    def __init__(self, data):
        self.id = data["id"]
        self.username = data["username"]
        self.password = data["password"]
        self.avatar = self.normalizeAvatar(data.get("avatar"))

    @classmethod
    def normalizeAvatar(cls, avatar):
        avatar_name = str(avatar or "").strip().lower()
        if avatar_name in cls.ALLOWED_AVATARS:
            return avatar_name
        return cls.DEFAULT_AVATAR
        
    # methods exclusive for user schema
    @classmethod
    def insertUser(cls, data):
        insert_data = {
            "username": data["username"],
            "password": data["password"],
            "avatar": cls.normalizeAvatar(data.get("avatar")),
        }
        query = """INSERT INTO users (username, password, avatar) 
        VALUES (%(username)s, %(password)s, %(avatar)s);"""
        return MysqlConnection("habitUp").query_start(query, insert_data)
    
    @classmethod
    def loginUser(cls, data):
        query = """SELECT * FROM users WHERE username = %(username)s AND password = %(password)s;"""
        result = MysqlConnection("habitUp").query_start(query, data)
        if len(result) > 0:
            return cls(result[0])
        else:
            return False

    @classmethod
    def getUserById(cls, data):
        query = """SELECT * FROM users WHERE id = %(id)s;"""
        result = MysqlConnection("habitUp").query_start(query, data)
        if len(result) > 0:
            return cls(result[0])
        return False

    @classmethod
    def updateProfile(cls, data):
        update_data = {
            "id": data["id"],
            "username": data["username"],
            "avatar": cls.normalizeAvatar(data.get("avatar")),
        }

        password_fragment = ""
        if data.get("password"):
            update_data["password"] = data["password"]
            password_fragment = ", password = %(password)s"

        query = f"""UPDATE users SET username = %(username)s, avatar = %(avatar)s{password_fragment} WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, update_data)

    @classmethod
    def updateAvatar(cls, data):
        update_data = {
            "id": data["id"],
            "avatar": cls.normalizeAvatar(data.get("avatar")),
        }
        query = """UPDATE users SET avatar = %(avatar)s WHERE id = %(id)s;"""
        return MysqlConnection("habitUp").query_start(query, update_data)

    @classmethod
    def usernameExists(cls, username, exclude_user_id=None):
        params = {"username": str(username or "").strip().lower()}
        query = """SELECT id FROM users WHERE LOWER(username) = %(username)s"""

        if exclude_user_id is not None:
            query += " AND id != %(exclude_user_id)s"
            params["exclude_user_id"] = exclude_user_id

        query += " LIMIT 1;"
        result = MysqlConnection("habitUp").query_start(query, params)
        return len(result) > 0