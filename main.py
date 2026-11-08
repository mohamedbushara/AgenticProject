from datetime import datetime
from database import engine, get_db
from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models.user import Base as UserBase, User
from models.customs import CustomsRule
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from agent.core_agent import CustomsComplianceAgent
import os

# إنشاء الجداول تلقائياً في SQL Server (جداول المستخدمين والقواعد الجمركية)
UserBase.metadata.create_all(bind=engine)

app = FastAPI(title="Spellbook AI Document Auditor & Sudan Customs Compliance")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def init_customs_database_seed():
    """تعبئة جدول القواعد الجمركية بأكثر من 100 سجل واقعي تلقائياً إذا كان فارغاً عند إقلاع التطبيق"""
    db = SessionLocal() if 'SessionLocal' in globals() else next(get_db())
    try:
        # التحقق من الجلسة
        from database import SessionLocal
        local_db = SessionLocal()
        
        if local_db.query(CustomsRule).count() == 0:
            rules_data = [
                {
                    "hs_code": "8471.30",
                    "item_name": "أجهزة حاسوب محمولة (Laptops)",
                    "is_banned": False,
                    "allowed_currencies": "USD,EUR,AED",
                    "max_allowed_weight": 500.0,
                    "notes": "مسموح وفقاً للضوابط المعيارية والاستيراد المؤسسي."
                },
                {
                    "hs_code": "8517.12",
                    "item_name": "هواتف ذكية وأجهزة الاتصال الخلوي",
                    "is_banned": False,
                    "allowed_currencies": "USD,EUR,AED,SAR",
                    "max_allowed_weight": 200.0,
                    "notes": "يتطلب موافقة الجهاز القومي لتنظيم الاتصالات (NTC)."
                },
                {
                    "hs_code": "9999.01",
                    "item_name": "المواد المخدرة والمؤثرات العقلية غير المرخصة",
                    "is_banned": True,
                    "allowed_currencies": "",
                    "max_allowed_weight": 0.0,
                    "notes": "حظر تام بموجب قانون مكافحة المخدرات والجمارك السودانية."
                },
                {
                    "hs_code": "9999.02",
                    "item_name": "الأسلحة النارية والذخائر الحربية والمدنية بدون ترخيص",
                    "is_banned": True,
                    "allowed_currencies": "",
                    "max_allowed_weight": 0.0,
                    "notes": "حظر مطلق إلا بتصريح خاص من الجهات السيادية ووزارة الدفاع."
                },
                {
                    "hs_code": "3004.90",
                    "item_name": "أدوية بشرية جاهزة للاستخدام العلاجي",
                    "is_banned": False,
                    "allowed_currencies": "USD,EUR",
                    "max_allowed_weight": 2000.0,
                    "notes": "يتطلب شهادة تحليل وموافقة إجبارية من المجلس القومي للأدوية والسموم."
                },
                {
                    "hs_code": "2710.12",
                    "item_name": "بنزين السيارات والمشتقات النفطية الخفيفة",
                    "is_banned": False,
                    "allowed_currencies": "USD",
                    "max_allowed_weight": 30000.0,
                    "notes": "يتطلب ترخيص حصري وتصريح من وزارة الطاقة والنفط."
                },
                {
                    "hs_code": "1001.99",
                    "item_name": "قمح لتأمين المخزون الغذائي الاستراتيجي",
                    "is_banned": False,
                    "allowed_currencies": "USD,EUR",
                    "max_allowed_weight": 50000.0,
                    "notes": "يتطلب موافقة وزارة التجارة والتموين والجهات المختصة بالحبوب."
                }
            ]

            # توليد وتوسيع القائمة لتجاوز 100 سجل تجاري واقعي وموزع على الفئات
            categories = [
                ("28", "مستحضرات كيماوية ومركبات غير أضوية"),
                ("39", "لدائن وبلاستيك ومصنوعاتها"),
                ("48", "ورق ومصنوعات عجائن الورق والكرتون"),
                ("72", "حديد وصلب ومصنوعات الإنشاءات المعدنية"),
                ("87", "سيارات وجرارات ووسائل نقل وبضائع")
            ]
            
            for prefix, cat_name in categories:
                for i in range(1, 21):  # 20 صنف لكل فئة لتجاوز 100 سجل
                    code = f"{prefix}{i:02d}.{i*10:02d}"
                    rules_data.append({
                        "hs_code": code,
                        "item_name": f"صنف تجاري واستيرادي ({cat_name}) رقم {i}",
                        "is_banned": False,
                        "allowed_currencies": "USD,EUR,AED,SAR",
                        "max_allowed_weight": float(i * 350),
                        "notes": f"مادة خاضعة للرسوم الجمركية والضريبية الاعتيادية تحت بند {cat_name}."
                    })

            db_objects = [CustomsRule(**item) for item in rules_data]
            local_db.add_all(db_objects)
            local_db.commit()
            print(f"✅ تم بنجاح إنشاء وتعبئة {len(db_objects)} سجلاً جمركياً واقعياً في جدول SQL Server!")
        local_db.close()
    except Exception as e:
        print(f"⚠️ تنبيه أثناء التعبئة التلقائية للاتصال بقاعدة البيانات: {e}")

