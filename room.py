class Room:

    def __init__(self, number: int, capacity = 2) -> None:
        self.number = number
        self.students = []
        self.capacity = capacity
        self.gender = None

    def __str__(self) -> str:
        return f"Room {self.room_number} {self.gender}: {self.students}"

    def __repr__(self) -> str:
        return f"Room {self.room_number} {self.gender}: {self.students}"

    def addStudent(self, newStudent):
        newStudent.setRoom(self)
        self.students.append(newStudent)


