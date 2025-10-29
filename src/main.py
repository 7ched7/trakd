from manager.cli import CliManager
from client import Client
from server import Server

def main() -> None:
    client = Client() 
    server = Server()
    cli_manager = CliManager(client=client, server=server)

    args = cli_manager.create_parser() 
    cli_manager.arg_controller(args)

if __name__ == '__main__':
    main()
