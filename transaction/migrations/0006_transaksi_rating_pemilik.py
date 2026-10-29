from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0005_transaksi_menunggu_pengambilan'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaksi',
            name='rating_pemilik',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaksi',
            name='rating_dilewati',
            field=models.BooleanField(default=False),
        ),
    ]
