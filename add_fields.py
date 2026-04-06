import sqlite3
import os

# الاتصال بقاعدة البيانات
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# التحقق من وجود الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_journalentry'")
table_exists = cursor.fetchone()

if not table_exists:
    print("Table journal_journalentry does not exist!")
    conn.close()
    exit()

# الحصول على الأعمدة الحالية
cursor.execute("PRAGMA table_info(journal_journalentry)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Existing columns: {columns}")

# إضافة الأعمدة الجديدة إذا لم تكن موجودة
if 'is_adjustment' not in columns:
    cursor.execute("ALTER TABLE journal_journalentry ADD COLUMN is_adjustment BOOLEAN NOT NULL DEFAULT 0")
    print("✅ Added is_adjustment column")
else:
    print("⚠️ is_adjustment column already exists")

if 'adjustment_type' not in columns:
    cursor.execute("ALTER TABLE journal_journalentry ADD COLUMN adjustment_type VARCHAR(20) NOT NULL DEFAULT 'none'")
    print("✅ Added adjustment_type column")
else:
    print("⚠️ adjustment_type column already exists")

if 'adjustment_reference' not in columns:
    cursor.execute("ALTER TABLE journal_journalentry ADD COLUMN adjustment_reference VARCHAR(100) NOT NULL DEFAULT ''")
    print("✅ Added adjustment_reference column")
else:
    print("⚠️ adjustment_reference column already exists")

if 'adjustment_notes' not in columns:
    cursor.execute("ALTER TABLE journal_journalentry ADD COLUMN adjustment_notes TEXT NOT NULL DEFAULT ''")
    print("✅ Added adjustment_notes column")
else:
    print("⚠️ adjustment_notes column already exists")

# التحقق من الإضافة
cursor.execute("PRAGMA table_info(journal_journalentry)")
new_columns = [col[1] for col in cursor.fetchall()]
print(f"New columns: {new_columns}")

conn.commit()
conn.close()
print("\n✅ All columns added successfully!")