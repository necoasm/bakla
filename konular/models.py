from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Konu(models.Model):
    title = models.CharField(max_length=100, unique=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    favorited_by = models.ManyToManyField(User, related_name='favorite_topics', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    def __str__(self): return self.title
