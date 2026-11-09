from agent.tools import CustomsAgentTools
from datetime import datetime, timezone


class CustomsComplianceAgent:

  def __init__(self, session_id: str):
    self.session_id = session_id
    self.trace_log = []

  def log_step(self, phase: str, description: str, data: dict = None):
    step_info = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "description": description,
        "data": data or {},
    }
    self.trace_log.append(step_info)

  def run_audit(
      self, invoice_path: str, bill_of_lading_path: str, cert_of_origin_path: str
  ) -> dict:
    """تشغيل دورة التدقيق الجمركي الكاملة للوكيل الذكي"""
    self.trace_log = []

    try:
      # 1. مرحلة الاستشعار والتحليل (SENSE & PARSE)
      self.log_step(
          "SENSE",
          "بدء استقراء وقراءة المستندات الجمركية المرفوعة عبر أداة التحليل.",
      )
      parsed_data = CustomsAgentTools.document_parser_tool(
          invoice_path, bill_of_lading_path, cert_of_origin_path
      )

      # إذا فشل التحقق الذكي للمستندات
      if parsed_data.get("status") == "INVALID_DOCUMENT":
        self.log_step(
            "SENSE_FAILED",
            "تم رفض المستندات لعدم مطابقتها لمتطلبات التخليص الجمركي.",
            parsed_data,
        )
        return {
            "session_id": self.session_id,
            "status": "INVALID_DOCUMENT",
            "error_message": parsed_data.get("error_message"),
            "trace_log": self.trace_log,
        }

      extracted_hs = parsed_data.get("hs_code")
      self.log_step(
          "SENSE_COMPLETE",
          f"تم استخراج الكود الجمركي بنجاح: {extracted_hs}",
          parsed_data,
      )

      # 2. مرحلة الاستعلام عن القواعد التشريعية (REASON & RETRIEVE)
      self.log_step(
          "REASON",
          f"استعلام قاعدة بيانات SQL Server للتحقق من تشريعات الكود: {extracted_hs}",
      )
      playbook_rules = CustomsAgentTools.customs_playbook_retriever(
          extracted_hs
      )
      self.log_step(
          "REASON_COMPLETE",
          (
              "تم جلب القاعدة الجمركية وحالة الصنف:"
              f" {playbook_rules.get('status')}"
          ),
          playbook_rules,
      )

      # 3. مرحلة المطابقة والتحقق المتقاطع (ACT & VERIFY)
      self.log_step(
          "ACT", "تنفيذ المطابقة والتحقق المتقاطع بين المستندات وقواعد التشريع."
      )
      verification_result = CustomsAgentTools.cross_verification_tool(
          parsed_data, playbook_rules
      )
      self.log_step(
          "ACT_COMPLETE",
          (
              "نتائج الفحص والتحقق المتقاطع:"
              f" {verification_result.get('verification_status')}"
          ),
          verification_result,
      )

      # 4. التقرير النهائي (OBSERVE & REPORT)
      self.log_step(
          "OBSERVE", "إعداد وتجميع تقرير التدقيق الجمركي النهائي للعميل."
      )

      final_report = {
          "session_id": self.session_id,
          "timestamp": datetime.now(timezone.utc).isoformat(),
          "status": "success",
          "extracted_data": parsed_data,
          "playbook_rules": playbook_rules,
          "verification_result": verification_result,
          "trace_log": self.trace_log,
          "disclaimer": (
              "ملاحظة قانونية: هذا التقرير صادر عن نظام ذكاء اصطناعي لأغراض"
              " التدقيق الاستباقي، ولا يعد موافقة رسمية نهائية للتخليص"
              " الجمركي."
          ),
      }

      return final_report

    except Exception as e:
      self.log_step("ERROR", f"حدث خطأ استثنائي أثناء دورة التدقيق: {str(e)}")
      return {
          "session_id": self.session_id,
          "status": "ERROR",
          "error_message": str(e),
          "trace_log": self.trace_log,
      }