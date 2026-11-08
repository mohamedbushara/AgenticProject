from datetime import datetime
from database import Base
from sqlalchemy import Column, DateTime, Float, Integer, String, Text


class AuditLog(Base):
  __tablename__ = "audit_logs"

  id = Column(
      Integer,
      primary_key=True,
      index=True,
      autoincrement=True,
      comment="المعرف الفريد لسجل التدقيق",
  )
  session_id = Column(
      String(100), index=True, nullable=False, comment="معرف جلسة الوكيل (Agent)"
  )
  username = Column(
      String(100),
      nullable=True,
      comment="المستخدم الذي قام بعملية التدقيق (إن وجد)",
  )
  invoice_filename = Column(
      String(255), nullable=True, comment="اسم ملف الفاتورة التجارية"
  )
  bill_filename = Column(
      String(255), nullable=True, comment="اسم ملف بوليصة الشحن"
  )
  cert_filename = Column(
      String(255), nullable=True, comment="اسم ملف شهادة المنشأ"
  )
  detected_hs_code = Column(
      String(50), nullable=True, comment="الكود الجمركي المستخرج"
  )
  verification_result = Column(
      String(50),
      nullable=False,
      comment="نتيجة التدقيق (PASSED, FAILED, REVIEW_REQUIRED)",
  )
  risk_score = Column(
      String(50),
      nullable=False,
      comment="تقييم المخاطر (LOW, MEDIUM, HIGH, CRITICAL)",
  )
  audit_report_json = Column(
      Text, nullable=True, comment="تقرير التدقيق الكامل بصيغة JSON"
  )
  created_at = Column(
      DateTime,
      default=datetime.utcnow,
      comment="وقت وتاريخ إجراء عملية التدقيق",
  )