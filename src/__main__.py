from .settings import get_settings


def main() -> None:
    settings = get_settings()
    print(f"PlantOps scaffold loaded (env={settings.environment})")


if __name__ == "__main__":
    main()
