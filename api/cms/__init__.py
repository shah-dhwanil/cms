from cms.utils.config import Config
def main() -> None:
    Config.load_config()
    print(Config.get_config())
    print("Hello from cms!")
