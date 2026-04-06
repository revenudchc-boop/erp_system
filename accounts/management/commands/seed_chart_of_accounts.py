from django.core.management.base import BaseCommand
from accounts.models import Account

class Command(BaseCommand):
    help = 'Seeds the database with a standard Egyptian chart of accounts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed chart of accounts...'))
        
        # تعريف دليل الحسابات (القائمة الرئيسية)
        accounts_data = [
            # الأصول (1)
            {'code': '1', 'name': 'الأصول', 'type': 'asset', 'parent_code': None},
            {'code': '11', 'name': 'أصول متداولة', 'type': 'asset', 'parent_code': '1'},
            {'code': '111', 'name': 'نقدية بالصندوق', 'type': 'asset', 'parent_code': '11'},
            {'code': '112', 'name': 'نقدية بالبنك', 'type': 'asset', 'parent_code': '11'},
            {'code': '113', 'name': 'شيكات تحت التحصيل', 'type': 'asset', 'parent_code': '11'},
            {'code': '12', 'name': 'ذمم مدينة (عملاء)', 'type': 'asset', 'parent_code': '1'},
            {'code': '121', 'name': 'عملاء محليون', 'type': 'asset', 'parent_code': '12'},
            {'code': '122', 'name': 'عملاء أجانب', 'type': 'asset', 'parent_code': '12'},
            {'code': '13', 'name': 'أوراق مالية واستثمارات قصيرة الأجل', 'type': 'asset', 'parent_code': '1'},
            {'code': '14', 'name': 'مخزون', 'type': 'asset', 'parent_code': '1'},
            {'code': '141', 'name': 'مخزون مواد خام', 'type': 'asset', 'parent_code': '14'},
            {'code': '142', 'name': 'مخزون تحت التشغيل', 'type': 'asset', 'parent_code': '14'},
            {'code': '143', 'name': 'مخزون تام الصنع', 'type': 'asset', 'parent_code': '14'},
            {'code': '144', 'name': 'مخزون مهمات وقطع غيار', 'type': 'asset', 'parent_code': '14'},
            {'code': '15', 'name': 'أصول ثابتة', 'type': 'asset', 'parent_code': '1'},
            {'code': '151', 'name': 'أراضي', 'type': 'asset', 'parent_code': '15'},
            {'code': '152', 'name': 'مباني', 'type': 'asset', 'parent_code': '15'},
            {'code': '153', 'name': 'آلات ومعدات', 'type': 'asset', 'parent_code': '15'},
            {'code': '154', 'name': 'أثاث وتجهيزات', 'type': 'asset', 'parent_code': '15'},
            {'code': '155', 'name': 'وسائل نقل', 'type': 'asset', 'parent_code': '15'},
            {'code': '156', 'name': 'أصول غير ملموسة (برمجيات، شهرة)', 'type': 'asset', 'parent_code': '15'},
            {'code': '157', 'name': 'مجمع إهلاك الأصول الثابتة', 'type': 'asset', 'parent_code': '15'},
            {'code': '16', 'name': 'مصروفات مدفوعة مقدماً', 'type': 'asset', 'parent_code': '1'},
            {'code': '17', 'name': 'ودائع تأمينية', 'type': 'asset', 'parent_code': '1'},

            # الخصوم (2)
            {'code': '2', 'name': 'الخصوم', 'type': 'liability', 'parent_code': None},
            {'code': '21', 'name': 'خصوم متداولة', 'type': 'liability', 'parent_code': '2'},
            {'code': '211', 'name': 'دائنون (موردون)', 'type': 'liability', 'parent_code': '21'},
            {'code': '212', 'name': 'أوراق دفع (شيكات مستحقة)', 'type': 'liability', 'parent_code': '21'},
            {'code': '213', 'name': 'مصروفات مستحقة', 'type': 'liability', 'parent_code': '21'},
            {'code': '214', 'name': 'إيرادات مقبوضة مقدماً', 'type': 'liability', 'parent_code': '21'},
            {'code': '215', 'name': 'ضريبة القيمة المضافة المستحقة', 'type': 'liability', 'parent_code': '21'},
            {'code': '216', 'name': 'الضرائب على الدخل المستحقة', 'type': 'liability', 'parent_code': '21'},
            {'code': '22', 'name': 'قروض طويلة الأجل', 'type': 'liability', 'parent_code': '2'},
            {'code': '221', 'name': 'قروض بنكية طويلة الأجل', 'type': 'liability', 'parent_code': '22'},
            {'code': '222', 'name': 'قروض من مؤسسات تمويل', 'type': 'liability', 'parent_code': '22'},

            # حقوق الملكية (3)
            {'code': '3', 'name': 'حقوق الملكية', 'type': 'equity', 'parent_code': None},
            {'code': '31', 'name': 'رأس المال', 'type': 'equity', 'parent_code': '3'},
            {'code': '32', 'name': 'احتياطي قانوني', 'type': 'equity', 'parent_code': '3'},
            {'code': '33', 'name': 'أرباح محتجزة', 'type': 'equity', 'parent_code': '3'},
            {'code': '34', 'name': 'أرباح (خسائر) العام', 'type': 'equity', 'parent_code': '3'},

            # الإيرادات (4)
            {'code': '4', 'name': 'الإيرادات', 'type': 'revenue', 'parent_code': None},
            {'code': '41', 'name': 'إيرادات النشاط الرئيسي', 'type': 'revenue', 'parent_code': '4'},
            {'code': '411', 'name': 'مبيعات تامة الصنع', 'type': 'revenue', 'parent_code': '41'},
            {'code': '412', 'name': 'مبيعات مهمات وقطع غيار', 'type': 'revenue', 'parent_code': '41'},
            {'code': '413', 'name': 'مردودات المبيعات', 'type': 'revenue', 'parent_code': '41'},
            {'code': '42', 'name': 'إيرادات أخرى', 'type': 'revenue', 'parent_code': '4'},
            {'code': '421', 'name': 'إيرادات فوائد بنكية', 'type': 'revenue', 'parent_code': '42'},
            {'code': '422', 'name': 'أرباح فروق عملة', 'type': 'revenue', 'parent_code': '42'},
            {'code': '423', 'name': 'إيرادات استثنائية', 'type': 'revenue', 'parent_code': '42'},

            # تكلفة المبيعات (5)
            {'code': '5', 'name': 'تكلفة المبيعات', 'type': 'cost_of_sales', 'parent_code': None},
            {'code': '51', 'name': 'تكلفة المبيعات', 'type': 'cost_of_sales', 'parent_code': '5'},
            {'code': '52', 'name': 'مردودات المشتريات', 'type': 'cost_of_sales', 'parent_code': '5'},
            {'code': '53', 'name': 'تغير المخزون (م.م - م.أ)', 'type': 'cost_of_sales', 'parent_code': '5'},

            # المصروفات (6)
            {'code': '6', 'name': 'المصروفات', 'type': 'expense', 'parent_code': None},
            {'code': '61', 'name': 'مصروفات عمومية وإدارية', 'type': 'expense', 'parent_code': '6'},
            {'code': '611', 'name': 'مرتبات وأجور', 'type': 'expense', 'parent_code': '61'},
            {'code': '612', 'name': 'إيجارات', 'type': 'expense', 'parent_code': '61'},
            {'code': '613', 'name': 'كهرباء ومياه', 'type': 'expense', 'parent_code': '61'},
            {'code': '614', 'name': 'اتصالات (تليفون، إنترنت)', 'type': 'expense', 'parent_code': '61'},
            {'code': '615', 'name': 'صيانة', 'type': 'expense', 'parent_code': '61'},
            {'code': '616', 'name': 'مصروفات إهلاك', 'type': 'expense', 'parent_code': '61'},
            {'code': '617', 'name': 'مصروفات تسويقية وإعلانية', 'type': 'expense', 'parent_code': '61'},
            {'code': '618', 'name': 'مصروفات تدريب وبعثات', 'type': 'expense', 'parent_code': '61'},
            {'code': '619', 'name': 'مصروفات تمثيل وضيافة', 'type': 'expense', 'parent_code': '61'},
            {'code': '62', 'name': 'مصروفات تمويلية', 'type': 'expense', 'parent_code': '6'},
            {'code': '621', 'name': 'فوائد مدفوعة على قروض', 'type': 'expense', 'parent_code': '62'},
            {'code': '622', 'name': 'عمولات بنكية', 'type': 'expense', 'parent_code': '62'},
            {'code': '623', 'name': 'خسائر فروق عملة', 'type': 'expense', 'parent_code': '62'},
        ]

        # حفظ الحسابات مع الحفاظ على الهيكل الهرمي
        created_accounts = {}
        for acc_data in accounts_data:
            # البحث عن الحساب الأب
            parent = None
            if acc_data['parent_code']:
                parent = created_accounts.get(acc_data['parent_code'])
                if not parent:
                    # إذا لم يتم العثور على الأب، حاول البحث في قاعدة البيانات
                    try:
                        parent = Account.objects.get(code=acc_data['parent_code'])
                    except Account.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Parent {acc_data['parent_code']} for {acc_data['code']} not found yet."))
            
            # إنشاء الحساب
            account, created = Account.objects.get_or_create(
                code=acc_data['code'],
                defaults={
                    'name': acc_data['name'],
                    'type': acc_data['type'],
                    'parent': parent,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created account: {account.code} - {account.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Account {account.code} already exists. Skipping."))
            
            created_accounts[acc_data['code']] = account
        
        # المرحلة الثانية: ربط الحسابات التي لم يتم ربط أباؤها في المرحلة الأولى
        self.stdout.write(self.style.SUCCESS("\nUpdating missing parent relationships..."))
        for acc_data in accounts_data:
            if acc_data['parent_code']:
                try:
                    child = Account.objects.get(code=acc_data['code'])
                    if not child.parent:
                        parent = Account.objects.get(code=acc_data['parent_code'])
                        child.parent = parent
                        child.save()
                        self.stdout.write(self.style.SUCCESS(f"Linked {child.code} to parent {parent.code}"))
                except Account.DoesNotExist:
                    pass
        
        self.stdout.write(self.style.SUCCESS("\n✅ Chart of accounts seeding completed successfully!"))