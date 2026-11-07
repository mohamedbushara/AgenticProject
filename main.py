from datetime import datetime
from database import engine, get_db
from fastapi import Cookie, Depends, FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models.user import Base, User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# إنشاء الجداول تلقائياً في SQL Server
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spellbook AI Document Auditor")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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

  # البحث بالاسم أو البريد الإلكتروني
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

  # توجيه ناجح وتعيين الـ Cookie للمستخدم
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

  # 1. التحقق من تطابق كلمات المرور
  if password != confirm_password:
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {"error_message": "كلمتا المرور غير متطابقتين!"},
    )

  try:
    # 2. التحقق من تكرار اسم المستخدم
    existing_user = (
        db.query(User).filter(User.username == clean_username).first()
    )
    if existing_user:
      return templates.TemplateResponse(
          request,
          "auth/register.html",
          {
              "error_message": (
                  "اسم المستخدم هذا مسجل مسبقاً، يرجى اختيار اسم آخر."
              )
          },
      )

    # 3. التحقق من تكرار البريد الإلكتروني
    existing_email = db.query(User).filter(User.email == clean_email).first()
    if existing_email:
      return templates.TemplateResponse(
          request,
          "auth/register.html",
          {"error_message": "البريد الإلكتروني هذا مستخدم لحساب آخر مسبقاً."},
      )

    # 4. الحفظ في SQL Server
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

  # 5. التوجيه الناجح لشاشة الدخول
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


if __name__ == "__main__":
  import uvicorn

  uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)