import pymysql

def connectdb():
    print('连接到mysql服务器...')
    db = pymysql.connect(
        host="localhost",
        user="root",
        passwd="test",
        port=3306,
        db="test",
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor)
    print('连接上了!')
    return db

connectdb()