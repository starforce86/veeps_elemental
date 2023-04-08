#!/usr/bin/env python
import os
import sys
import django


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    current_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_path)
    sys.path.append(os.path.join(current_path, "apps"))

    django.setup()

    from apps.users.models import User
    from rest_framework.authtoken.models import Token
    from config.settings import API_AUTH_KEY

    arguments = sys.argv

    usage = "Usage: ./createsuperuser <email> <password>"

    if "-h" in arguments or "--help" in arguments:
        print(usage)
        print("   NOTE: this will only create the first superuser, if a superuser already exists, it will exit")
        exit()

    if len(arguments) < 3:
        raise ValueError(usage)

    username = arguments[1]
    password = arguments[2]

    if "@" not in username:
        print(f"'{username}' doesn't appear to be an email")
        exit()

    existing_superuser = User.objects.filter(is_superuser=True).first()

    if existing_superuser is not None:
        print("A superuser already exists")
        exit()

    new_user = User.objects.create(
        email=username,
        is_admin=True,
        is_superuser=True,
    )
    new_user.save()
    new_user.set_password(password)

    token = Token.objects.create(
        user=new_user,
        key=API_AUTH_KEY,
    )

    # this shouldn't be necessary, but for good measure, save everything.
    new_user.save()
    token.save()
