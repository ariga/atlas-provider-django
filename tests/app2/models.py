from django.db import models


class User(models.Model):
    Rolls = {"student": "student", "teacher": "teacher"}
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True)
    roll = models.CharField(choices=Rolls, max_length=10, default=Rolls["student"])


class Blog(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateField()
    num_stars = models.IntegerField()
