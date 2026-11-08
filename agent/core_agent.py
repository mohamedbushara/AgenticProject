from agent.tools import CustomsAgentTools


class CustomsComplianceAgent:

  def __init__(self, session_id: str):
    self.session_id = session_id
    self.iteration_count = 0
    self.max_iterations = 3  # شرط الأمان الحرم للحد من الحلقات اللانهائية
    self.trace_log = []

  def run_audit(
      self, invoice_path: str, bill_of_lading_path: str, cert_of_origin_path: str
  ) -> dict:
    """تشغيل دورة الوكيل الكاملة لفحص المستندات الجمركية الثلاثة"""
    state = {
        "session_id": self.session_id,
        "iteration_count": 0,
        "raw_documents": {
            "invoice": invoice_path,
            "bill_of_lading": bill_of_lading_path,
            "certificate_of_origin": cert_of_origin_path,
        },
        "extracted_data": {},
        "playbook_rules": {},
        "validation_findings": [],
        "risk_score": "LOW",
        "human_approval_status": "PENDING",
        "trace_log": [],
    }

    while self.iteration_count < self.max_iterations:
      self.iteration_count += 1
      state["iteration_count"] = self.iteration_count

      # 1. SENSE: استخراج وتحليل بيانات المستندات الثلاثة
      extracted = CustomsAgentTools.document_parser_tool(
          invoice_path, bill_of_lading_path, cert_of_origin_path
      )
      state["extracted_data"] = extracted
      self.trace_log = CustomsAgentTools.audit_trail_logger(
          "SENSE",
          f"تم تحليل المستندات الثلاثة بنجاح في الدورة رقم {self.iteration_count}",
          self.trace_log,
      )

      if extracted.get("status") == "error":
        state["risk_score"] = "CRITICAL"
        state["validation_findings"] = [extracted.get("message")]
        break

      # 2. REASON: جلب القواعد الجمركية بناءً على الكود الجمركي (HS Code) المستخرج
      hs_code = extracted.get("hs_code", "8471.30")
      rules = CustomsAgentTools.customs_playbook_retriever(hs_code)
      state["playbook_rules"] = rules
      self.trace_log = CustomsAgentTools.audit_trail_logger(
          "REASON",
          f"تم جلب قواعد الدليل الجمركي (Playbook) للتصنيف {hs_code}",
          self.trace_log,
      )

      # 3. ACT: تنفيذ المطابقة والتحقق الحتمي بين البيانات والقواعد
      verification = CustomsAgentTools.cross_verification_tool(extracted, rules)
      state["validation_findings"] = verification.get("discrepancies", [])
      state["risk_score"] = verification.get("calculated_risk_score", "LOW")
      self.trace_log = CustomsAgentTools.audit_trail_logger(
          "ACT",
          (
              "تم تنفيذ التحقق والمطابقة. النتيجة:"
              f" {verification.get('verification_status')}"
          ),
          self.trace_log,
      )

      # 4. OBSERVE & STOPPING CONDITIONS (شروط الإيقاف)
      status = verification.get("verification_status")
      if status == "CRITICAL_VIOLATION" or status == "PASSED":
        # شرط الإيقاف 1 أو 2: نجاح الفحص أو اكتشاف انتهاك خطير يتطلب تصعيد فوري
        break
      elif self.iteration_count >= self.max_iterations:
        # شرط الإيقاف 3: بلوغ الحد الأقصى للتكرار (Safety Cap = 3)
        self.trace_log = CustomsAgentTools.audit_trail_logger(
            "OBSERVE",
            "تم الوصول إلى الحد الأقصى للتكرار (Max Iterations = 3)، إيقاف الوكيل.",
            self.trace_log,
        )
        break

    state["trace_log"] = self.trace_log
    return state