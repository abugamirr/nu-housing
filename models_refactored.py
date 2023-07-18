import pandas as pd

class Dormitory:
    class Block:
        def __init__(self, number: int, room_cap_list: list[tuple[int, int]]):
            self.number = number
            self.room_cap_list = sorted(room_cap_list, key = lambda x: x[0])
        
    def __init__(self, blocks: dict[int, Block], excluded_rooms_file: str | None = None) -> None:
        self.rooms: dict[int, dict[int, Room]] = {}
        self.blocks = blocks
        
        self.excluded_rooms = set()
        if excluded_rooms_file is not None:
            df = pd.read_excel(excluded_rooms_file) # header: Block, Room
            self.excluded_rooms = set(df.iloc[:,0].astype(str) + '.' + df.iloc[:,1].astype(str))

        for block in self.blocks.values():
            self.rooms[block.number] = {}
            for room, capacity in block.room_cap_list:
                if f"{block.number}.{room}" in self.excluded_rooms:
                    continue
                self.rooms[block.number][room] = Room(room, block.number, capacity)

    def __str__(self):
        result = "Dormitory:\n"
        indent = "    "
        for block in self.rooms:
            result += f"Block {block}:\n"
            for room in self.rooms[block].values():
                result += indent + f"{room}\n"
        
        return result

class Room:
    def __init__(self, number: int, block_number: int, capacity: int = 2):
        self.number = number
        self.block_number = block_number
        self.capacity = capacity
        self.students: list[Student] = []
        self.gender: str | None = None

    def __str__(self) -> str:
        return f"Room {self.block_number}.{self.number} {self.gender}: {self.students}"
    
    def __repr__(self) -> str:
        return f"Room {self.block_number}.{self.number} {self.gender}: {self.students}"
    
    def addStudent(self, new_student: 'Student'):
        if self.capacity == 0:
            raise ValueError(f"Room {self.block_number}.{self.number} is full")
        if new_student in self.students:
            raise ValueError(f"Student {new_student.id} is already in room {self.block_number}.{self.number}")
        if self.gender is not None and self.gender != new_student.gender:
            raise ValueError(f"Student {new_student.id} has gender {new_student.gender} and it doesn't match Room {self.block_number}.{self.number} gender {self.gender}")
        
        if self.gender is None:
            self.gender = new_student.gender
        
        for habitat in self.students:
            habitat.roommates.append(new_student)
            new_student.roommates.append(habitat)
    
        new_student.room = self
        self.students.append(new_student)
        self.capacity -= 1

        print(f"{self.block_number}.{self.number}:\n    Added Student {new_student.id}")

    def deleteStudent(self, delete_student: 'Student'):
        delete_student.room = None
        
        try:
            self.students.remove(delete_student)
        except ValueError:
            raise ValueError(f"Student {delete_student.id} is not in room {self.block_number}.{self.number}")
        
        self.capacity += 1

        for habitat in self.students:
            if delete_student in habitat.roommates:
                habitat.roommates.remove(delete_student)
            if habitat in delete_student.roommates:
                delete_student.roommates.remove(habitat)

        if len(self.students) == 0:
            self.gender = None

class Student:
    def __init__(self, id: int, gender: str, degree: str | None = None, year: str | None = None, intended_roommate_ids: list[int] | None = None):
        self.id = id
        self.gender = gender
        self.degree = degree
        self.year = year
        self.intended_roommate_ids = [] if intended_roommate_ids is None else intended_roommate_ids
        self.roommates: list[Student] = []
        self.room: Room | None = None
    
    def __str__(self) -> str:
        return f"Student {self.id} {self.gender} {[roomate.id for roomate in self.roommates]}"
    
    def __repr__(self) -> str:
        return f"Student {self.id} {self.gender} {[roomate.id for roomate in self.roommates]}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Student):
            return self.id == other.id
        else:
            return False
    
    def __hash__(self) -> int:
        return hash(self.id)