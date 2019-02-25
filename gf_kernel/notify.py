import sys, signal, os, time

def main():
    """This process is called after every shell input and signals the GFRepl that the shell command is finished""" 
    time.sleep(0.2)
    os.kill(int(sys.argv[1]), signal.SIGUSR1)



if __name__ == "__main__":
    main()