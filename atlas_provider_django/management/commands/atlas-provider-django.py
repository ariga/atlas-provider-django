from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import Django migrations into Atlas"

    def handle(self, *args, **options):
        pass
