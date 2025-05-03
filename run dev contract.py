# /run.py
import argparse
import os
from dotenv import load_dotenv


parser = argparse.ArgumentParser(description="Run the application with specified environment.")

parser.add_argument("--env", choices=["development", "production"], default="development", help="Specify the environment (development or production).")

args = parser.parse_args()
env_file = f"env-contract.{args.env}"

load_dotenv(os.path.join(os.getcwd(), env_file))

from app import create_app
app = create_app()
app.debug = (app.config.get('DEBUG') == 'True')

if __name__ == "__main__":
    app.run(host=app.config.get('HOST'))