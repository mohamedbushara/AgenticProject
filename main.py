from datetime import datetime
import os
from agent.core_agent import CustomsComplianceAgent
from database import SessionLocal, engine, get_db
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models.customs import CustomsRule
from models.user import Base as UserBase, User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

UserBase.metadata.create_all(bind=engine)

app = FastAPI(title="Spellbook AI Document Auditor & Sudan Customs Compliance")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def init_customs_database_seed():
  try:
    local_db = SessionLocal()
    if local_db.query(CustomsRule).count() == 0:
      rules_data = [
          {
              "hs_code": "8471.30",
              "item_name": "أجهزة حاسوب محمولة (Laptops)",
              "status": "ALLOWED",
              "allowed_currencies": "USD,EUR,AED",
              "max_allowed_weight": 500.0,
              "required_permits": "لا يتطلب",
              "legislative_reference": "قانون الجمارك السودانية - البند الموحد",
              "notes": "مسموح وفقاً للضوابط المعيارية والاستيراد المؤسسي.",
          },
          {
              "hs_code": "8517.12",
              "item_name": "هواتف ذكية وأجهزة الاتصال الخلوي",
              "status": "PERMIT_REQUIRED",
              "allowed_currencies": "USD,EUR,AED,SAR",
              "max_allowed_weight": 200.0,
              "required_permits": "تصريح الجهاز القومي لتنظيم الاتصالات (NTC)",
              "legislative_reference": "قوانين تنظيم الاتصالات والاستيراد التقني",
              "notes": "يتطلب موافقة الجهاز القومي لتنظيم الاتصالات (NTC).",
          },
          {
              "hs_code": "9999.01",
              "item_name": "المواد المخدرة والمؤثرات العقلية غير المرخصة",
              "status": "PROHIBITED",
              "allowed_currencies": "",
              "max_allowed_weight": 0.0,
              "required_permits": "محظور كلياً",
              "legislative_reference": "قانون مكافحة المخدرات والجمارك السودانية",
              "notes": "حظر تام بموجب قانون مكافحة المخدرات والجمارك السودانية.",
          },
          {
              "hs_code": "3004.90",
              "item_name": "أدوية بشرية جاهزة للاستخدام العلاجي",
              "status": "PERMIT_REQUIRED",
              "allowed_currencies": "USD,EUR",
              "max_allowed_weight": 2000.0,
              "required_permits": "المجلس القومي للأدوية والسموم",
              "legislative_reference": "قانون الأدوية والسموم السوداني",
              "notes": (
                  "يتطلب شهادة تحليل وموافقة إجبارية من المجلس القومي للأدوية"
                  " والسموم."
              ),
          },
      ]

      categories = [
          ("28", "مستحضرات كيماوية ومركبات غير أضوية"),
          ("39", "لدائن وبلاستيك ومصنوعاتها"),
          ("48", "ورق ومصنوعات عجائن الورق والكرتون"),
          ("72", "حديد وصلب ومصنوعات الإنشاءات المعدنية"),
          ("87", "سيارات وجرارات ووسائل نقل وبضائع"),
      ]

      for prefix, cat_name in categories:
        for i in range(1, 21):
          code = f"{prefix}{i:02d}.{i*10:02d}"
          rules_data.append({
              "hs_code": code,
              "item_name": f"صنف تجاري واستيرادي ({cat_name}) رقم {i}",
              "status": "ALLOWED",
              "allowed_currencies": "USD,EUR,AED,SAR",
              "max_allowed_weight": float(i * 350),
              "required_permits": "مواصفات قياسية اعتيادية",
              "legislative_reference": f"قانون التعرفة الجمركية - بند {cat_name}",
              "notes": (
                  f"مادة خاضعة للرسوم الجمركية والضريبية الاعتيادية تحت بند"
                  f" {cat_name}."
              ),
          })

      db_objects = [CustomsRule(**item) for item in rules_data]
      local_db.add_all(db_objects)
      local_db.commit()
      print(
          f"✅ تم بنجاح إنشاء وتعبئة {len(db_objects)} سجلاً جمركياً واقعياً في"
          " جدول SQL Server!"
      )
    local_db.close()
  except Exception as e:
    print(f"⚠️ تنبيه أثناء التعبئة التلقائية للاتصال بقاعدة البيانات: {e}")


