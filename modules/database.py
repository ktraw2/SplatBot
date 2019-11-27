import sqlite3
import modules.checks
import pytz
from modules.lobby_data import LobbyData
from datetime import datetime
import pickle


class Database:
    fieldNames = {
        "channelID": "channelID",
        "players": "players",
        "lobbyName": "lobbyName",
        "rotationData": "rotationData",
        "numPlayers": "numPlayers",
        "lobbyTime": "lobbyTime",
        "notified": "notified"
    }

    def __init__(self, dbfile: str = "splatbot.db"):
        modules.checks.make_sure_file_exists(dbfile)
        self.connection = sqlite3.connect(dbfile)
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    def create_database(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS lobbies (
            channelID bigint PRIMARY KEY,
            players blob NOT NULL,
            lobbyName text NOT NULL,
            rotationData blob DEFAULT NULL,
            numPlayers int DEFAULT 0,
            lobbyTime bigint NOT NULL,
            notified bool DEFAULT false
        );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS serverSettings (
            serverID bigint PRIMARY KEY,
            timezone text NOT NULL
        );
        """)
        self.connection.commit()

    def store_lobby(self, lobby: LobbyData):
        self.cursor.execute("""
        INSERT INTO lobbies VALUES (?,?,?,?,?,?,?);
        """,
        (lobby.channel, pickle.dumps(lobby.players), lobby.name,
         pickle.dumps(lobby.rotation_data), lobby.num_players, lobby.time.timestamp(), lobby.notified))
        self.connection.commit()

    def get_all_lobbies_cursor(self):
        self.cursor.execute("""
        SELECT * FROM lobbies
        """)
        return self.cursor.fetchall()

    def get_lobby_for_channel(self, channel: int):
        self.cursor.execute("""
        SELECT * FROM lobbies WHERE channelID = ?;
        """, (channel,))
        row = self.cursor.fetchone()
        self.cursor.fetchall()
        if row is not None:
            return self.make_lobby_from_row(row)
        return None

    def delete_lobby_for_channel(self, channel: int):
        self.cursor.execute("""
        DELETE FROM lobbies WHERE channelID = ?;
        """, (channel,))
        self.connection.commit()

    def update_lobby_row(self, channel: int, field, value):
        self.cursor.execute("""
        UPDATE lobbies
        SET {} = ?
        WHERE channelID = ?;
        """.format(Database.fieldNames[field]), (value, channel))
        self.connection.commit()

    def make_lobby_from_row(self, row):
        return LobbyData(channel=row[0], players=pickle.loads(row[1]), name=row[2],
                         rotation_data=pickle.loads(row[3]), num_players=row[4], time=datetime.fromtimestamp(row[5]),
                         notified=row[6], database=self)

    def time_zone_for_server(self, server: int):
        self.cursor.execute("""
        SELECT timezone FROM serverSettings WHERE serverID = ?
        """, (server,))
        row = self.cursor.fetchone()
        self.cursor.fetchall()
        if row is not None:
            try:
                return pytz.timezone(row[0])
            except pytz.UnknownTimeZoneError:
                return pytz.utc

        return pytz.utc


if __name__ == "__main__":
    mydb = Database()
    mydb.create_database()
