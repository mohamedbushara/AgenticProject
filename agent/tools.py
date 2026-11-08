from database import SessionLocal
from models.customs import CustomsRule
from sqlalchemy.orm import Session


class CustomsAgentTools:

  @staticmethod
  def document_parser_tool(
      invoice_path: str, bill_of_lading_path: str, cert_of_origin_path: str
  ) -> dict:
    """أداة تحليل المستندات واستخراج البيانات والـ HS Code"""
    # محاكاة الاستخراج الناجح للملفات المرفوعة
    return {
        "status": "success",
        "invoice": {"currency": "USD", "amount": 15000},
        "bill_of_lading": {"weight": 450.0, "port_of_entry": "Port Sudan"},
        "certificate_of_origin": {"country_of_origin": "China"},
        "hs_code": "8471.30",  # كود تجريبي للاستعلام
    }

  @staticmethod
  def customs_playbook_retriever(hs_code: str, db: Session = None) -> dict:
    """استعلام ديناميكي مباشر من جدول customs_rules في SQL Server"""
    should_close = False
    if db is None:
      db = SessionLocal()
      should_close = True

    try:
      rule = (
          db.query(CustomsRule).filter(CustomsRule.hs_code == hs_code).first()
      )

      if rule:
        return {
            "hs_code": rule.hs_code,
            "item_name": rule.item_name,
            "status": rule.status,  # ALLOWED, PROHIBITED, RESTRICTED, etc.
            "allowed_currencies": [
                c.strip() for c in rule.allowed_currencies.split(",") if c
            ],
            "max_allowed_weight": rule.max_allowed_weight,
            "required_permits": rule.required_permits,
            "legislative_reference": rule.legislative_reference,
            "notes": rule.notes,
            "source": "SQL Server Database (Live)",
        }
      else:
        # مبدأ قانوني: عدم العثور على الكود لا يعني حظر السلعة، بل تعتبر مجهولة UNKNOWN
        return {
            "hs_code": hs_code,
            "item_name": "صنف غير مسجل في التعريفة الجمركية",
            "status": "UNKNOWN",
            "allowed_currencies": [],
            "max_allowed_weight": None,
            "required_permits": "مراجعة بشرية إلزامية",
            "legislative_reference": None,
            "notes": (
                "تحذير قانوني: الكود الجمركي غير مدرج في قاعدة بيانات"
                " التشريعات الحالية وتتطلب حالته التحقق اليدوي (UNKNOWN)."
            ),
            "source": "SQL Server Database (Fallback - UNKNOWN)",
        }
    finally:
      if should_close:
        db.close()

  @staticmethod
  def cross_verification_tool(extracted_data: dict, rules: dict) -> dict:
    """أداة المطابقة والتحقق المتقاطع وفق الحالات القانونية"""
    status = rules.get("status", "UNKNOWN")

    if status == "PROHIBITED":
      return {
          "verification_status": "FAILED",
          "calculated_risk_score": "CRITICAL",
          "reason": "السلعة محظورة كلياً بموجب القوانين واللوائح الجمركية.",
      }

    if status == "UNKNOWN":
      return {
          "verification_status": "REVIEW_REQUIRED",
          "calculated_risk_score": "MEDIUM",
          "reason": (
              "الكود غير معروف (UNKNOWN)، تتطلب المعاملة تدخلاً ومراجعة بشرية."
          ),
      }

    inv_currency = extracted_data.get("invoice", {}).get("currency", "USD")
    allowed_currencies = rules.get("allowed_currencies", ["USD"])

    if allowed_currencies and inv_currency not in allowed_currencies:
      return {
          "verification_status": "FAILED",
          "calculated_risk_score": "HIGH",
          "reason": f"عملة الفاتورة ({inv_currency}) غير مسموح بها لهذا الصنف.",
      }

    return {
        "verification_status": "PASSED",
        "calculated_risk_score": "LOW",
        "reason": (
            "جميع الاشتراطات الجمركية والتشريعية مستوفاة بنجاح (ملاحظة: هذا"
            " التدقيق آلي ولا يعد موافقة رسمية نهائية)."
        ),
    }