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
from colorama import init, Fore
import os

init(autoreset=True)  # colorama init

MEMORY_SIZE = 64


def read_data(filename, start, size):
    with open(filename, 'rb') as file:
        file.seek(start, 0)
        data = file.read(size)
    return data


def create_task(name, size):
    with open(name, "wb") as task_file:
        # task_file.seek(size - 1)
        task_file.write(bytes([65 for i in range(size)]))
        # task_file.write(bytes([i + 65 for i in range(size)]))
        # task_file.write(b'\0')


def check_for_range(first_range_max, second_range_min):
    if second_range_min - first_range_max == 1:
        return None
    if first_range_max + 1 == second_range_min - 1:
        return [second_range_min]
    return [first_range_max + 1, second_range_min - 1]


def search_ranges(size, addr_ranges):
    undistributed_addresses = []

    if len(addr_ranges) < 1:
        return [[0, size]]

    for i in range(len(addr_ranges) - 1):
        free_range = check_for_range(addr_ranges[i][1], addr_ranges[i + 1][0])
        if free_range is not None:
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

# Низший уровень(физический)
class Memory:
    def __init__(self):
        self.__memory = list('NaN' for i in range(MEMORY_SIZE))

    # Чтение памяти по адресу и размеру
    def read(self, address, bytes_count=1):
        if address + bytes_count > MEMORY_SIZE:
            print(
                Fore.RED + f"[!] Выход за пределы адресного пространства памяти!\n"
                + f"\t\tНевозможно прочитать по адресу больше чем {Fore.LIGHTGREEN_EX + str(MEMORY_SIZE)}")
            return
        data = []
        for i in range(bytes_count):
            data.append(self.__memory[address + i])
        return data

    # Запись в память массива байтов по адресу
    def write(self, base_address, byte_arr):
        if base_address >= MEMORY_SIZE:
            print("[!] Выход за пределы адресного пространства памяти")
            return False
        if base_address + len(byte_arr) > MEMORY_SIZE:
            print(
                Fore.RED + f"[!] Выход за пределы адресного пространства памяти!\n"
                + f"\t\tНевозможно прочитать по адресу больше чем {Fore.LIGHTGREEN_EX + str(MEMORY_SIZE)}")
            return False
        for i in range(len(byte_arr)):
            self.__memory[base_address + i] = byte_arr[i]
        return True

# Сегмент памяти процесса
class Segment:
    def __init__(self, name, start, size):
        self.name = name
        self.start = start
        self.size = size
        self.is_load = False

    def __str__(self):
        return f"name: {self.name}\nbase: {self.start}\nsize: {self.size}\nis_load: {self.is_load}"
    # def get_info(self):
    #     return {'name': self.name,
    #             'base': self.start,
    #             'size': self.size,
    #             'is_load'}

# Процесс(Виртуальная память представлена файлом задачи)
class Process:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.segments_table = {}  # {"example": obj}

    # Добавление сегмента в таблицу процесса
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
            if start in range(i.start + 1, i.start + i.size) or start + size in range(i.start + 1, i.start + i.size):
                print(
                    Fore.LIGHTBLUE_EX + f"[-] Вхождение в имющийся сегмент!\n"
                    + f"\t\t{Fore.LIGHTGREEN_EX} {[i.name, i.start, i.start + i.size]}")
                return False
        self.segments_table[name] = Segment(name, start, size)
        return True

    # Получить нераспределенную память процесса | НЕ ВЫГРУЖАТЬ ИЗ ПУЛА В ПАМЯТЬ ПРИ НЕ РАСПРЕД. УЧАСТКАХ!
    def get_undistributed_addresses(self):

        addr_ranges = sorted([i for i in [[x.start, x.start + x.size - 1]
                                          for x in list(self.segments_table.values())]])
        return search_ranges(self.size-1, addr_ranges)

    # Размер всех сегментов | для контроля памяти процессф
    def _get_segments_size(self):
        return sum([i.size for i in self.segments_table.values()])

    # Получение объекта сегмента по имени
    def _get_segment(self, name):
        try:
            return self.segments_table[name]
        except KeyError:
            print(Fore.RED + f"[!] Нет сегмента с именем {Fore.LIGHTYELLOW_EX + name}")