init_customs_database_seed()


def get_greeting():
  hour = datetime.now().hour
  if 4 <= hour < 12:
    return "صباح الخير"
  elif 12 <= hour < 18:
    return "نهارك سعيد"
  else:
    return "مساء الخير"


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request, user_session: str = Cookie(None)):
  is_logged_in = bool(user_session)
  return templates.TemplateResponse(
      request,
      "home/index.html",
      {
          "is_logged_in": is_logged_in,
          "username": user_session if is_logged_in else "",
          "greeting": get_greeting() if is_logged_in else "",
      },
  )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, username: str = ""):
  return templates.TemplateResponse(
      request, "auth/login.html", {"username": username, "error_message": None}
  )


@app.post("/login", response_class=HTMLResponse)
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
  clean_username = username.strip()
  clean_password = password.strip()
  user = (
      db.query(User)
      .filter(
          (User.username == clean_username) | (User.email == clean_username)
      )
      .first()
  )
  if not user or user.password != clean_password:
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "username": clean_username,
            "error_message": "اسم المستخدم / البريد أو كلمة المرور غير صحيحة!",
        },
    )
  response = RedirectResponse(url="/", status_code=303)
  response.set_cookie(key="user_session", value=user.username, httponly=True)
  return response


@app.post("/logout")
async def handle_logout():
  response = RedirectResponse(url="/login", status_code=303)
  response.delete_cookie(key="user_session")
  return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
  return templates.TemplateResponse(
      request, "auth/register.html", {"error_message": None}
  )


@app.post("/register", response_class=HTMLResponse)
async def handle_register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
  clean_username = username.strip()
  clean_email = email.strip()
  if password != confirm_password:
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {"error_message": "كلمتا المرور غير متطابقتين!"},
    )
  try:
    if db.query(User).filter(User.username == clean_username).first():
      return templates.TemplateResponse(
          request,
          "auth/register.html",
          {
              "error_message": (
                  "اسم المستخدم هذا مسجل مسبقاً، يرجى اختيار اسم آخر."
              )
          },
      )
    if db.query(User).filter(User.email == clean_email).first():
      return templates.TemplateResponse(
          request,
          "auth/register.html",
          {"error_message": "البريد الإلكتروني هذا مستخدم لحساب آخر مسبقاً."},
      )
    new_user = User(
        username=clean_username,
        email=clean_email,
        phone=phone.strip() if phone else None,
        password=password,
    )
    db.add(new_user)
    db.commit()
  except Exception as e:
    db.rollback()
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {"error_message": f"حدث خطأ في النظام: {str(e)}"},
    )
  return RedirectResponse(
      url=f"/login?username={clean_username}", status_code=303
  )


@app.get("/hs-code", response_class=HTMLResponse)
async def hs_code_page(request: Request, user_session: str = Cookie(None)):
  if not user_session:
    return RedirectResponse(url="/login", status_code=303)
  return templates.TemplateResponse(
      request,
      "home/hs_code.html",
      {"is_logged_in": True, "username": user_session, "greeting": get_greeting()},
  )


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, user_session: str = Cookie(None)):
  if not user_session:
    return RedirectResponse(url="/login", status_code=303)
  return templates.TemplateResponse(
      request,
      "home/history.html",
      {"is_logged_in": True, "username": user_session, "greeting": get_greeting()},
  )


