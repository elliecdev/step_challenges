from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("steps", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="stepentry",
            old_name="total_steps",
            new_name="daily_steps",
        ),
    ]

