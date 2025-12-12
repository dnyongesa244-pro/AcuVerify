from django.db import migrations, models, connection


def forwards(apps, schema_editor):
    Subject = apps.get_model('AcuVerifyapp', 'Subject')
    # The M2M through table for Subject.classes
    through = Subject.classes.through
    m2m_table = through._meta.db_table

    # Check if the old FK column 'class_id_id' exists in the subject table
    subj_table = Subject._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info('%s')" % subj_table)
        cols = [row[1] for row in cursor.fetchall()]

        if 'class_id_id' in cols:
            # Copy existing FK values into the M2M table
            cursor.execute(
                "SELECT id, class_id_id FROM %s WHERE class_id_id IS NOT NULL" % subj_table
            )
            rows = cursor.fetchall()
            if not rows:
                return

            # Insert into M2M table (subject_id, classes_id)
            # Column names depend on the through model; fetch them
            col_subj = through._meta.get_field('subject').column
            col_class = through._meta.get_field('classes').column

            for subj_id, class_id in rows:
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO %s (%s, %s) VALUES (%%s, %%s)" % (m2m_table, col_subj, col_class),
                        [subj_id, class_id]
                    )
                except Exception:
                    # If anything goes wrong for one row, continue with others
                    continue


def backwards(apps, schema_editor):
    # No real backward operation: leave M2M rows as-is
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('AcuVerifyapp', '0007_remove_subject_class_id_subject_classes'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
