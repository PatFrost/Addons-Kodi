
idVersion = 1

from hashlib import sha1
from traceback import print_exc

# http://docs.python.org/library/sqlite3.html
try:
    import sqlite3
    sql_connect = sqlite3.connect
except:
    raise
    #try: import sqlite
    #except:
    #    try: from pysqlite2 import dbapi2 as sqlite
    #    except: sqlite = None
    #def sql_connect( *args, **kwargs ):
    #    return sqlite.connect( *args )


GAMES_DB = "AddonGames%i.db" % idVersion
try:
    from xbmc import getInfoLabel, translatePath
    GAMES_DB = translatePath( "special://database/" + GAMES_DB )
except:
    #print_exc()
    pass



# table scores = idScore, idUser, score, level, perfect, strMode, strTimePlayed, strDate, online, strGameId
# table users  = idUser, strNickName, strUserName, strPass, strAvatar
def createTables( c ):
    # http://docs.python.org/library/sqlite3.html#sqlite3.Cursor.executescript
    # Create tables
    many = None
    try:
        many = c.executescript("PRAGMA page_size=4096;" \
                               "PRAGMA default_cache_size=4096;")
                        
        many = c.executescript("CREATE TABLE version ( idVersion INTEGER, iCompressCount INTEGER );" \
                               "INSERT INTO version ( idVersion, iCompressCount ) VALUES( %i, 0 );" % idVersion)
                        
        many = c.executescript(
            """
            CREATE TABLE scores (
            idScore INTEGER PRIMARY KEY,
            idUser INTEGER,
            score INTEGER,
            level INTEGER,
            perfect INTEGER,
            strMode TEXT,
            strTimePlayed TEXT,
            strDate TEXT,
            online BOOL,
            strGameId TEXT,
            hash TEXT );
            CREATE UNIQUE INDEX ix_scores_1 ON scores ( idScore );

            CREATE TABLE users ( idUser INTEGER PRIMARY KEY, strNickName TEXT, strUserName TEXT, strPass TEXT, strAvatar TEXT );
            CREATE UNIQUE INDEX ix_users_1 ON users ( idUser );
            """
            #CREATE TABLE games ( idGame INTEGER PRIMARY KEY, strGameId TEXT, strGameName TEXT, strGameIcon TEXT );
            #CREATE UNIQUE INDEX ix_games_1 ON games ( idGame );
            )
    except:
        print locals()
        print_exc()
    return many


def getVersion( c ):
    version = 0
    try: version = c.execute( "SELECT idVersion FROM version" ).fetchone()[ 0 ]
    except: pass #print_exc()
    return version


def getConnection():
    con = sql_connect( GAMES_DB, check_same_thread=False )
    cur = con #.cursor()

    if not getVersion( cur ):
        if createTables( cur ):
            con.commit()
        else:
            con.rollback()

    many = con.executescript("PRAGMA cache_size=4096;" \
                             "PRAGMA synchronous='NORMAL';" \
                             "PRAGMA count_changes='OFF';")
    return con, cur


def addScore( score ):
    OK = 0
    idScore = -1
    con, cur = getConnection()
    try:
        # first get id user, if not exists insert
        idUser = con.execute( "SELECT idUser FROM users WHERE LOWER(strNickName)=LOWER(?)", ( score[ "strNickName" ], ) ).fetchone()
        if not idUser:
            insert = con.execute( "INSERT INTO users VALUES ( NULL, ?, ?, ?, ? )",
                ( score[ "strNickName" ], score.get( "strUserName" ), score.get( "strPass" ), score.get( "strAvatar" ) )
                )
            if insert.rowcount:
                OK += 1
                idUser = [ insert.lastrowid ]
                #idUser = con.execute( "SELECT idUser FROM users WHERE strNickName=?", ( score[ "strNickName" ], ) ).fetchone()
        idUser = idUser[ 0 ]

        # now insert new score
        values = ( idUser, score[ "score" ], score.get( "level" ), score.get( "perfect" ), score.get( "strMode" ),
            score.get( "strTimePlayed" ), score.get( "strDate" ), score.get( "online" ), score[ "strGameId" ]
            )
        insert = con.execute( "INSERT INTO scores VALUES ( NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL )", values )
        if insert.rowcount:
            # get idScore
            #idScore = con.execute( "SELECT idScore FROM scores WHERE idUser=? AND score=? ORDER BY idScore DESC", ( idUser, score[ "score" ] ) ).fetchone()
            #idScore = idScore[ 0 ]#[ 2 ]
            OK += 1
            idScore = insert.lastrowid
            score = con.execute( "SELECT * FROM scores WHERE idScore=?", ( idScore, ) ).fetchone()
            if score: OK += con.execute( "UPDATE scores SET hash=? WHERE idScore=?", ( sha1( str( score ) ).hexdigest() , idScore ) ).rowcount
    except:
        print locals()
        print_exc()
    if OK: con.commit()
    else: con.rollback()
    con.close()
    return OK, idScore


