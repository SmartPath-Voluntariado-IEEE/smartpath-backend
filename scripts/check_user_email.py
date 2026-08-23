from database.database import get_admin_client

EMAIL = "rensto56700@gmail.com"


def main():
    client = get_admin_client()
    response = client.table("users").select("*").eq("email", EMAIL).execute()

    if not response.data:
        print(f"No existe ningún usuario con email '{EMAIL}'.")
        return

    for user in response.data:
        print(user)


if __name__ == "__main__":
    main()
