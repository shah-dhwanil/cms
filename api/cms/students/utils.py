from cms.utils.config import Config


def generate_enrollment_no(
    code: str, year: int, name: str, program_name: str, serial_no: int
) -> str:  # noqa
    Config.load_config()
    enrollment_fmt = Config.get_config().ENROLLMENT_NO_FORMAT
    return eval(f"f'{enrollment_fmt}'")