def getScore( idScore ):
    con, cur = getConnection()
    score = []
    try:
        score = con.execute( "SELECT scores.*, users.strNickName, users.strAvatar FROM scores JOIN users ON users.idUser=scores.idUser WHERE idScore=?", ( idScore, ) ).fetchone()
    except:
        print locals()
        print_exc()
    con.close()
    return score


def getScores( strGameId, hi_scores=0, keys=0 ):
    scores = []
    con, cur = getConnection()
    try:
        #idScore, idUser, score, level, perfect, strMode, strTimePlayed, strDate, online, strGameId, strNickName, strAvatar
        sql = "SELECT scores.*, users.strNickName, users.strAvatar FROM scores JOIN users ON users.idUser=scores.idUser"
        if hi_scores:
            sql += " WHERE scores.score=(SELECT MAX(score) FROM scores AS m WHERE {0}={1!r} AND m.strMode=scores.strMode)"
            #sql += " AND scores.perfect=(SELECT MAX(perfect) FROM scores AS p WHERE {0}={1!r} AND p.strMode=scores.strMode)"
            sql += " AND {0}={1!r} ORDER BY strMode"
        else:
            sql += " WHERE {0}={1!r} ORDER BY strMode, score DESC"
        sql = sql.format( "strGameId", str( strGameId ) )

        scores = [ s for s in con.execute( sql ) ]
        if keys:
            keys   = [ u"idScore", u"idUser", u"score", u"level", u"perfect", u"strMode", u"strTimePlayed", u"strDate", u"online", u"strGameId", u"hash", u"strNickName", u"strAvatar" ]
            scores = [ dict( zip( keys, s ) ) for s in scores ]
    except:
        print locals()
        print_exc()
    con.close()
    return scores


def removeScore( idScore ):
    OK = 0
    con, cur = getConnection()
    try: OK += con.execute( "DELETE FROM scores WHERE idScore=?", ( int( idScore ), ) ).rowcount
    except:
        print locals()
        print_exc()
    if OK: con.commit()
    else: con.rollback()
    con.close()
    return OK


def removeScores( strGameId, strMode=None ):
    OK = 0
    con, cur = getConnection()     
    try:
        if strMode: OK += con.execute( "DELETE FROM scores WHERE strGameId=? AND strMode=?", ( strGameId, strMode ) ).rowcount
        else: OK += con.execute( "DELETE FROM scores WHERE strGameId=?", ( strGameId, ) ).rowcount
    except:
        print locals()
        print_exc()
    if OK: con.commit()
    else: con.rollback()
    con.close()
    return OK


def removeUserScores( idUser, strGameId ):
    OK = 0
    con, cur = getConnection()
    try: OK += con.execute( "DELETE FROM scores WHERE idUser=? AND strGameId=?", ( int( idUser ), strGameId ) ).rowcount
    except:
        print locals()
        print_exc()
    if OK: con.commit()
    else: con.rollback()
    con.close()
    return OK


def setUserAvatar( idUser, strAvatar ):
    OK = 0
    con, cur = getConnection()
    try: OK += con.execute( "UPDATE users SET strAvatar=? WHERE idUser=?", ( strAvatar , int( idUser ) ) ).rowcount
    except:
        print locals()
        print_exc()
    if OK: con.commit()
    else: con.rollback()
    con.close()
    return OK


def getGames():
    games = []
    con, cur = getConnection()
    try:
        for game in con.execute( "SELECT strGameId FROM scores GROUP BY strGameId" ):
            game = ( getInfoLabel( "System.AddonTitle(%s)" % game ), getInfoLabel( "System.AddonIcon(%s)" % game ), game[ 0 ] )
            games.append( game )
    except:
        print locals()
        print_exc()
    con.close()
    return games

    

if __name__ == '__main__':
    #print "WHERE {0}={1!r} ORDER BY strMode, score DESC".format( "strGameId", str( u"script.game.duck.hunt" ) )
    score = {
        "strNickName": "frost",
        "score": 33000,
        "level": 4,
        "perfect": 0,
        "strMode": "Game A",
        "strTimePlayed": "3:40",
        "strDate": "2012-10-15",
        "strGameId": "script.game.duck.hunt",
        }
    print addScore( score )
    #print removeScore( 4 )
    #print removeScores( strGameId=score[ "strGameId" ] )
    #print removeUserScores( 2, score[ "strGameId" ] )
    #print setUserAvatar( 1, "avatar_227.png" )
    #for s in getScores( score[ "strGameId" ], 0, 1 ):
    #    print s
    #print getScore( 2 )

