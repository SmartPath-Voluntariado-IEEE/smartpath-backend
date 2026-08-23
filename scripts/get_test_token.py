from database.database import get_admin_client, supabase_client

EMAIL = "rensto56700@gmail.com"
TEMP_PASSWORD = "SmartPathTest#2026"

def main():
    admin = get_admin_client()

    users = admin.auth.admin.list_users()
    user = next((u for u in users if u.email == EMAIL), None)

    if not user:
        print(f"No existe un usuario de Auth con email '{EMAIL}'.")
        return

    admin.auth.admin.update_user_by_id(
        user.id,
        {"password": TEMP_PASSWORD},
    )

    session = supabase_client.auth.sign_in_with_password(
        {"email": EMAIL, "password": TEMP_PASSWORD}
    )

    print(f"user_id: {user.id}")
    print(f"password temporal: {TEMP_PASSWORD}")
    print(f"access_token:\n{session.session.access_token}")


if __name__ == "__main__":
    main()
