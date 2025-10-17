from django.core.management.base import BaseCommand
from downloader.models import TelegramUser
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Register a Telegram user with phone number'

    def add_arguments(self, parser):
        parser.add_argument('telegram_id', type=int, help='Telegram user ID')
        parser.add_argument('phone_number', type=str, help='Phone number with country code')
        parser.add_argument('--first_name', type=str, help='First name', default='')
        parser.add_argument('--last_name', type=str, help='Last name', default='')
        parser.add_argument('--username', type=str, help='Telegram username', default='')

    def handle(self, *args, **options):
        telegram_id = options['telegram_id']
        phone_number = options['phone_number']
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        username = options.get('username', '')

        try:
            # Check if user already exists
            if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
                # Update existing user
                telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
                telegram_user.phone_number = phone_number
                if first_name:
                    telegram_user.first_name = first_name
                if last_name:
                    telegram_user.last_name = last_name
                if username:
                    telegram_user.username = username
                telegram_user.save()
                
                # Update Django user
                django_user = telegram_user.user
                if first_name:
                    django_user.first_name = first_name
                if last_name:
                    django_user.last_name = last_name
                django_user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Telegram user {telegram_id} with phone {phone_number}')
                )
            else:
                # Create new user
                # Create Django user
                django_username = f"user_{phone_number.replace('+', '').replace('-', '').replace(' ', '')}"
                counter = 1
                while User.objects.filter(username=django_username).exists():
                    django_username = f"user_{phone_number.replace('+', '').replace('-', '').replace(' ', '')}_{counter}"
                    counter += 1

                django_user = User.objects.create_user(
                    username=django_username,
                    first_name=first_name or phone_number,
                    last_name=last_name,
                    email=f"{django_username}@telegram.local"
                )

                # Create Telegram user
                telegram_user = TelegramUser.objects.create(
                    user=django_user,
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    is_verified=True
                )

                self.stdout.write(
                    self.style.SUCCESS(f'Created new Telegram user {telegram_id} with phone {phone_number}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error registering user: {str(e)}')
            )