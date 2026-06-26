from django.db import migrations, models
import django.db.models.deletion


def convert_hod_text_to_teacher(apps, schema_editor):
    """
    Convert existing text HOD values to Teacher foreign keys.
    Creates placeholder teachers for HODs that don't exist.
    """
    Department = apps.get_model('StudentManage_app', 'Department')
    Teacher = apps.get_model('StudentManage_app', 'Teacher')
    
    for dept in Department.objects.all():
        # Get the old text value (stored in 'hod' column before migration)
        hod_text = str(dept.hod) if dept.hod else ""
        
        if hod_text and hod_text.strip() and hod_text != "None":
            # Try to find existing teacher with this name
            teacher = Teacher.objects.filter(name__iexact=hod_text.strip()).first()
            
            if not teacher:
                # Create a placeholder teacher for this HOD
                teacher = Teacher.objects.create(
                    teacher_id=f"HOD_{dept.id:03d}",
                    name=hod_text.strip(),
                    email=f"hod{dept.id}@placeholder.com",
                    phone="0000000000",
                    qualification="",
                    experience=0,
                    department=dept,
                    status=True,
                    is_teacher_admin=False
                )
                # Set a default password
                import hashlib
                teacher.password_hash = hashlib.sha256("password123".encode()).hexdigest()
                teacher.save()
            
            # Set the new foreign key
            dept.hod_new = teacher
            dept.save()


class Migration(migrations.Migration):
    dependencies = [
        ('StudentManage_app', '0011_alter_student_created_at'),
    ]

    operations = [
        # Step 1: Rename old hod field to preserve data temporarily
        migrations.RenameField(
            model_name='department',
            old_name='hod',
            new_name='hod_old',
        ),
        
        # Step 2: Add new hod field as ForeignKey (nullable)
        migrations.AddField(
            model_name='department',
            name='hod',
            field=models.ForeignKey(
                to='StudentManage_app.teacher',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                related_name='headed_departments',
            ),
        ),
        
        # Step 3: Run data conversion
        migrations.RunPython(convert_hod_text_to_teacher),
        
        # Step 4: Remove old field
        migrations.RemoveField(
            model_name='department',
            name='hod_old',
        ),
    ]