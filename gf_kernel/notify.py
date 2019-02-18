import sys, signal, os, time

def main():
    time.sleep(0.2)
    os.kill(int(sys.argv[1]), signal.SIGUSR1)



if __name__ == "__main__":
    main()