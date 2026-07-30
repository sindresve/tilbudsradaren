from collections import defaultdict
from db.database import get_connection
from api.utils.utils import current_year_week
from api.utils.notifications import notify_matching_products, send_discord_message, send_email, send_deals_email

def notifications_enabled(conn):
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

    cursor.execute("SELECT discord_webhook_url, smtp_host, smtp_port, smtp_username, smtp_password, email_to FROM settings WHERE id = 1")
    row = cursor.fetchone()
    webhook = row["discord_webhook_url"] if row else None
    smtp_settings = {"host": row["smtp_host"], "port": row["smtp_port"], "username": row["smtp_username"], "password": row["smtp_password"], "email_to": row["email_to"]}

    return watch_list, webhook, smtp_settings

class ProductMonitor:
    def __init__(self):
        self.conn = None
        self.product_list = []
        self.products_by_keyword = defaultdict(list)
        self.year, self.week = current_year_week()

        try:
            self.conn = get_connection()
            self.enabled = notifications_enabled(self.conn)
            self.watch_list, self.webhook, self.smtp_settings = get_scan_settings(self.conn)

            if not self.enabled["smtp"] and not self.enabled["webhook"]:
                self.conn.close()
                raise RuntimeError("Notifications are not enabled")
            if not self.webhook and self.enabled["webhook"]:
                self.conn.close()
                raise RuntimeError("User has not set a webhook")
            if not self.smtp_settings and self.enabled["smtp"]:
                self.conn.close()
                raise RuntimeError("User has not set smtp settings")
            if not self.watch_list:
                self.conn.close()
                raise RuntimeError("User has not made a watch list")
            
        except Exception:
            if self.conn:
                self.conn.close()
            raise


    def run(self):
        print("Starting product monitor...")

        self.check_keywords()
        self.conn.close()
        
        print("Product monitor finished!")

    def find_products(self, keyword: str):
        """Retrieves discounted product id/name pairs for this week's catalog, based on keyword"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT DISTINCT p.id, p.product_name, p.category, p.current_price, p.old_price, p.discount_percent
            FROM product_search_terms st
            JOIN products p ON p.id = st.product_id
            JOIN catalogs c ON c.id = p.catalog_id
            WHERE st.term = ?
            AND c.year = ?
            AND c.week = ?
            AND (
                (p.current_price IS NOT NULL AND p.old_price IS NOT NULL AND p.old_price > 0 AND p.current_price < p.old_price)
                OR (p.discount_percent IS NOT NULL AND p.discount_percent > 0)
            )
        """, (keyword.lower(), self.year, self.week))

        return [{"id": row["id"], "name": row["product_name"], "category": row["category"], "current_price": row["current_price"], "old_price": row["old_price"], "discount_percent": row["discount_percent"], "keyword": keyword} for row in cursor.fetchall()]

    def check_keywords(self):
        seen_ids = set()
        for keyword in self.watch_list:
            products = self.find_products(keyword)
            for product in products:
                if product["id"] not in seen_ids:
                    seen_ids.add(product["id"])
                    self.product_list.append(product)
                    self.products_by_keyword[product["keyword"]].append(product)

        if len(self.product_list) > 0:
            print(f"Found {len(self.product_list)} product(s)!")
            print("Sending notfications now...")
            self.send_notifications()
        else:
            print("No products found...")
            send_discord_message("Ingen produkter funnet denne uken. 🔍", self.webhook)
            send_email("Ingen produkter funnet denne uken. 🔍", f"Rapport for uke {self.week}", self.smtp_settings)

    def send_notifications(self):
        if self.enabled['smtp']:
            send_deals_email(self.products_by_keyword, self.smtp_settings)
            print("Email notification sent!")
        if self.enabled['webhook']:
            webhook_notifications = 0
            for keyword, products in self.products_by_keyword.items():
                webhook_notifications = webhook_notifications + 1
                notify_matching_products(products, keyword, self.webhook)
            print(f"Webhook notification{'s' if webhook_notifications > 1 else ''} sent!")