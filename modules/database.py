import sqlite3
import modules.checks
import modules.lobby_data as lobby_data


class Database:
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
            metadata blob NOT NULL
        );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS serverSettings (
            serverID bigint PRIMARY KEY,
            timezone smallint NOT NULL
        );
        """)

        self.connection.commit()

    def store_lobby(self, lobby: lobby_data.LobbyData):
        if "channel" in lobby.metadata:
            channel_id = lobby.metadata["channel"].id
            self.cursor.execute()


    def get_lobby_for_channel(self, channel):
        self.cursor.execute()
        pass


if __name__ == "__main__":
    mydb = Database()
    mydb.create_database()
