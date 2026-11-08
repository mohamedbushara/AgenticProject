from database import Base, engine
from models.audit import AuditLog
from models.customs import CustomsRule
from seed_customs import seed_database_rules

if __name__ == "__main__":
  print("جاري إنشاء الجداول في قاعدة بيانات SQL Server...")
  # إنشاء الجداول الجديدة (CustomsRule و AuditLog) دون المساس بجدول Users
  Base.metadata.create_all(bind=engine)
  print("✅ تم إنشاء الجداول بنجاح!")

  print("جاري تشغيل تعبئة القواعد الجمركية...")
  seed_database_rules()