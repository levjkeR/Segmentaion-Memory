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
import os

init(autoreset=True)  # colorama init

MEMORY_SIZE = 63


def create_task(name, size):
    with open(name, "wb") as task_file:
        task_file.seek(size - 1)
        task_file.write(b'\0')


def check_for_range(first_range_max, second_range_min):
    if second_range_min - first_range_max == 1:
        return None
    if first_range_max + 1 == second_range_min - 1:
        return [second_range_min - 1]
    return [first_range_max + 1, second_range_min - 1]


class Memory:
    def __init__(self):
        self.size = MEMORY_SIZE
        self.memory = list(hex(0) for i in range(MEMORY_SIZE))

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

    def write(self, offset, str_data):
        if offset >= self.size:
            print("[!] Выход за пределы адресного пространства памяти")
            return
        if offset + len(str_data) > self.size:
            print(
                Fore.RED + f"[!] Выход за пределы адресного пространства памяти!\n"
                + f"\t\tНевозможно прочитать {Fore.LIGHTGREEN_EX + hex(self.size)}")
            return
        for i in range(len(str_data)):
            self.memory[offset + i] = str_data[i]


class Segment:
    def __init__(self, name, start, size):
        self.name = name
        self.start = start
        self.size = size

    def load_segment(self, memory):
        pass

    def unload_segment(self, memory):
        pass


class Process:
    def __init__(self, name, size):
        self.segments = {}
        self.name = name
        self.size = size
        self.segments_table = {}

    def add_segment(self, name, start, size):
        for i in self.segments:
            if i.name == name:
                print(Fore.LIGHTBLUE_EX + f"[-] Имя сегмента '{Fore.LIGHTGREEN_EX + name + Fore.LIGHTBLUE_EX}'\n"
                                          f"для процесса {Fore.LIGHTGREEN_EX + self.name + Fore.LIGHTBLUE_EX} занято!")
                return False
        if size > self.size:
            print(
                Fore.RED + f"[-] Размер сегмента больше допустимого!")
            return False

        if start + size > self.size:
            print(
                Fore.RED + f"[!] Выход за пределы адресного пространства памяти!\n"
                + f"\t\tНевозможно писать по адресу {Fore.LIGHTGREEN_EX + hex(start + size)}")
            return False

        for i in self.segments.values():
            if start in range(i.start, i.start + i.size) or size in range(i.start, i.start + i.size):
                print(
                    Fore.LIGHTBLUE_EX + f"[-] Вхождение в имющийся сегмент!\n"
                    + f"\t\t{Fore.LIGHTGREEN_EX} {[i.name, i.start, i.start + i.size]}")
                return False

        self.segments[name] = (Segment(name, start, size))
        self.segments_table[name] = {'start': start, 'size': size}
        return True

    def get_undistributed_addresses(self):
        undistributed_addresses = []
        addr_ranges = sorted([i for i in [[x['start'], x['start'] + x['size'] - 1]
                                          for x in list(self.segments_table.values())]])
        for i in range(len(addr_ranges) - 1):
            free_range = check_for_range(addr_ranges[i][1], addr_ranges[i + 1][0])
            if undistributed_addresses is not None:
                undistributed_addresses.append(free_range)

        if addr_ranges[0][0] != 0:
            if addr_ranges[0][0] - 1 == 0:
                undistributed_addresses.append([0])
            else:
                undistributed_addresses.append([0, addr_ranges[0][0] - 1])
        if addr_ranges[-1][1] < self.size:
            if addr_ranges[-1][1] + 1 == self.size:
                undistributed_addresses.append([self.size])
            else:
                undistributed_addresses.append([addr_ranges[-1][1] + 1, self.size])
        return undistributed_addresses

    def get_segment(self, name):
        try:
            return self.segments_table[name]
        except KeyError:
            print(Fore.RED + f"[!] Нет сегмента с именем {Fore.LIGHTYELLOW_EX + name}")


class MemoryManager:
    memory = Memory()

    def __init__(self):
        self.processes = []

    def add_process(self, name, segments_count):
        size = os.path.getsize(name)
        if size > MEMORY_SIZE - 1:
            print(
                Fore.RED + f"[!] Размер задачи выше максимального! "
                           f"{Fore.LIGHTYELLOW_EX + str(size) + Fore.RED} > {Fore.RESET + str(MEMORY_SIZE)}")
            return False
        self.processes = Process(name, segments_count)
        return True

