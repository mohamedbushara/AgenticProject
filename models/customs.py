from database import Base
from sqlalchemy import Boolean, Column, Float, String, Text


class CustomsRule(Base):
  __tablename__ = "customs_rules"

  hs_code = Column(
      String(50), primary_key=True, index=True, comment="الكود الجمركي للصنف"
  )
  item_name = Column(
      String(200), nullable=False, comment="اسم الصنف أو الوصف التجاري"
  )
  status = Column(
      String(50),
      default="ALLOWED",
      comment=(
          "الحالة القانونية: ALLOWED, PROHIBITED, RESTRICTED,"
          " PERMIT_REQUIRED, UNKNOWN"
      ),
  )
  allowed_currencies = Column(
      String(100), default="USD,EUR", comment="العملات المسموح بالتعامل بها"
  )
  max_allowed_weight = Column(
      Float, nullable=True, comment="الوزن الأقصى المسموح استيراده إن وجد"
  )
  required_permits = Column(
      String(255),
      nullable=True,
      comment="الجهة المختصة أو التصريح المطلوب (إن وجد)",
  )
  legislative_reference = Column(
      String(255),
      nullable=True,
      comment="المرجع القانوني أو رقم القرار الوزاري أو المنشور",
  )
  notes = Column(Text, nullable=True, comment="ملاحظات تشريعية وإضافية")