@app.post("/api/scan-document")
async def scan_customs_documents(files: list[UploadFile] = File(...)):
  try:
    if not files or len(files) == 0:
      raise HTTPException(
          status_code=400, detail="لم يتم إرفاق أي مستندات للفحص."
      )

    upload_dir = "uploads_temp"
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    for file in files:
      file_path = os.path.join(upload_dir, file.filename)
      with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
      saved_paths.append(file_path)

    inv_path = saved_paths[0] if len(saved_paths) > 0 else "dummy_inv.pdf"
    bol_path = saved_paths[1] if len(saved_paths) > 1 else "dummy_bol.pdf"
    cert_path = saved_paths[2] if len(saved_paths) > 2 else "dummy_cert.pdf"

    session_id = f"SESSION-{os.urandom(4).hex().upper()}"
    agent = CustomsComplianceAgent(session_id=session_id)
    audit_report = agent.run_audit(
        invoice_path=inv_path,
        bill_of_lading_path=bol_path,
        cert_of_origin_path=cert_path,
    )

    for p in saved_paths:
      if os.path.exists(p):
        os.remove(p)

    if audit_report.get("status") == "INVALID_DOCUMENT":
      return {
          "status": "error",
          "message": audit_report.get("error_message"),
      }

    return {
        "status": "success",
        "message": "تم الفحص والتدقيق الجمركي بنجاح.",
        "report": audit_report,
    }

  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"حدث خطأ أثناء تشغيل الوكيل: {str(e)}"
    )

from models.customs import CustomsRule

# 1. API لجلب جميع البنود الجمركية من جدول customs_rules في قاعدة البيانات
@app.get("/api/customs-rules")
def get_customs_rules(db: Session = Depends(get_db)):
    try:
        rules = db.query(CustomsRule).all()
        result = []
        for r in rules:
            result.append({
                "hs_code": r.hs_code,
                "item_name": r.item_name,
                "status": r.status,
                "allowed_currencies": r.allowed_currencies,
                "max_allowed_weight": r.max_allowed_weight,
                "required_permits": r.required_permits,
                "legislative_reference": r.legislative_reference,
                "notes": r.notes
            })
        print(f"-> [DB INDEX] Fetched {len(result)} records from customs_rules.")
        return {"status": "success", "data": result}
    except Exception as e:
        print(f"-> [DB INDEX ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 2. API لإضافة بند جديد ومباشر إلى جدول customs_rules وحفظه في الـ SQL Server
@app.post("/api/customs-rules")
def create_customs_rule(rule_data: dict, db: Session = Depends(get_db)):
    try:
        hs_code_val = rule_data.get("hs_code")
        
        # التحقق مما إذا كان الكود موجوداً مسبقاً لتفادي تضارب المفتاح الأساسي (Primary Key)
        existing = db.query(CustomsRule).filter(CustomsRule.hs_code == hs_code_val).first()
        if existing:
            raise HTTPException(status_code=400, detail="الكود الجمركي (HS Code) موجود مسبقاً في القاعدة.")

        new_rule = CustomsRule(
            hs_code=hs_code_val,
            item_name=rule_data.get("item_name"),
            status=rule_data.get("status", "ALLOWED"),
            allowed_currencies=rule_data.get("allowed_currencies", "USD,EUR"),
            max_allowed_weight=float(rule_data.get("max_allowed_weight", 1000.0)),
            required_permits=rule_data.get("required_permits", "لا يتطلب"),
            legislative_reference=rule_data.get("legislative_reference", "إضافة مباشرة عبر شاشة الإندكس"),
            notes=rule_data.get("notes", "بند جديد تم إضافته للقاعدة")
        )
        db.add(new_rule)
        db.commit()
        print(f"-> [DB INSERT] Successfully added new rule: {hs_code_val}")
        return {"status": "success", "message": "تمت إضافة البند بنجاح وحفظه في قاعدة البيانات"}
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        print(f"-> [DB INSERT ERROR]: {e}")
        raise HTTPException(status_code=400, detail=f"خطأ في حفظ البيانات: {str(e)}")
    
# أضف هذا الـ API في ملف main.py الخاص بك
@app.delete("/api/customs-rules/{hs_code}")
def delete_customs_rule(hs_code: str, db: Session = Depends(get_db)):
    try:
        rule = db.query(CustomsRule).filter(CustomsRule.hs_code == hs_code).first()
        if not rule:
            raise HTTPException(status_code=404, detail="البند غير موجود في القاعدة.")
        
        db.delete(rule)
        db.commit()
        print(f"-> [DB DELETE] Successfully deleted rule: {hs_code}")
        return {"status": "success", "message": "تم حذف البند بنجاح من قاعدة البيانات"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"خطأ أثناء الحذف: {str(e)}")

if __name__ == "__main__":
  import uvicorn

  uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)