
import streamlit as st
import pandas as pd

# رفع ملف البيانات الأساسي
data_file = st.file_uploader("رفع ملف البيانات الأساسي", type=["xlsx", "csv"])
# رفع تقرير القروض
q_report_file = st.file_uploader("رفع تقرير القروض", type=["xlsx", "csv"])

if data_file is not None and q_report_file is not None:
    # قراءة ملفات Excel أو CSV بناءً على نوع الملف
    if data_file.name.endswith('.xlsx'):
        data = pd.read_excel(data_file)
    else:
        data = pd.read_csv(data_file)
    
    if q_report_file.name.endswith('.xlsx'):
        q_report = pd.read_excel(q_report_file)
    else:
        q_report = pd.read_csv(q_report_file)
    # تعديل اسم العمود رقم 19 إلى "المدفوع"
    data.rename(columns={data.columns[18]: "المدفوع"}, inplace=True)

    # دمج تقرير القروض لجلب "حالة القرض"
    data = data.merge(q_report[['رقم القرض', 'حالة القرض']], on='رقم القرض', how='left')
    data = data.merge(q_report[['رقم القرض', 'عدد أيام التأخير للقسط المستحق']], on='رقم القرض', how='left')

    # فلترة العملاء بناءً على "حالة القرض" (الإبقاء على القروض القائمة فقط)
    data_filtered = data[(data['حالة القرض'] == 'القرض قائم') & (data['عدد أيام التأخير للقسط المستحق'] == 0)]
    
    # أخذ أول قسط لكل قرض فقط بناءً على "رقم القرض"
    data_filtered = data_filtered.sort_values(by=['رقم القرض', 'رقم القسط'])
    first_installment = data_filtered.drop_duplicates(subset=['رقم القرض'], keep='first')

    # حساب إجمالي الأصول لكل قرض
    total_assets = data_filtered.groupby('رقم القرض')['قيمة الاصل من القسط'].sum().reset_index()
    total_assets.rename(columns={'قيمة الاصل من القسط': 'إجمالي الأصول'}, inplace=True)

    # حساب إجمالي الفائدة لكل قرض
    total_interest = data_filtered.groupby('رقم القرض')['قيمة الفائده من القسط'].sum().reset_index()
    total_interest.rename(columns={'قيمة الفائده من القسط': 'إجمالي الفائدة'}, inplace=True)

    # دمج البيانات مع أول قسط
    result = first_installment.merge(total_assets, on='رقم القرض', how='left')
    result = result.merge(total_interest, on='رقم القرض', how='left')

    # حساب إجمالي المطلوب من العميل
    result['إجمالي المطلوب'] = result['إجمالي الأصول'] + result['إجمالي الفائدة']

    # حساب المتبقي على العميل
    result['المتبقي على العميل'] = result['المدفوع'] - result['إجمالي المطلوب']

    # حساب الأصل بدون أصل أول قسط
    result['الأصل بدون أول قسط'] = result['إجمالي الأصول'] - result['قيمة الاصل من القسط']

    # حساب قيمة السداد المعجل
    result['قيمة السداد المعجل'] = (result['الأصل بدون أول قسط'] * 1.05) + result['قيمة القسط']

    # حساب المتبقي للسداد المعجل
    result['المتبقي للسداد المعجل'] = result['المدفوع'] - result['قيمة السداد المعجل']    # عرض النتائج في التطبيق
    st.write(result)

    # حفظ البيانات في ملف جديد
    result_filename = "سداد_معجل.xlsx"
    result.to_excel(result_filename, index=False)
    
    # إضافة زر التحميل بعد إنشاء الملف فقط
    st.success("تم إنشاء شيت السداد المعجل بنجاح.")
    st.download_button(
        label="تحميل ملف السداد المعجل",
        data=open(result_filename, "rb").read(),
        file_name=result_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.warning("يرجى تحميل الملفات قبل المتابعة.")