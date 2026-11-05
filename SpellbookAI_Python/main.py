from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Spellbook AI Document Auditor")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# المسار الرئيسي (الجذر)
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    is_logged_in = False
    return templates.TemplateResponse(
        request, "home/index.html", {"is_logged_in": is_logged_in}
    )


# دعم مسارات إضافية لتجنب خطأ 404 إذا طلب المستخدم /index أو /index.html
@app.get("/index", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def read_index_alias(request: Request):
    is_logged_in = False
    return templates.TemplateResponse(
        request, "home/index.html", {"is_logged_in": is_logged_in}
    )


# صفحة دليل التعريفة والتقييم الجمركي
@app.get("/hs-code", response_class=HTMLResponse)
async def hs_code_page(request: Request):
    is_logged_in = False
    return templates.TemplateResponse(
        request, "home/hs_code.html", {"is_logged_in": is_logged_in}
    )


# صفحة أرشيف وسجل الفحص الفوري (History)
@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    is_logged_in = False
    return templates.TemplateResponse(
        request, "home/history.html", {"is_logged_in": is_logged_in}
    )


# شاشة تسجيل الدخول
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    return {"message": "تم استلام بيانات تسجيل الدخول", "username": username}


# شاشة إنشاء الحساب
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html")


@app.post("/register")
async def handle_register(
    username: str = Form(...), email: str = Form(...), password: str = Form(...)
):
    return {"message": "تم إنشاء الحساب بنجاح", "username": username}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)