import os
import sys

# إضافة المسار الجذري للمشروع بشكل دقيق ليتعرف بايثون على مجلد agent
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from agent.core_agent import CustomsComplianceAgent
from agent.tools import CustomsAgentTools


def test_document_parser_tool_valid():
  """اختبار أداة محلل المستندات عند توفر الملفات الثلاثة"""
  result = CustomsAgentTools.document_parser_tool(
      invoice_path="dummy_inv.pdf",
      bill_of_lading_path="dummy_bol.pdf",
      cert_of_origin_path="dummy_coo.pdf",
  )
  assert result["status"] == "success"
  assert "invoice" in result
  assert "bill_of_lading" in result
  assert "certificate_of_origin" in result
  assert result["hs_code"] == "8471.30"


def test_customs_playbook_retriever_valid():
  """اختبار أداة جلب القواعد الجمركية بناءً على الكود"""
  rules = CustomsAgentTools.customs_playbook_retriever("8471.30")
  assert rules["is_banned"] is False
  assert "USD" in rules["allowed_currencies"]


def test_customs_playbook_retriever_banned():
  """اختبار جلب قواعد صنف محظور كلياً"""
  rules = CustomsAgentTools.customs_playbook_retriever("9999.99")
  assert rules["is_banned"] is True


def test_cross_verification_tool_passed():
  """اختبار أداة المطابقة والتحقق (حالة النجاح)"""
  extracted = {
      "invoice": {"currency": "USD"},
      "certificate_of_origin": {"country_of_origin": "China"},
  }
  rules = {"is_banned": False, "allowed_currencies": ["USD"]}
  verification = CustomsAgentTools.cross_verification_tool(extracted, rules)
  assert verification["verification_status"] == "PASSED"
  assert verification["calculated_risk_score"] == "LOW"


def test_agent_full_run_offline():
  """اختبار دورة الوكيل الكاملة محلياً (بدون إنترنت وبدون مفاتيح API)"""
  agent = CustomsComplianceAgent(session_id="TEST-SESSION-001")
  state = agent.run_audit(
      invoice_path="dummy_inv.pdf",
      bill_of_lading_path="dummy_bol.pdf",
      cert_of_origin_path="dummy_coo.pdf",
  )

  # التأكد من أن الوكيل قام بالتشغيل ومرّ عبر الدورات وسجل الـ Trace Log
  assert state["session_id"] == "TEST-SESSION-001"
  assert len(state["trace_log"]) > 0
  assert state["risk_score"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]