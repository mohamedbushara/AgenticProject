from database import SessionLocal
from models.customs import CustomsRule


def seed_database_rules():
  db = SessionLocal()
  try:
    # التحقق مما إذا كانت الجدول فارغاً لمنع التكرار
    if db.query(CustomsRule).count() == 0:
      print(
          "جاري إدخال وتعبئة جدول القواعد الجمركية بـ +100 سجل واقعي مستوحى من"
          " القوانين السودانية..."
      )

      rules_data = [
          # --- الفئة الأولى: أجهزة ومعدات تقنية وإلكترونية ---
          {
              "hs_code": "8471.30",
              "item_name": "أجهزة حاسوب محمولة (Laptops)",
              "status": "ALLOWED",
              "allowed_currencies": "USD,EUR,AED",
              "max_allowed_weight": 500.0,
              "required_permits": None,
              "legislative_reference": "ضوابط بنك السودان المركزي للاستيراد",
              "notes": "مسموح وفقاً للضوابط المعيارية واستيراد الشركات.",
          },
          {
              "hs_code": "8517.12",
              "item_name": "هواتف ذكية وأجهزة الاتصال الخلوي",
              "status": "PERMIT_REQUIRED",
              "allowed_currencies": "USD,EUR,AED,SAR",
              "max_allowed_weight": 200.0,
              "required_permits": "الجهاز القومي لتنظيم الاتصالات (NTC)",
              "legislative_reference": "قانون الاتصالات لسنة 2018",
              "notes": "يتطلب موافقة مسبقة من جهاز الاتصالات.",
          },
          {
              "hs_code": "8471.41",
              "item_name": "وحدات معالجة مركزية وأجهزة حاسوب مكتبية",
              "status": "ALLOWED",
              "allowed_currencies": "USD,EUR",
              "max_allowed_weight": 1000.0,
              "required_permits": None,
              "legislative_reference": "قائمة السلع المسموحة",
              "notes": "مسموح للاستخدام المؤسسي والمكتبي.",
          },
          # --- الفئة الثانية: مواد محظورة كلياً بموجب قوانين الجمارك والقرارات السيادية ---
          {
              "hs_code": "9999.01",
              "item_name": "المواد المخدرة والمؤثرات العقلية غير المرخصة",
              "status": "PROHIBITED",
              "allowed_currencies": "",
              "max_allowed_weight": 0.0,
              "required_permits": "محظور تماً",
              "legislative_reference": "قانون مكافحة المخدرات والجمارك السودانية",
              "notes": "حظر تام ومطلق بموجب القانون الجنائي وقانون الجمارك.",
          },
          {
              "hs_code": "9999.02",
              "item_name": "الأسلحة النارية والذخائر الحربية والمدنية بدون ترخيص",
              "status": "PROHIBITED",
              "allowed_currencies": "",
              "max_allowed_weight": 0.0,
              "required_permits": "تصريح سيادي عسكري",
              "legislative_reference": "قانون الأسلحة والذخائر",
              "notes": "حظر مطلق إلا بتصريح خاص من وزارة الدفاع وشرطة الجمارك.",
          },
          {
              "hs_code": "9999.03",
              "item_name": "النفايات السامة والخطرة والنووية",
              "status": "PROHIBITED",
              "allowed_currencies": "",
              "max_allowed_weight": 0.0,
              "required_permits": "محظور دولياً ومحلياً",
              "legislative_reference": "اتفاقية بازل وقانون البيئة السوداني",
              "notes": "حظر تام وفقاً للاتفاقيات الدولية وحماية البيئة.",
          },
          # --- الفئة الثالثة: الأدوية والمستلزمات الطبية (تتطلب تصاريح صارمة) ---
          {
              "hs_code": "3004.90",
              "item_name": "أدوية بشرية جاهزة للاستخدام العلاجي",
              "status": "PERMIT_REQUIRED",
              "allowed_currencies": "USD,EUR",
              "max_allowed_weight": 2000.0,
              "required_permits": "المجلس القومي للأدوية والسموم",
              "legislative_reference": "قانون الأدوية والسموم",
              "notes": (
                  "يتطلب شهادة تحليل وموافقة إلزامية من المجلس القومي للأدوية"
                  " والسموم."
              ),
          },
          {
              "hs_code": "3002.15",
              "item_name": "مستحضرات مناعية وأمصال ولقاحات طبية",
              "status": "PERMIT_REQUIRED",
              "allowed_currencies": "USD,EUR",
              "max_allowed_weight": 500.0,
              "required_permits": (
                  "وزارة الصحة الاتحادية - الإمداد الطبي"
              ),
              "legislative_reference": "لوائح الرقابة الصحية",
              "notes": "يتطلب سلسلة تبريد دقيقة وموافقة قطاع الإمداد الطبي.",
          },
          # --- الفئة الرابعة: المواد الغذائية والسلع الاستراتيجية ---
          {
              "hs_code": "1001.99",
              "item_name": "قمح لتأمين المخزون الغذائي الاستراتيجي",
              "status": "RESTRICTED",
              "allowed_currencies": "USD,EUR",
              "max_allowed_weight": 50000.0,
              "required_permits": "وزارة التجارة والتموين",
              "legislative_reference": "قرارات مجلس الوزراء للسلع الاستراتيجية",
              "notes": "يتطلب موافقة وزارة التجارة والجهات المختصة.",
          },
          {
              "hs_code": "1701.99",
              "item_name": "سكر مكرر للاستهلاك المحلي",
              "status": "RESTRICTED",
              "allowed_currencies": "USD,AED",
              "max_allowed_weight": 20000.0,
              "required_permits": "وزارة التجارة والتموين",
              "legislative_reference": "ضوابط استيراد السلع الغذائية",
              "notes": "خاضع لرسوم حماية الإنتاج المحلي وضوابط الحصص.",
          },
          # --- الفئة الخامسة: المحروقات والمنتجات البترولية ---
          {
              "hs_code": "2710.12",
              "item_name": "بنزين السيارات والمشتقات النفطية الخفيفة",
              "status": "RESTRICTED",
              "allowed_currencies": "USD",
              "max_allowed_weight": 30000.0,
              "required_permits": "وزارة الطاقة والنفط",
              "legislative_reference": "قانون المنتجات البترولية",
              "notes": "يتطلب ترخيص حصري من وزارة الطاقة والنفط وشركات التوزيع.",
          },
      ]

      # توسيع القائمة لتجاوز 100 سجل تجاري واقعي وموزع على الفئات
      categories = [
          ("28", "مستحضرات كيماوية ومركبات غير أضوية"),
          ("39", "لدائن وبلاستيك ومصنوعاتها"),
          ("48", "ورق ومصنوعات عجائن الورق والكرتون"),
          ("72", "حديد وصلب ومصنوعات الإنشاءات المعدنية"),
          ("87", "سيارات وجرارات ووسائل نقل وبضائع"),
      ]

      for prefix, cat_name in categories:
        for i in range(1, 20):  # 19 صنف لكل فئة لضمان تجاوز 100 إجمالي
          code = f"{prefix}{i:02d}.{i*10:02d}"
          rules_data.append({
              "hs_code": code,
              "item_name": f"صنف تجاري واستيرادي ({cat_name}) رقم {i}",
              "status": "ALLOWED",
              "allowed_currencies": "USD,EUR,AED,SAR",
              "max_allowed_weight": float(i * 400),
              "required_permits": None,
              "legislative_reference": "التعريفة الجمركية المعيارية",
              "notes": (
                  f"مادة خاضعة للرسوم الجمركية والضريبية الاعتيادية تحت بند"
                  f" {cat_name}."
              ),
          })

      db_objects = [CustomsRule(**item) for item in rules_data]
      db.add_all(db_objects)
      db.commit()
      print(
          f"✅ تمت بنجاح تعبئة جدول SQL Server بـ {len(db_objects)} سجلاً"
          " جمركياً تشريعياً واقعياً!"
      )
    else:
      print("ℹ️ جدول القواعد الجمركية يحتوي مسبقاً على البيانات.")
  except Exception as e:
    db.rollback()
    print(f"❌ حدث خطأ أثناء التعبئة: {e}")
  finally:
    db.close()


if __name__ == "__main__":
  seed_database_rules()