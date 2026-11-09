from datetime import datetime
from database import Base
from sqlalchemy import Boolean, Column, Float, String, Text, DateTime


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


class InspectionLog(Base):
    __tablename__ = "inspection_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) if 'Integer' in globals() else Column(String(50), primary_key=True)
    transaction_id = Column(String(50), unique=True, index=True, comment="رقم المعاملة الفريد")
    inspection_date = Column(DateTime, default=datetime.utcnow, comment="تاريخ ووقت الفحص")
    importer_name = Column(String(200), comment="اسم المستورد أو الجهة")
    item_name = Column(String(200), comment="اسم السلعة المفحوصة")
    hs_code = Column(String(50), comment="البند الجمركي المستخرج")
    risk_score = Column(Float, default=0.0, comment="نسبة تقييم المخاطر")
    risk_level = Column(String(20), comment="مستوى المخاطرة LOW, MEDIUM, HIGH")
    status = Column(String(30), comment="حالة الفحص PASSED, HIGH_RISK, REVIEW_REQUIRED")
    status_text = Column(String(50), comment="وصف الحالة باللغة العربية")
    ai_summary = Column(Text, comment="تقرير وملخص الذكاء الاصطناعي")
    documents_list = Column(Text, comment="قائمة المستندات المفحوصة بصيغة JSON")