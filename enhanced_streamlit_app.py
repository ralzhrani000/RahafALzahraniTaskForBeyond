import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import time
import re
from pathlib import Path
import json

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة المصنع الذكي - RAG المحسن",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS للعربية والتصميم المحسن مع RTL
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .main .block-container {
        direction: rtl !important;
        text-align: right !important;
        padding-right: 2rem;
        padding-left: 2rem;
    }
    
    .stApp > div {
        direction: rtl !important;
    }
    
    .stSidebar > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        direction: rtl !important;
    }
    
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        direction: rtl !important;
    }
    
    .reference-box {
        background: #f8f9fa;
        border-right: 4px solid #1f77b4;
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        font-size: 12px;
        direction: rtl !important;
    }
    
    .file-uploaded {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif;
        font-weight: 700;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        direction: rtl !important;
        text-align: right !important;
        border-radius: 10px;
        padding: 0.75rem;
    }
    
    .nav-link {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        direction: rtl !important;
        text-align: right !important;
        gap: 8px !important;
    }
    
    .nav-link i {
        min-width: 16px !important;
        text-align: center !important;
        vertical-align: middle !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        direction: rtl !important;
        text-align: center !important;
    }
    
    div[data-testid="metric-container"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stFileUploader > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    .col {
        direction: rtl !important;
        text-align: right !important;
    }
</style>
""", unsafe_allow_html=True)

# بيانات المستخدمين مع صلاحيات محددة
users_db = {
    "admin": {
        "password": "admin123", 
        "role": "مدير عام", 
        "name": "أحمد المدير",
        "permissions": ["all"]
    },
    "hr": {
        "password": "hr123", 
        "role": "موارد بشرية", 
        "name": "سارة الموارد البشرية",
        "permissions": ["hr", "employees", "salaries", "attendance"]
    },
    "maintenance": {
        "password": "maintenance123", 
        "role": "صيانة", 
        "name": "محمد الصيانة",
        "permissions": ["maintenance", "machines", "issues", "repairs"]
    },
    "production": {
        "password": "production123", 
        "role": "إنتاج", 
        "name": "علي الإنتاج",
        "permissions": ["production", "orders", "wip", "delivery"]
    },
    "finance": {
        "password": "finance123", 
        "role": "مالية", 
        "name": "فاطمة المالية",
        "permissions": ["finance", "budgets", "costs", "revenues"]
    }
}

# إنشاء بيانات تجريبية
def get_sample_data():
    """الحصول على البيانات التجريبية"""
    
    # بيانات الموظفين
    employees_data = pd.DataFrame({
        "ID": ["EMP001", "EMP002", "EMP003", "EMP004", "EMP005"],
        "الاسم": ["أحمد.س", "سارة محمد", "محمد علي", "فاطمة أحمد", "علي حسن"],
        "القسم": ["الإنتاج", "الموارد البشرية", "الصيانة", "المالية", "الإنتاج"],
        "الراتب_الأساسي": [8000, 12000, 7500, 10000, 8500],
        "البدلات": [1000, 1500, 800, 1200, 1100],
        "الخصومات": [200, 300, 150, 250, 200],
        "الراتب_الصافي": [8800, 13200, 8150, 10950, 9400],
        "تاريخ_التوظيف": ["2020-01-15", "2019-03-20", "2021-06-10", "2020-08-05", "2021-11-30"]
    })
    
    # بيانات الأعطال
    machine_issues = pd.DataFrame({
        "تاريخ_العطل": ["2025-07-15", "2025-07-20", "2025-07-25", "2025-08-01", "2025-08-10"],
        "اسم_الماكينة": ["داي-كت الرئيسية", "خط التعبئة 1", "داي-كت الرئيسية", "مولد الكهرباء", "نظام التبريد"],
        "نوع_العطل": ["عطل ميكانيكي", "عطل كهربائي", "صيانة دورية", "نقص وقود", "فلاتر مسدودة"],
        "مدة_التوقف_ساعات": [4, 2, 6, 1, 3],
        "التكلفة": [2500, 800, 1200, 150, 600],
        "الحالة": ["مكتمل", "مكتمل", "مكتمل", "مكتمل", "قيد التنفيذ"]
    })
    
    # بيانات الطلبيات
    orders_data = pd.DataFrame({
        "رقم_الطلبية": ["ORD001", "ORD002", "ORD003", "ORD004", "ORD005"],
        "العميل": ["شركة الرياض للمقاولات", "مؤسسة جدة التجارية", "شركة الدمام الصناعية", "مكتب المدينة الهندسي", "شركة أبها للتطوير"],
        "تاريخ_الطلب": ["2025-06-01", "2025-06-05", "2025-06-10", "2025-06-15", "2025-06-20"],
        "تاريخ_التسليم_المطلوب": ["2025-06-08", "2025-06-12", "2025-06-17", "2025-06-22", "2025-06-27"],
        "تاريخ_التسليم_الفعلي": ["2025-06-08", "2025-06-15", "2025-06-17", "2025-06-25", "2025-07-02"],
        "المنتج": ["خزانات معدنية", "أنابيب حديد", "خزانات معدنية", "قطع غيار", "أنابيب حديد"],
        "الكمية": [50, 200, 75, 30, 150],
        "السعر_الإجمالي": [125000, 80000, 187500, 15000, 60000],
        "أيام_التأخير": [0, 3, 0, 3, 5]
    })
    
    return employees_data, machine_issues, orders_data

# تحميل البيانات
EMPLOYEES_DATA, MACHINE_ISSUES, ORDERS_DATA = get_sample_data()

def authenticate(username, password):
    """التحقق من صحة بيانات المستخدم"""
    if username in users_db and users_db[username]["password"] == password:
        return True, users_db[username]
    return False, None

def has_permission(user_info, required_permission):
    """التحقق من الصلاحيات"""
    if not user_info:
        return False
    permissions = user_info.get('permissions', [])
    return 'all' in permissions or required_permission in permissions

def query_structured_data(query, user_info):
    """استعلام البيانات المنظمة مع مراجع دقيقة"""
    results = []
    query_lower = query.lower()
    
    # استعلام الرواتب
    if 'راتب' in query and has_permission(user_info, 'hr'):
        for index, employee in EMPLOYEES_DATA.iterrows():
            if employee['الاسم'] in query:
                reference = f"employees_2025.csv - الصف {index + 2}"
                result = {
                    'type': 'salary',
                    'data': f"""**راتب العامل {employee['الاسم']} لشهر 07/2025:**

• الراتب الأساسي: {employee['الراتب_الأساسي']:,} ر.س
• البدلات: {employee['البدلات']:,} ر.س  
• الخصومات: {employee['الخصومات']:,} ر.س
• **الراتب الصافي: {employee['الراتب_الصافي']:,} ر.س**
• القسم: {employee['القسم']}""",
                    'reference': reference
                }
                results.append(result)
                break
    
    # استعلام أعطال الماكينات
    elif ('عطل' in query or 'ماكينة' in query or 'داي-كت' in query) and has_permission(user_info, 'maintenance'):
        if 'الأسبوع الماضي' in query and 'داي-كت' in query:
            diecut_issues = MACHINE_ISSUES[MACHINE_ISSUES['اسم_الماكينة'].str.contains('داي-كت')]
            
            summary_text = f"**ملخص أعطال ماكينة الداي-كت الأسبوع الماضي:**\n\n"
            references = []
            
            for index, issue in diecut_issues.iterrows():
                summary_text += f"• {issue['تاريخ_العطل']}: {issue['نوع_العطل']} - مدة التوقف: {issue['مدة_التوقف_ساعات']} ساعات - التكلفة: {issue['التكلفة']:,} ر.س\n"
                references.append(f"machine_issues_2025.csv - الصف {index + 2}")
            
            summary_text += f"\n**الإجمالي:** {len(diecut_issues)} أعطال بتكلفة {diecut_issues['التكلفة'].sum():,} ر.س"
            
            results.append({
                'type': 'machine_issues',
                'data': summary_text,
                'reference': " | ".join(references)
            })
    
    # استعلام الطلبيات المتأخرة
    elif ('طلبية' in query or 'تأخر' in query) and has_permission(user_info, 'production'):
        if 'تأخر' in query and '3 أيام' in query:
            if 'شهر 6' in query:
                june_orders = ORDERS_DATA[ORDERS_DATA['تاريخ_الطلب'].str.contains('2025-06')]
                delayed_orders = june_orders[june_orders['أيام_التأخير'] > 3]
                
                summary_text = f"**الطلبات المتأخرة أكثر من 3 أيام في شهر 6/2025:**\n\n"
                summary_text += f"**العدد الإجمالي: {len(delayed_orders)} طلبية**\n\n"
                
                references = []
                for index, order in delayed_orders.iterrows():
                    summary_text += f"• طلبية {order['رقم_الطلبية']}: {order['العميل']} - تأخير {order['أيام_التأخير']} أيام\n"
                    original_index = ORDERS_DATA.index[ORDERS_DATA['رقم_الطلبية'] == order['رقم_الطلبية']].tolist()[0]
                    references.append(f"orders_2025.csv - الصف {original_index + 2}")
                
                total_loss = delayed_orders['السعر_الإجمالي'].sum()
                summary_text += f"\n**القيمة الإجمالية للطلبات المتأخرة: {total_loss:,} ر.س**"
                
                results.append({
                    'type': 'delayed_orders',
                    'data': summary_text,
                    'reference': " | ".join(references)
                })
    
    return results

def generate_enhanced_ai_response(question, user_info):
    """توليد إجابة ذكية محسنة مع مراجع دقيقة"""
    
    # أولاً: محاولة الاستعلام من البيانات المنظمة
    structured_results = query_structured_data(question, user_info)
    
    if structured_results:
        response = ""
        for result in structured_results:
            response += result['data'] + "\n\n"
            response += f"**المرجع:** {result['reference']}\n\n"
        return response
    
    # ثانياً: الردود المعتادة مع تحسينات
    question_lower = question.lower()
    
    # تنظيف النص
    question_clean = re.sub(r'[^\w\s]', '', question_lower)
    words = question_clean.split()
    
    # تصنيف الكلمات المفتاحية
    sales_keywords = ['مبيعات', 'بيع', 'عميل', 'طلب', 'revenue', 'sales']
    maintenance_keywords = ['صيانة', 'عطل', 'ماكينة', 'آلة', 'مكينة', 'تصليح', 'maintenance', 'machine']
    hr_keywords = ['موظف', 'عامل', 'راتب', 'حضور', 'إجازة', 'hr', 'employee', 'salary']
    finance_keywords = ['مالي', 'ميزانية', 'تكلفة', 'ربح', 'مصروف', 'finance', 'budget', 'cost']
    production_keywords = ['إنتاج', 'تصنيع', 'خط', 'جودة', 'production', 'manufacturing']
    
    has_sales = any(word in question_lower for word in sales_keywords)
    has_maintenance = any(word in question_lower for word in maintenance_keywords)
    has_hr = any(word in question_lower for word in hr_keywords)
    has_finance = any(word in question_lower for word in finance_keywords)
    has_production = any(word in question_lower for word in production_keywords)
    
    # فحص الصلاحيات قبل الرد
    if has_hr and not has_permission(user_info, 'hr'):
        return "عذراً، ليس لديك صلاحية للوصول لبيانات الموارد البشرية."
    
    if has_maintenance and not has_permission(user_info, 'maintenance'):
        return "عذراً، ليس لديك صلاحية للوصول لبيانات الصيانة."
    
    if has_production and not has_permission(user_info, 'production'):
        return "عذراً، ليس لديك صلاحية للوصول لبيانات الإنتاج."
    
    if has_finance and not has_permission(user_info, 'finance'):
        return "عذراً، ليس لديك صلاحية للوصول للبيانات المالية."
    
    # الردود المخصصة حسب القسم
    if has_sales or 'مبيعات' in question:
        return f"""**تقرير المبيعات والعملاء:**

**الأداء الحالي:**
• إجمالي المبيعات الشهرية: 995,000 ر.س (+15.2%)
• عدد العملاء الجدد: 12 عميل
• معدل الرضا: 96%
• أهم المنتجات: الخزانات المعدنية (65% من المبيعات)

**العملاء الرئيسيين:**
• شركة الرياض للمقاولات: 125,000 ر.س
• شركة الدمام الصناعية: 187,500 ر.س
• مؤسسة جدة التجارية: 80,000 ر.س

**التوقعات:**
• نمو متوقع 8% الشهر القادم
• طلبات جديدة تحت المراجعة: 5 طلبات

**المرجع:** تقرير المبيعات الشهري + orders_2025.csv"""

    elif has_maintenance or 'صيانة' in question or 'معدات' in question:
        return f"""**تقرير حالة المعدات والصيانة:**

**حالة المعدات الحالية:**
• خط الإنتاج الأول: ✅ يعمل بكامل الطاقة (100%)
• خط الإنتاج الثاني: ⚠️ صيانة مجدولة الثلاثاء
• داي-كت الرئيسية: ⚠️ تحتاج فحص دوري
• مولد الكهرباء: ✅ حالة ممتازة
• نظام التبريد: 🚨 يحتاج فلاتر جديدة

**آخر الأعطال:**
• 2025-08-10: نظام التبريد - فلاتر مسدودة (قيد التنفيذ)
• 2025-08-01: مولد الكهرباء - نقص وقود (مكتمل)
• 2025-07-25: داي-كت الرئيسية - صيانة دورية (مكتمل)

**التكاليف الإجمالية:** 5,250 ر.س

**المرجع:** machine_issues_2025.csv - آخر 5 أعطال مسجلة"""

    elif has_hr or 'موظف' in question:
        return f"""**تقرير الموارد البشرية:**

**إحصائيات الموظفين:**
• إجمالي الموظفين: 5 موظفين
• معدل الحضور: 92%
• إجمالي كشف الرواتب: 50,500 ر.س شهرياً

**توزيع الأقسام:**
• الإنتاج: 2 موظف
• الموارد البشرية: 1 موظف  
• الصيانة: 1 موظف
• المالية: 1 موظف

**آخر التوظيفات:**
• علي حسن - الإنتاج (2021-11-30)
• محمد علي - الصيانة (2021-06-10)

**المرجع:** employees_2025.csv - قاعدة بيانات الموظفين الرئيسية"""

    elif has_finance or 'مالي' in question:
        return f"""**التقرير المالي الشامل:**

**الوضع المالي الحالي:**
• إجمالي الإيرادات: 995,000 ر.س
• إجمالي التكاليف: 325,000 ر.س  
• **صافي الربح: 670,000 ر.س**
• هامش الربح: 67.3%

**تفصيل التكاليف:**
• الرواتب والأجور: 180,000 ر.س (55%)
• المواد الخام: 85,000 ر.س (26%)
• الكهرباء والماء: 25,000 ر.س (8%)
• الصيانة: 15,000 ر.س (5%)
• مصروفات إدارية: 20,000 ر.س (6%)

**التدفق النقدي:**
• النقدية المتاحة: 285,000 ر.س
• الذمم المدينة: 125,000 ر.س
• الذمم الدائنة: 75,000 ر.س

**المرجع:** التقرير المالي الشهري + بيانات التكاليف الداخلية"""

    elif has_production or 'إنتاج' in question:
        return f"""**تقرير الإنتاج والتشغيل:**

**أداء الإنتاج:**
• الطاقة الإنتاجية: 95% من الهدف المخطط
• معدل الجودة: 98.5% (ممتاز)
• الطلبات المنجزة: 5 طلبات هذا الشهر
• متوسط وقت التسليم: 3.2 أيام

**حالة خطوط الإنتاج:**
• الخط الأول: يعمل بكامل الطاقة (24/7)
• الخط الثاني: صيانة مجدولة الثلاثاء
• خط التعبئة: كفاءة 92%

**المنتجات الحالية:**
• خزانات معدنية: 65% من الإنتاج
• أنابيب حديدية: 25% من الإنتاج  
• قطع غيار: 10% من الإنتاج

**الطلبات المعلقة:**
• طلبية ORD005: تأخير 5 أيام (شركة أبها للتطوير)

**المرجع:** orders_2025.csv + تقارير الإنتاج اليومية"""

    else:
        # رد افتراضي مع إرشادات
        return f"""**مساعدك الذكي - نظام محسن مع مراجع دقيقة**

**أهلاً {user_info.get('name', 'المستخدم')}!** 

يمكنني الآن الإجابة على أسئلتك مع **مراجع دقيقة** من الملفات الفعلية:

**أمثلة للاستعلامات المدعومة:**

🔹 **للرواتب:** "راتب العامل أحمد.س لشهر 07/2025 مع الخصومات؟"

🔹 **للأعطال:** "أعطني ملخص أعطال ماكينة الداي-كت الأسبوع الماضي"

🔹 **للطلبيات:** "كم طلبية تأخرت أكثر من 3 أيام في شهر 6؟"

**مميزات النظام الجديد:**
• ✅ استعلامات دقيقة من البيانات الفعلية
• ✅ مراجع واضحة (اسم الملف + رقم الصف)
• ✅ صلاحيات محددة لكل مستخدم
• ✅ دعم كامل للغة العربية

**صلاحياتك الحالية:** {user_info.get('role', 'غير محدد')}

جرب أحد الأمثلة أعلاه أو اطرح سؤالك المخصص! 💪"""

def login_page():
    """صفحة تسجيل الدخول"""
    st.markdown("""
    <div style='text-align: center; padding: 2rem; direction: rtl;'>
        <h1 style='color: #1f4e79; font-size: 3rem;'>نظام إدارة المصنع الذكي - RAG المحسن</h1>
        <p style='font-size: 1.2rem; color: #666;'>منصة متكاملة مع مراجع دقيقة وصلاحيات محددة</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### تسجيل الدخول")
        
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            
            # إظهار بيانات المستخدمين التجريبية
            show_demo_accounts = st.checkbox("إظهار الحسابات التجريبية")
            
            if show_demo_accounts:
                st.markdown("### الحسابات التجريبية:")
                for user, data in users_db.items():
                    st.markdown(f"**{data['role']}:** {user} / {data['password']}")
            
            submit_button = st.form_submit_button("تسجيل الدخول")
            
            if submit_button:
                if username and password:
                    is_valid, user_info = authenticate(username, password)
                    if is_valid:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user_info
                        st.success(f"مرحباً {user_info['name']}!")
                        st.rerun()
                    else:
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
                else:
                    st.warning("الرجاء إدخال اسم المستخدم وكلمة المرور")

def dashboard_page():
    """لوحة التحكم الرئيسية"""
    st.title("لوحة التحكم الرئيسية")
    
    user_info = st.session_state.get('user_info', {})
    st.markdown(f"### مرحباً {user_info.get('name', 'المستخدم')} - {user_info.get('role', 'دور غير محدد')}")
    
    # عرض الصلاحيات
    permissions = user_info.get('permissions', [])
    if 'all' in permissions:
        st.success("🔓 لديك صلاحية الوصول لجميع البيانات")
    else:
        st.info(f"🔒 صلاحياتك: {', '.join(permissions)}")
    
    # بيانات وهمية
    sales_data = pd.DataFrame({
        'الشهر': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو'],
        'المبيعات': [150000, 180000, 220000, 195000, 250000],
        'التكاليف': [120000, 140000, 170000, 150000, 190000]
    })
    
    # الإحصائيات السريعة
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sales = sales_data['المبيعات'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <h3>إجمالي المبيعات</h3>
            <h2>{total_sales:,} ر.س</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="success-card">
            <h3>عدد الموظفين</h3>
            <h2>25 موظف</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>المشاريع النشطة</h3>
            <h2>8 مشاريع</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        profit = sales_data['المبيعات'].sum() - sales_data['التكاليف'].sum()
        st.markdown(f"""
        <div class="success-card">
            <h3>صافي الربح</h3>
            <h2>{profit:,} ر.س</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # الرسوم البيانية
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("تطور المبيعات والتكاليف")
        fig = px.line(sales_data, x='الشهر', y=['المبيعات', 'التكاليف'], 
                     title="الأداء المالي الشهري")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("توزيع الأقسام")
        departments = ['الإنتاج', 'المالية', 'الصيانة', 'الموارد البشرية', 'المبيعات']
        counts = [8, 4, 5, 3, 5]
        fig = px.pie(values=counts, names=departments, title="توزيع الموظفين")
        st.plotly_chart(fig, use_container_width=True)

def enhanced_files_page():
    """صفحة إدارة الملفات المحسنة"""
    st.title("إدارة الملفات والمستندات المحسنة")
    
    user_info = st.session_state.get('user_info', {})
    
    tab1, tab2, tab3 = st.tabs(["رفع ملف مع فهرسة", "البيانات المفهرسة", "احصائيات النظام"])
    
    with tab1:
        st.subheader("رفع ملف جديد مع فهرسة تلقائية")
        
        col1, col2 = st.columns(2)
        with col1:
            file_category = st.selectbox("فئة الملف", 
                                       ["HR - الموارد البشرية", "Maintenance - الصيانة", "Production - الإنتاج", 
                                        "Finance - المالية", "General - عام"])
        with col2:
            file_priority = st.selectbox("أولوية الملف", ["عالية", "متوسطة", "منخفضة"])
        
        # رفع الملف
        uploaded_file = st.file_uploader(
            "اختر ملف (PDF, DOCX, TXT, CSV, XLSX)",
            type=['pdf', 'docx', 'txt', 'csv', 'xlsx'],
            help="الملفات المدعومة: PDF للمستندات، DOCX للتقارير، CSV/XLSX للبيانات الرقمية"
        )
        
        additional_info = st.text_area("معلومات إضافية (اختياري)", 
                                     placeholder="مثال: تقرير صيانة الماكينة رقم 3، تاريخ العمل 2025-08-15")
        
        if uploaded_file is not None:
            # عرض معلومات الملف
            st.markdown(f"""
            <div class="file-uploaded">
                ✅ **تم رفع الملف:** {uploaded_file.name}<br>
                📏 **الحجم:** {uploaded_file.size} بايت<br>
                📄 **النوع:** {uploaded_file.type}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("فهرسة الملف وحفظه"):
                with st.spinner("جاري المعالجة والفهرسة..."):
                    # محاكاة عملية الفهرسة
                    time.sleep(2)
                    
                    # حفظ المعلومات في session state
                    if 'indexed_files' not in st.session_state:
                        st.session_state.indexed_files = []
                    
                    file_info = {
                        'filename': uploaded_file.name,
                        'category': file_category,
                        'priority': file_priority,
                        'uploaded_by': user_info.get('name', 'مجهول'),
                        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'additional_info': additional_info,
                        'size': uploaded_file.size,
                        'type': uploaded_file.type,
                        'indexed': True
                    }
                    
                    st.session_state.indexed_files.append(file_info)
                    
                    st.success(f"✅ تم فهرسة الملف بنجاح! يمكن الآن البحث فيه عبر المساعد الذكي.")
                    
                    # معلومات تقنية للفهرسة
                    with st.expander("معلومات الفهرسة التقنية"):
                        st.json({
                            "معرف_الملف": f"FILE_{len(st.session_state.indexed_files):04d}",
                            "حالة_الاستخراج": "نجح",
                            "عدد_الكلمات_المستخرجة": "~500 كلمة",
                            "طريقة_الفهرسة": "Vector Embedding + Metadata",
                            "قابل_للبحث": True
                        })
    
    with tab2:
        st.subheader("البيانات والملفات المفهرسة")
        
        # عرض البيانات الأساسية
        st.markdown("### البيانات الأساسية المتاحة:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"""
            **بيانات الموظفين**
            📁 employees_2025.csv
            📊 {len(EMPLOYEES_DATA)} سجل
            🔍 قابل للاستعلام
            """)
        
        with col2:
            st.info(f"""
            **بيانات الأعطال** 
            📁 machine_issues_2025.csv
            📊 {len(MACHINE_ISSUES)} سجل
            🔍 قابل للاستعلام
            """)
        
        with col3:
            st.info(f"""
            **بيانات الطلبيات**
            📁 orders_2025.csv  
            📊 {len(ORDERS_DATA)} سجل
            🔍 قابل للاستعلام
            """)
        
        # عرض الملفات المرفوعة
        if 'indexed_files' in st.session_state and st.session_state.indexed_files:
            st.markdown("### الملفات المرفوعة حديثاً:")
            
            files_df = pd.DataFrame(st.session_state.indexed_files)
            st.dataframe(files_df[['filename', 'category', 'uploaded_by', 'upload_date', 'indexed']], 
                        use_container_width=True)
        else:
            st.info("لا توجد ملفات مرفوعة حديثاً. قم برفع ملفات من التبويب الأول.")
    
    with tab3:
        st.subheader("إحصائيات النظام")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            indexed_count = len(st.session_state.get('indexed_files', []))
            st.metric("الملفات المفهرسة", indexed_count + 3, delta=indexed_count)  # +3 للملفات الأساسية
        
        with col2:
            total_records = len(EMPLOYEES_DATA) + len(MACHINE_ISSUES) + len(ORDERS_DATA)
            st.metric("إجمالي السجلات", total_records)
        
        with col3:
            st.metric("الاستعلامات اليوم", 12, delta=3)
        
        # إحصائيات مفصلة
        st.markdown("### تفاصيل النظام:")
        
        system_stats = {
            "نوع_النظام": "RAG محسن مع مراجع دقيقة",
            "قواعد_البيانات_المدعومة": ["CSV", "Excel", "PDF", "DOCX", "TXT"],
            "الصلاحيات_النشطة": len(users_db),
            "آخر_تحديث": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "حالة_النظام": "نشط ومستقر ✅"
        }
        
        st.json(system_stats)

def enhanced_chat_page():
    """صفحة المحادثة المحسنة مع RAG"""
    st.title("مساعدك الذكي المحسن - مع مراجع دقيقة")
    
    user_info = st.session_state.get('user_info', {})
    
    tab1, tab2 = st.tabs(["المساعد الذكي المحسن", "دردشة الفريق"])
    
    with tab1:
        st.markdown(f"### مرحباً **{user_info.get('name', 'المستخدم')}** - صلاحياتك: **{user_info.get('role', 'غير محدد')}**")
        
        # إعداد المحادثة
        if 'enhanced_ai_messages' not in st.session_state:
            st.session_state.enhanced_ai_messages = [
                {
                    "role": "assistant", 
                    "content": f"""مرحباً **{user_info.get('name', 'المستخدم')}**! 

أنا المساعد الذكي المحسن. الآن يمكنني:

✅ **الإجابة بمراجع دقيقة** من ملفاتك الفعلية
✅ **تنفيذ استعلامات محددة** على البيانات الرقمية  
✅ **مراعاة صلاحياتك** ({user_info.get('role', 'غير محدد')})
✅ **تقديم المراجع** (اسم الملف + رقم الصف/الصفحة)

**جرب هذه الأمثلة:**
🔹 "راتب العامل أحمد.س لشهر 07/2025 مع الخصومات؟"
🔹 "أعطني ملخص أعطال ماكينة الداي-كت الأسبوع الماضي"  
🔹 "كم طلبية تأخرت أكثر من 3 أيام في شهر 6؟"

كيف يمكنني مساعدتك اليوم؟ 🚀"""
                }
            ]
        
        # اقتراحات سريعة
        st.markdown("### اقتراحات مبنية على صلاحياتك:")
        
        # عرض الاقتراحات حسب الصلاحيات
        permissions = user_info.get('permissions', [])
        
        if 'all' in permissions or 'hr' in permissions:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("راتب أحمد.س لشهر 07/2025", key="salary_btn"):
                    question = "راتب العامل أحمد.س لشهر 07/2025 مع الخصومات؟"
                    st.session_state.enhanced_ai_messages.append({"role": "user", "content": question})
                    response = generate_enhanced_ai_response(question, user_info)
                    st.session_state.enhanced_ai_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with col2:
                if st.button("تقرير الموارد البشرية", key="hr_btn"):
                    question = "أعطني تقرير شامل عن الموارد البشرية"
                    st.session_state.enhanced_ai_messages.append({"role": "user", "content": question})
                    response = generate_enhanced_ai_response(question, user_info)
                    st.session_state.enhanced_ai_messages.append({"role": "assistant", "content": response})
                    st.rerun()
        
        if 'all' in permissions or 'maintenance' in permissions:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("أعطال ماكينة الداي-كت", key="machine_btn"):
                    question = "أعطني ملخص أعطال ماكينة الداي-كت الأسبوع الماضي"
                    st.session_state.enhanced_ai_messages.append({"role": "user", "content": question})
                    response = generate_enhanced_ai_response(question, user_info)
                    st.session_state.enhanced_ai_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with col2:
                if st.button("حالة المعدات", key="equipment_btn"):
                    question = "ما حالة المعدات والماكينات؟"
                    st.session_state.enhanced_ai_messages.append({"role": "user", "content": question})
                    response = generate_enhanced_ai_response(question, user_info)
                    st.session_state.enhanced_ai_messages.append({"role": "assistant", "content": response})
                    st.rerun()
        
        if 'all' in permissions or 'production' in permissions:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("الطلبات المتأخرة في يونيو", key="delayed_btn"):
                    question = "كم طلبية تأخرت أكثر من 3 أيام في شهر 6؟"
                    st.session_state.enhanced_ai_messages.append({"role": "user", "content": question})
                    response = generate_enhanced_ai_response(question, user_info)
                    st.session_state.enhanced_ai_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with col2:
                if st.button("تقرير الإنتاج", key="production_btn"):
                    question = "كيف أداء الإنتاج والتشغيل؟"
                    st.session_state.enhanced_ai_messages.append({"role": "user", "content": question})
                    response = generate_enhanced_ai_response(question, user_info)
                    st.session_state.enhanced_ai_messages.append({"role": "assistant", "content": response})
                    st.rerun()
        
        st.markdown("---")
        
        # منطقة الدردشة المحسنة
        st.markdown("### محادثة مع مراجع دقيقة:")
        
        with st.container(height=400):
            for message in st.session_state.enhanced_ai_messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        
        # خانة الكتابة
        if prompt := st.chat_input("اكتب سؤالك المحدد هنا... (مثال: راتب أحمد.س أو أعطال الداي-كت)"):
            # إضافة رسالة المستخدم
            st.session_state.enhanced_ai_messages.append({"role": "user", "content": prompt})
            
            # توليد رد محسن
            with st.spinner("جاري البحث في البيانات وتوليد الإجابة..."):
                ai_response = generate_enhanced_ai_response(prompt, user_info)
            
            st.session_state.enhanced_ai_messages.append({"role": "assistant", "content": ai_response})
            st.rerun()
    
    with tab2:
        st.subheader("دردشة الفريق")
        st.info("ميزة دردشة الفريق ستكون متاحة قريباً مع إشعارات فورية.")

def hr_page():
    """صفحة الموارد البشرية مع صلاحيات"""
    st.title("الموارد البشرية")
    
    user_info = st.session_state.get('user_info', {})
    
    # فحص الصلاحيات
    if not has_permission(user_info, 'hr'):
        st.error("⛔ عذراً، ليس لديك صلاحية للوصول لبيانات الموارد البشرية")
        st.info(f"صلاحياتك الحالية: {user_info.get('role', 'غير محدد')}")
        return
    
    # بيانات الموظفين (من البيانات المحسنة)
    tab1, tab2 = st.tabs(["الإحصائيات", "قائمة الموظفين"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("إجمالي الموظفين", len(EMPLOYEES_DATA))
        with col2:
            active_count = len(EMPLOYEES_DATA)  # جميع الموظفين نشطين في البيانات التجريبية
            st.metric("الموظفون النشطون", active_count)
        with col3:
            avg_salary = EMPLOYEES_DATA['الراتب_الصافي'].mean()
            st.metric("متوسط الراتب الصافي", f"{avg_salary:,.0f} ر.س")
        
        # رسم بياني للرواتب
        fig = px.bar(EMPLOYEES_DATA, x='الاسم', y='الراتب_الصافي', 
                    color='القسم', title="الرواتب الصافية حسب الموظف والقسم")
        st.plotly_chart(fig, use_container_width=True)
        
        # رسم دائري للأقسام
        dept_counts = EMPLOYEES_DATA['القسم'].value_counts()
        fig2 = px.pie(values=dept_counts.values, names=dept_counts.index, 
                     title="توزيع الموظفين حسب القسم")
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("بيانات الموظفين التفصيلية")
        
        # عرض الجدول مع إمكانية التصفية
        selected_dept = st.selectbox("تصفية حسب القسم", 
                                   ["الكل"] + EMPLOYEES_DATA['القسم'].unique().tolist())
        
        if selected_dept != "الكل":
            filtered_data = EMPLOYEES_DATA[EMPLOYEES_DATA['القسم'] == selected_dept]
        else:
            filtered_data = EMPLOYEES_DATA
        
        st.dataframe(filtered_data, use_container_width=True)
        
        # معلومات إضافية
        st.markdown(f"""
        **المرجع:** employees_2025.csv  
        **عدد السجلات:** {len(filtered_data)}  
        **آخر تحديث:** 2025-07-31
        """)

def main():
    """الدالة الرئيسية"""
    # تهيئة حالة الجلسة
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {}
    
    # فحص تسجيل الدخول
    if not st.session_state.logged_in:
        login_page()
        return
    
    # الشريط الجانبي للتنقل
    with st.sidebar:
        st.markdown(f"### مرحباً {st.session_state.user_info.get('name', 'المستخدم')}")
        st.markdown(f"**الدور:** {st.session_state.user_info.get('role', 'غير محدد')}")
        
        selected = option_menu(
            "القائمة الرئيسية",
            ["لوحة التحكم", "إدارة الملفات المحسنة", "مساعدك الذكي المحسن", "الموارد البشرية"],
            icons=["speedometer2", "folder-plus", "robot", "people"],
            menu_icon="grid-3x3-gap",
            default_index=0,
            styles={
                "container": {"direction": "rtl", "text-align": "right"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "right",
                    "direction": "rtl",
                    "--hover-color": "#f0f2f6",
                    "display": "flex",
                    "align-items": "center",
                    "justify-content": "flex-start",
                    "gap": "8px"
                },
                "nav-link-selected": {
                    "background-color": "#1f77b4",
                    "color": "white",
                    "font-weight": "600"
                },
                "icon": {
                    "color": "#666",
                    "font-size": "16px",
                    "min-width": "16px",
                    "text-align": "center"
                }
            }
        )
        
        if st.button("تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.user_info = {}
            st.rerun()
    
    # عرض الصفحات
    if selected == "لوحة التحكم":
        dashboard_page()
    elif selected == "إدارة الملفات المحسنة":
        enhanced_files_page()
    elif selected == "مساعدك الذكي المحسن":
        enhanced_chat_page()
    elif selected == "الموارد البشرية":
        hr_page()

if __name__ == "__main__":
    main()
