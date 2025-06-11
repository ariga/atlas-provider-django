from django.db import models


class UserClone(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True)
    roll = models.CharField(max_length=100)


class BlogClone(models.Model):
    author = models.ForeignKey(UserClone, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateField()
    num_stars = models.IntegerField()
