from cli import create_parser, arg_controller

def main() -> None:
    args = create_parser()
    arg_controller(args)

if __name__ == '__main__':
    main()
