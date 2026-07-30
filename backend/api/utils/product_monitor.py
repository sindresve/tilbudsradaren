from ...db.database import get_connection

class ProductMonitor:
    def __init__(self, keywords: list[str], webhook: str, conn):
        self.watch_list = keywords
        self.product_list = []
        self.webhook_url = webhook
        self.conn = conn

    def run(self):
        self.check_keywords()

    def find_products(self, keyword: str):
        # find products containing the certain keyword and add them to a list
        # then send the list back

        return ["product_1", "product_2"]

    def check_keywords(self):
        for keyword in self.watch_list:
            products = self.find_products(keyword)
            for product in products:
                self.product_list.append(product)
        self.send_notifications()

    def send_notifications(self):
        if self.product_list:
            print("continue")
        else:
            return "No products on watchlist found"

def notfications_enabled(conn):
    """Checks if user has enabled notifications"""
    cursor = conn.cursor()

    cursor.execute("SELECT smtp_enabled, webhook_enabled FROM settings WHERE id = 1")
    row = cursor.fetchone()
    smtp_enabled = row["smtp_enabled"] if row else None
    webhook_enabled = row["webhook_enabled"] if row else None

    return {"smtp": smtp_enabled, "webhook": webhook_enabled}
        
def get_scan_settings(conn):
    """Retrives watch list, webhook and smtp settings"""
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM staples")
    watch_list = [row["name"] for row in cursor.fetchall()]

    cursor.execute("SELECT discord_webhook_url FROM settings WHERE id = 1")
    row = cursor.fetchone()
    webhook = row["discord_webhook_url"] if row else None

    return watch_list, webhook

def main():
    conn = get_connection()
    enabled = notfications_enabled(conn)

    if not enabled["smtp"] and not enabled["webhook"]:
        conn.close()
        return "Notifications are not enabled"
    
    watch_list, webhook = get_scan_settings(conn)

    if not watch_list:
        conn.close()
        return "User has not made a watch list"

    monitor = ProductMonitor(watch_list, webhook, conn)
    monitor.run()

    conn.close()