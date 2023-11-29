#!/usr/bin/env python3
import sqlite3


class IPProvider:
    DB_PATH = "../ips.sqlite"

    def __init__(self, ip_gateway: str, ip_version: str):
        self.IP_GATEWAY = ip_gateway
        self.IP_VERSION = ip_version
        self.db = sqlite3.connect(self.DB_PATH)

        self.db.execute(f"CREATE TABLE IF NOT EXISTS {self.IP_VERSION}"
                        f"(ip TEXT PRIMARY KEY, free INTEGER, last_used_by TEXT, last_used_for TEXT, last_used_at TEXT)")

    @staticmethod
    def create_db():
        db = sqlite3.connect(IPProvider.DB_PATH)
        db.execute("CREATE TABLE ipv4 (ip TEXT, free INTEGER, last_used_by TEXT, last_used_for TEXT, last_used_at TEXT)")
        db.execute("CREATE TABLE ipv6 (ip TEXT, free INTEGER, last_used_by TEXT, last_used_for TEXT, last_used_at TEXT)")
        db.commit()
        db.close()

    def get_all_ips(self) -> list:
        self.db = sqlite3.connect(self.DB_PATH)
        db_return = self.db.execute(f"SELECT ip FROM {self.IP_VERSION}").fetchall()
        return [ip[0] for ip in db_return]

    def get_available_ips(self) -> list:
        self.db = sqlite3.connect(self.DB_PATH)
        db_return = self.db.execute(f"SELECT ip FROM {self.IP_VERSION} WHERE free = 1").fetchall()
        return [ip[0] for ip in db_return]

    def get_used_ips(self) -> list:
        self.db = sqlite3.connect(self.DB_PATH)
        db_return = self.db.execute(f"SELECT ip FROM {self.IP_VERSION} WHERE free = 0").fetchall()
        return [ip[0] for ip in db_return]

    def get_used_ips_by_user(self, user) -> list:
        self.db = sqlite3.connect(self.DB_PATH)
        db_return = self.db.execute(f"SELECT ip, last_used_for FROM {self.IP_VERSION} "
                                    f"WHERE free = 0 "
                                    f"AND last_used_by = '{user}'").fetchall()
        return [{"ip": ip[0], "used_for": ip[1]} for ip in db_return]

    def is_free(self, ip) -> bool:
        return self.db.execute(f"SELECT free FROM {self.IP_VERSION} WHERE ip = '{ip}'").fetchone()[0] == 1

    def is_locked_by(self, ip, user) -> bool:
        db_result = self.db.execute(f"SELECT last_used_by "
                                    f"FROM {self.IP_VERSION} "
                                    f"WHERE ip = '{ip}' AND free = 0").fetchone()
        if db_result:
            return db_result[0] == user
        return False

    def lock_ip_address(self, ip, user, used_for) -> bool:
        self.db = sqlite3.connect(self.DB_PATH)
        if self.is_free(ip):
            self.db.execute(f"UPDATE {self.IP_VERSION} "
                            f"SET free = 0, last_used_by = '{user}', last_used_at = datetime('now'), "
                            f"last_used_for = '{used_for}' "
                            f"WHERE ip = '{ip}'")
            self.db.commit()
            return True
        return False

    def lock_any_ip_address(self, user, used_for):
        self.db = sqlite3.connect(self.DB_PATH)
        # Prio 1: Free IP address that was used by the same user for the same purpose
        db_result = self.db.execute(f"SELECT ip "
                                    f"FROM {self.IP_VERSION} "
                                    f"WHERE free = 1 "
                                    f"AND last_used_by = '{user}'"
                                    f"AND last_used_for = '{used_for}' "
                                    f"ORDER BY last_used_at DESC").fetchone()
        if db_result:
            ip = db_result[0]
            if self.lock_ip_address(ip, user, used_for):
                return ip

        # Prio 2: Free IP address that was used by the same user for a different purpose
        db_result = self.db.execute(f"SELECT ip "
                                    f"FROM {self.IP_VERSION} "
                                    f"WHERE free = 1 "
                                    f"AND last_used_by = '{user}'"
                                    f"ORDER BY last_used_at DESC").fetchone()
        if db_result:
            ip = db_result[0]
            if self.lock_ip_address(ip, user, used_for):
                return ip

        # Prio 3: Free IP address that wasn't used recently
        db_result = self.db.execute(f"SELECT ip "
                                    f"FROM {self.IP_VERSION} "
                                    f"WHERE free = 1 "
                                    f"ORDER BY last_used_at ASC").fetchone()
        if db_result:
            ip = db_result[0]
            if self.lock_ip_address(ip, user, used_for):
                return ip

        return False

    def free_ip_address(self, ip, user) -> bool:
        self.db = sqlite3.connect(self.DB_PATH)
        if self.is_locked_by(ip, user):
            self.db.execute(f"UPDATE {self.IP_VERSION} "
                            f"SET free = 1 "
                            f"WHERE ip = '{ip}' AND last_used_by = '{user}'")
            self.db.commit()
            return True
        return False

    def free_any_ip_address(self, user, used_for):
        self.db = sqlite3.connect(self.DB_PATH)
        db_result = self.db.execute(f"SELECT ip "
                                    f"FROM {self.IP_VERSION} "
                                    f"WHERE free = 0 "
                                    f"AND last_used_by = '{user}'"
                                    f"AND last_used_for = '{used_for}' "
                                    f"ORDER BY last_used_at DESC").fetchone()
        if db_result:
            ip = db_result[0]
            if self.free_ip_address(ip, user):
                return ip
        return False

    def add_ip(self, ip) -> bool:
        self.db = sqlite3.connect(self.DB_PATH)
        if ip not in self.get_all_ips():
            self.db.execute(f"INSERT INTO {self.IP_VERSION} "
                            f"VALUES ('{ip}', 1, '-', '-', '-')")
            self.db.commit()
            return True
        return False

    def delete_ip(self, ip):
        self.db = sqlite3.connect(self.DB_PATH)
        if not self.is_free(ip):
            return False

        self.db.execute(f"DELETE FROM {self.IP_VERSION} "
                        f"WHERE ip = '{ip}'")
        self.db.commit()
        return True


class IPv4Provider(IPProvider):
    def __init__(self, ip_gateway: str):
        super().__init__(ip_gateway, "ipv4")


class IPv6Provider(IPProvider):
    def __init__(self, ip_gateway: str = ""):
        super().__init__(ip_gateway, "ipv6")
