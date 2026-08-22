import os
import subprocess

api_token = "fixture-secret-not-real"

def dynamic(value):
    return eval(value)

def shell(command):
    os.system(command)
    subprocess.run(command, shell=True)

def bare_handler():
    try:
        return 1 / 0
    except:
        return None

def long_function():
    values = []
    values.append(1)
    values.append(2)
    values.append(3)
    values.append(4)
    values.append(5)
    values.append(6)
    values.append(7)
    values.append(8)
    values.append(9)
    values.append(10)
    values.append(11)
    values.append(12)
    values.append(13)
    values.append(14)
    values.append(15)
    values.append(16)
    values.append(17)
    values.append(18)
    values.append(19)
    values.append(20)
    return values
