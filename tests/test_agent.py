from agent.core_agent import CustomsComplianceAgent
from agent.tools import CustomsAgentTools


def test_document_parser_tool_valid():
  res = CustomsAgentTools.document_parser_tool(
      "dummy_inv.pdf", "dummy_bol.pdf", "dummy_cert.pdf"
  )
  assert res["status"] == "success"
  assert "hs_code" in res


def test_customs_playbook_retriever_valid():
  # الكود التجريبي الذي يدخل في قاعدة البيانات
  res = CustomsAgentTools.customs_playbook_retriever("8471.30")
  assert res["hs_code"] == "8471.30"
  # التأكد من وجود حقل الحالة القانونية الجديد بدل is_banned
  assert "status" in res


def test_customs_playbook_retriever_banned():
  # اختبار كود غير موجود (يجب أن يعود بـ UNKNOWN ولا يسبب خطأ) أو كود محظور
  res = CustomsAgentTools.customs_playbook_retriever("9999.01")
  assert res["status"] in ["PROHIBITED", "UNKNOWN"]


def test_cross_verification_tool_passed():
  extracted = {"invoice": {"currency": "USD", "amount": 1000}}
  rules = {"status": "ALLOWED", "allowed_currencies": ["USD", "EUR"]}
  res = CustomsAgentTools.cross_verification_tool(extracted, rules)
  assert res["verification_status"] == "PASSED"


def test_agent_full_run_offline():
  agent = CustomsComplianceAgent(session_id="TEST-SESSION-001")
  report = agent.run_audit("inv.pdf", "bol.pdf", "cert.pdf")
  assert report["session_id"] == "TEST-SESSION-001"
  assert "verification_result" in report
  assert "trace_log" in report