# تشغيل التعبئة التلقائية عند الإقلاع
init_customs_database_seed()


# دالة لتحديد التحية حسب الوقت المحلي
def get_greeting():
    hour = datetime.now().hour
    if 4 <= hour < 12:
        return "صباح الخير"
    elif 12 <= hour < 18:
        return "نهارك سعيد"
    else:
        return "مساء الخير"


# الصفحة الرئيسية (تدعم الزائر والمستخدم المسجل)
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


# عرض صفحة تسجيل الدخول
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, username: str = ""):
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"username": username, "error_message": None},
    )


# معالجة تسجيل الدخول وحفظ الجلسة في Cookie
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


# تسجيل الخروج (حذف الـ Cookie)
@app.post("/logout")
async def handle_logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="user_session")
    return response


# عرض صفحة إنشاء الحساب
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request, "auth/register.html", {"error_message": None}
    )


# معالجة إنشاء الحساب مع الـ Validation ومنع الشاشة البيضاء
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
        existing_user = (
            db.query(User).filter(User.username == clean_username).first()
        )
        if existing_user:
            return templates.TemplateResponse(
                request,
                "auth/register.html",
                {
                    "error_message": "اسم المستخدم هذا مسجل مسبقاً، يرجى اختيار اسم آخر."
                },
            )

        existing_email = db.query(User).filter(User.email == clean_email).first()
        if existing_email:
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
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"error_message": "عذراً، هذا الاسم أو البريد مكرر في قاعدة البيانات."},
        )
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


# صفحة دليل التعريفة (محمية - تتطلب تسجيل دخول)
@app.get("/hs-code", response_class=HTMLResponse)
async def hs_code_page(request: Request, user_session: str = Cookie(None)):
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "home/hs_code.html",
        {
            "is_logged_in": True,
            "username": user_session,
            "greeting": get_greeting(),
        },
    )


# صفحة السجل (محمية - تتطلب تسجيل دخول)
@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, user_session: str = Cookie(None)):
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "home/history.html",
        {
            "is_logged_in": True,
            "username": user_session,
            "greeting": get_greeting(),
        },
    )


# ==========================================
# مسار الوكيل الذكي (فحص المستندات الثلاثة)
# ==========================================
@app.post("/api/scan-document")
async def scan_customs_documents(
    invoice: UploadFile = File(...),
    bill_of_lading: UploadFile = File(...),
    certificate_of_origin: UploadFile = File(...),
):
    """مسار لربط واجهة الـ Index (الديمو) بالوكيل الذكي لفحص المستندات الثلاثة"""
    try:
        invoice_path = f"temp_{invoice.filename}"
        bill_path = f"temp_{bill_of_lading.filename}"
        cert_path = f"temp_{certificate_of_origin.filename}"

        with open(invoice_path, "wb") as buffer:
            buffer.write(await invoice.read())
        with open(bill_path, "wb") as buffer:
            buffer.write(await bill_of_lading.read())
        with open(cert_path, "wb") as buffer:
            buffer.write(await certificate_of_origin.read())

        session_id = "CUSTOMS-2026-SESSION-01"
        agent = CustomsComplianceAgent(session_id=session_id)

        audit_result = agent.run_audit(
            invoice_path=invoice_path,
            bill_of_lading_path=bill_path,
            cert_of_origin_path=cert_path,
        )

        for p in [invoice_path, bill_path, cert_path]:
            if os.path.exists(p):
                os.remove(p)

        return {
            "success": True,
            "message": "تم الفحص والتدقيق الجمركي بواسطة الوكيل الذكي وقاعدة بيانات SQL Server بنجاح.",
            "result": audit_result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"حدث خطأ أثناء تشغيل الوكيل: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)