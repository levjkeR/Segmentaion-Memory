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

MEMORY_SIZE = 64


def read_data(filename, start, size):
    with open(filename, 'rb') as file:
        file.seek(start)
        data = file.read(size)
    return data


def create_task(name, size):
    with open(name, "wb") as task_file:
        # task_file.seek(size - 1)

        task_file.write(bytes([i for i in range(size-1)]))
        task_file.write(b'\0')


def check_for_range(first_range_max, second_range_min):
    if second_range_min - first_range_max == 1:
        return None
    if first_range_max + 1 == second_range_min - 1:
        return [second_range_min - 1]
    return [first_range_max + 1, second_range_min - 1]


def get_free_addresses(size, addr_ranges):
    undistributed_addresses = []
    # print("--", len(addr_ranges), addr_ranges)
    if len(addr_ranges) < 1:
        return [[0, size]]

    for i in range(len(addr_ranges) - 1):
        free_range = check_for_range(addr_ranges[i][1], addr_ranges[i + 1][0])
        if free_range is None:
            return None
        undistributed_addresses.append(free_range)

    if addr_ranges[0][0] != 0:
        if addr_ranges[0][0] - 1 == 0:
            undistributed_addresses.append([0])
        else:
            undistributed_addresses.append([0, addr_ranges[0][0] - 1])
    if addr_ranges[-1][1] < size:
        if addr_ranges[-1][1] + 1 == size:
            undistributed_addresses.append([size])
        else:
            undistributed_addresses.append([addr_ranges[-1][1] + 1, size])
    return undistributed_addresses if len(undistributed_addresses) > 0 else None


class Memory:
    def __init__(self):
        self.size = MEMORY_SIZE
        self.memory = list('NaN' for i in range(MEMORY_SIZE))

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
            return False
        if offset + len(str_data) > self.size:
            print(
                Fore.RED + f"[!] Выход за пределы адресного пространства памяти!\n"
                + f"\t\tНевозможно прочитать {Fore.LIGHTGREEN_EX + str(self.size)}")
            return False
        for i in range(len(str_data)):
            self.memory[offset + i] = str_data[i]
        return True


class Segment:
    def __init__(self, name, start, size):
        self.name = name
        self.start = start
        self.size = size
        self.state = 0


class Process:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.segments_table = {}  # {"example": seg}

    def add_segment(self, name, start, size):
        if sum(x.size for x in self.segments_table.values()) == self.size:
            print(Fore.LIGHTMAGENTA_EX + f"[x] Вся память процесса размечена на сегменты!")
            print('\t\t\t\t' + Fore.LIGHTYELLOW_EX + ', '.join(self.segments_table.keys()))
            return False
        if name in self.segments_table.keys():
            print(Fore.LIGHTBLUE_EX + f"[-] Имя сегмента '{Fore.LIGHTGREEN_EX + name + Fore.LIGHTBLUE_EX}' "
                                      f"для процесса '{Fore.LIGHTGREEN_EX + self.name + Fore.LIGHTBLUE_EX}' занято!")
            return False

        if size > self.size:
            print(Fore.RED + f"[-] Размер сегмента больше допустимого!")
            return False

        if start + size - 1 > self.size:
            print(
                Fore.RED + f"[!] Выход за пределы адресного пространства памяти!\n"
                + f"\t\tНевозможно писать по адресу {Fore.LIGHTGREEN_EX + str(start + size)}")
            return False

        for i in self.segments_table.values():
            print(start, start+size, i.start, i.start + i.size)
            if start in range(i.start+1, i.start + i.size) or start+size in range(i.start+1, i.start + i.size):
                print(
                    Fore.LIGHTBLUE_EX + f"[-] Вхождение в имющийся сегмент!\n"
                    + f"\t\t{Fore.LIGHTGREEN_EX} {[i.name, i.start, i.start + i.size]}")
                return False
        self.segments_table[name] = Segment(name, start, size)
        return True

    def get_undistributed_addresses(self):
        addr_ranges = sorted([i for i in [[x.start, x.start + x.size-1]
                                          for x in list(self.segments_table.values())]])
        return get_free_addresses(self.size, addr_ranges)

    def get_segment(self, name):
        try:
            return self.segments_table[name]
        except KeyError:
            print(Fore.RED + f"[!] Нет сегмента с именем {Fore.LIGHTYELLOW_EX + name}")


class MemoryManager:
    def __init__(self):
        self.processes_table = {}
        self.phys_memory_table = {}  # {'segment_name': [start, size]}
        self.memory = Memory()

    def add_process(self, name):
        size = os.path.getsize(name)
        if size > MEMORY_SIZE - 1:
            print(
                Fore.RED + f"[!] Размер задачи выше максимального! "
                           f"{Fore.LIGHTYELLOW_EX + str(size) + Fore.RED} > {Fore.RESET + str(MEMORY_SIZE-1)}")
            return False

        self.processes_table[name] = Process(name, size)
        return True

    def get_free_memory(self):
        usage_addr_ranges = sorted([i for i in [[x[0], x[0] + x[1]]
                                                for x in list(self.phys_memory_table.values())]])
        return get_free_addresses(MEMORY_SIZE, usage_addr_ranges)

    def load_segment(self, process_name, segment_name):
        if process_name not in self.processes_table.keys():
            print(Fore.RED + f"[!] Неверное имя процесса")
            return False
        process = self.processes_table[process_name]
        if segment_name not in process.segments_table.keys():
            print(Fore.RED + f"[!] Неверное имя сегмента")
            return False

        segment = process.segments_table[segment_name]
        phys_addr = None
        free = self.get_free_memory()
        print(free)
        for i in free:
            print(i)
            if i[1] - i[0] + 1 >= segment.size:
                phys_addr = i
                print(Fore.LIGHTGREEN_EX + f"[+] Успех! Выделение места для сегмента " \
                                           f"'{Fore.CYAN + segment.name + Fore.LIGHTGREEN_EX}' в физической памяти "
                                           f"{Fore.BLUE + str(i)}")
                break
        if phys_addr is None:
            print(Fore.LIGHTYELLOW_EX + f"[x] В данный момент нет места для сегмента '{Fore.CYAN + segment.name}'")
            return False

        self.phys_memory_table[', '.join([process_name, segment_name])] = phys_addr

        segment_data = read_data(process_name, segment.start, segment.size)
        if self.memory.write(phys_addr[0], segment_data):
            segment.state = 1
            print(Fore.LIGHTGREEN_EX + f"[+] Успех! Загружен в память, область "
                                       f"({Fore.CYAN + hex(phys_addr[0]) + Fore.LIGHTGREEN_EX}"
                                       f":{Fore.CYAN + hex(phys_addr[1])})")
            return True

    def unload_segment(self):
        pass



