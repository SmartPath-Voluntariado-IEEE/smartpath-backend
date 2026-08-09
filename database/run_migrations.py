import os
import sys

import psycopg2
from dotenv import load_dotenv

dir_actual = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(dir_actual, "..", ".env.local")
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL", "")

def run():
    # Comprobar si se ha pasado el flag --reset
    hacer_reset = "--reset" in sys.argv

    root_dir = os.path.dirname(os.path.dirname(dir_actual))
    envs_path = os.path.join(root_dir, "envs")

    password = None
    if os.path.exists(envs_path):
        with open(envs_path, encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                password = lines[1].strip()

    if not password:
        password = ".BZ%JH3SrMzY-tS"

    project_ref = None
    if supabase_url:
        project_ref = supabase_url.replace("https://", "").split(".")[0]

    if not project_ref:
        project_ref = "izjoapkmshybyxpplxfr"

    host = f"db.{project_ref}.supabase.co"
    database = "postgres"
    user = "postgres"
    port = "5432"

    print(f"Conectando a {host}:{port} en la base de datos '{database}'...")
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        conn.autocommit = True
        cur = conn.cursor()

        # 1. Ejecutar reset.sql si se solicita
        if hacer_reset:
            reset_path = os.path.join(dir_actual, "reset.sql")
            print(f"Limpiando base de datos con {reset_path}...")
            with open(reset_path, encoding="utf-8") as f:
                reset_sql = f.read()
            cur.execute(reset_sql)
            print("¡Base de datos limpiada con éxito!")

        # 2. Ejecutar schema.sql
        schema_path = os.path.join(dir_actual, "schema.sql")
        print(f"Leyendo y aplicando {schema_path}...")
        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()
        cur.execute(schema_sql)
        print("¡Esquema de base de datos creado exitosamente!")

        # 3. Ejecutar seed.sql
        seed_path = os.path.join(dir_actual, "seed.sql")
        print(f"Leyendo y aplicando {seed_path}...")
        with open(seed_path, encoding="utf-8") as f:
            seed_sql = f.read()
        cur.execute(seed_sql)
        print("¡Datos semilla cargados exitosamente!")

        # 4. Recargar caché de PostgREST
        print("Recargando caché de PostgREST...")
        cur.execute("NOTIFY pgrst, 'reload schema';")
        print("¡Notificación de recarga de esquema enviada exitosamente!")

        cur.close()
        conn.close()
        print("¡Proceso de migración finalizado con éxito!")
    except Exception as e:
        print(f"Error al ejecutar la migración: {e}")

if __name__ == "__main__":
    run()
