# run.py
import argparse
import os
from dotenv import load_dotenv


parser = argparse.ArgumentParser(description="Run the application with specified environment.")
# 添加--env参数，默认值为development
parser.add_argument("--env", choices=["development", "production"], default="development", help="Specify the environment (development or production).")
# 解析命令行参数
args = parser.parse_args()
env_file = f"env.{args.env}"

# 根据参数加载环境变量
load_dotenv(os.path.join(os.getcwd(), env_file))

# 初始化应用
from app import create_app
app = create_app()
app.debug = (app.config.get('DEBUG') == 'True')

if __name__ == "__main__":
    app.run(host=app.config.get('HOST'))