# Менелжер памяти
class MemoryManager:
    def __init__(self):
        self.memory = Memory()
        self.processes_table = {}
        self.phys_memory_table = {}  # {'segment_name': [base, size]}

    # Добавить процесс(задачу) | ИМЯ ЭТО НАЗВАНИЕ ФАЙЛА
    def add_process(self, name):
        size = os.path.getsize(name)
        if size > MEMORY_SIZE - 1:
            print(
                Fore.RED + f"[!] Размер задачи выше максимального! "
                           f"{Fore.LIGHTYELLOW_EX + str(size) + Fore.RED} > {Fore.RESET + str(MEMORY_SIZE - 1)}")
            return False

        self.processes_table[name] = Process(name, size)
        return True

    # Получить диапозоны свободной памяти
    def _free_memory_ranges(self):
        usage_addr_ranges = sorted([i for i in [[x[0], x[0] + x[1] - 1]
                                                for x in list(self.phys_memory_table.values())]])
        usage_addr_ranges = list(dict.fromkeys([tuple(x) for x in usage_addr_ranges]))
        return search_ranges(MEMORY_SIZE-1, usage_addr_ranges)

    # поиск совпадения в физицеской памяти
    def __find_match(self, bytes_arr, size):
        for seg_name, info in self.phys_memory_table.items():
            # найден по размеру
            if info[1] == size:
                match_bytes = bytes(self.memory.read(info[0], info[1]))
                if match_bytes == bytes_arr:
                    return seg_name, info

    # Получение процесса по имени
    def _get_process(self, name):
        try:
            return self.processes_table[name]
        except KeyError:
            print(Fore.RED + f"[!] Нет процесса с именем {Fore.LIGHTYELLOW_EX + name}")
            return

    # Поиск оптимальной области в физической памяти
    def __find_optimal(self, size):
        free_rng = self._free_memory_ranges()
        if free_rng is not None:
            searched = [[info[0], size] for info in free_rng if info[1] >= size]
            return searched[0] if len(searched) else None

    # Загрузка сегмента в паямять по имени процесса и сегмента
    def load_segment(self, process_name, segment_name):
        prosess = self._get_process(process_name)
        if prosess is None:
            return False

        if prosess._get_segments_size() < prosess.size:
            print(f"{Fore.RED}[!] Не вся память процесса '{process_name}' распреределена"
                  f"\n\t{prosess.get_undistributed_addresses()}")
            return False

        segment = prosess._get_segment(segment_name)
        if segment is None:
            return False

        segment_data = read_data(process_name, segment.start, segment.size)
        match = self.__find_match(segment_data, segment.size)

        if match:
            print(f"[+] Обнаружен сегмент, который уже выгружен. Изменение таблицы памяти"
                  f"\n\t\t\tСегмент '{segment.name}' == сегменту '{match[0].split(', ')[1]}' "
                  f"процесса '{match[0].split(', ')[0]}'")
            self.phys_memory_table[', '.join([process_name, segment_name])] = self.phys_memory_table[match[0]]
            segment.is_load = True
            return True

        phys_addr = self.__find_optimal(segment.size)
        if phys_addr is None:
            print(Fore.LIGHTYELLOW_EX + f"[x] В данный момент нет места для сегмента '{Fore.CYAN + segment.name}'")
            return False
        else:
            print(Fore.LIGHTGREEN_EX + f"[+] Успех! Выделение места для сегмента " \
                                       f"'{Fore.CYAN + segment.name + Fore.LIGHTGREEN_EX}' в физической памяти "
                                       f"{Fore.BLUE + str(phys_addr[1])} byte")

        self.phys_memory_table[', '.join([process_name, segment_name])] = phys_addr
        if self.memory.write(phys_addr[0], segment_data):
            segment.is_load = True
            print(Fore.LIGHTGREEN_EX + f"[+] Успех! Загружен в память, область "
                                       f"{Fore.CYAN + '[' +str(phys_addr[0])}:"
                                       f"{Fore.CYAN + str(phys_addr[1] + phys_addr[0] - 1)}]")
            return True

    # Выгрузить сегмент из памяти
    def unload_segment(self, process_name, segment_name):
        prosess = self._get_process(process_name)
        if prosess is None:
            return False

        segment = prosess._get_segment(segment_name)
        if segment is None:
            return False
        key = f'{process_name}, {segment_name}'
        relation = [i for i in self.phys_memory_table if self.phys_memory_table[i] == self.phys_memory_table[key]]
        if len(relation) > 1:
            print(f"{Fore.LIGHTGREEN_EX} [+] Сегменты {relation} разделены, {[key]} "
                  f"выгружается без освобождения физического диапазона...")
            self.phys_memory_table.pop(key)
            segment.is_load = False
            print(f"{Fore.LIGHTGREEN_EX} [+] Выгружен")
            return True
        phys_segment_area = self.phys_memory_table[key]
        print(f"{Fore.LIGHTGREEN_EX} [+] Сегмент распологается в области "
              f"[{phys_segment_area[0], phys_segment_area[0]+ phys_segment_area[1]-1}] выгружается...")
        self.phys_memory_table.pop(key)
        segment.is_load = False
        print(f"{Fore.LIGHTGREEN_EX} [+] Выгружен")
        return True
