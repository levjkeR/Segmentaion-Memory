"""
    Разработать программу, моделирующую один из алгоритмов управления памятью в
    соответствии с вариантом задания. При моделировании считать что:
        - объем моделируемой «памяти» составляет 64К;
        - поступаемые на выполнение задачи содержатся в файлах, которые пользователь
        может «загружать» в моделируемую «память» и выгружать из нее (файл
        моделирует лишь размер задачи);
        - размер задачи в диапазоне от 0 до 65535 байт.
    Программа должна иметь возможность просмотра состояния моделируемой
    «памяти».
"""
from colorama import init
from colorama import Fore, Back, Style

init(autoreset=True)  # colorama init


def create_task(name, size):
    with open(name, "wb") as task_file:
        task_file.seek(size - 1)
        task_file.write(b'\0')


class Memory:
    def __init__(self, size):
        self.size = size
        # self.memory = [0]*self.size
        self.memory = range(size)

    def read(self, offset, n=1):
        if offset + n > self.size:
            print(
                Fore.RED + f"[!] Выход за пределы адресного пространства памяти!\n"
                + f"\t\tНевозможно прочитать {Fore.LIGHTGREEN_EX + hex(self.size)}")
            return
        memory = []
        for i in range(n):
            memory.append(self.memory[offset + i])
        return memory

    def write(self, offset):
        if offset + n > self.size:
            print("[!] Выход за пределы адресного пространства памяти")
            return


class MemoryManager:
    pass


m = Memory(10)

print(list(m.memory))
print(m.read(10))
