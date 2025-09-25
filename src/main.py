from cli import CliManager
from client import Client
from server import Server

def main() -> None:
    client = Client() 
    server = Server()
    cli_manager = CliManager(client=client, server=server)

    args = cli_manager.create_parser() # parse command-line arguments
    cli_manager.arg_controller(args) # delegate commands based on parsed arguments

if __name__ == '__main__':
    main()
