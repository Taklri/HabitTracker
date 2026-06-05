import pymysql.cursors

class MysqlConnection:
    def __init__(self, db):
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='root',
            port=3307,
            db="habitUp",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor)
        self.connection = connection
        
    def query(self, query, data=None):
        with self.connection.cursor() as cursor:
           try:
               query = cursor.mogrify(query, data)
               print("Running Query: ", query)
               cursor.execute(query, data)
               if query.lower().find("insert") >= 0:
                   self.connection.commit()
                   return cursor.lastrowid
               elif query.lower().find("select") >= 0:
                    return cursor.fetchall()
               else:
                     self.connection.commit()
           except Exception as e:
                  print("Something went wrong: ", e)
                  return False
           finally:
               self.connection.close()               

    def query_start(self, query, data=None):
        return self.query(query, data)
        