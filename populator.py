from typing import List, Dict
from models import Dormitory, Student
from random import shuffle
import pandas as pd
import os
class Populator:
    def __init__(self, input_name: str, dorm: Dormitory):
        self.dorm = dorm
        self.students: Dict[str, Student] = {}
        # self.read(input_name)

    def read_excel_dorm(self, input_name):
        # preprocess
        df = pd.read_excel(input_name, header = 0)
        df.columns = ['Block', 'Room', 'Id', 'Gender']
        for col in df.columns:
            df[col] = df[col].astype(str)
        df.Gender = df.Gender.map({'Female': 'Female', 'Male': 'Male'})
        df.Block = df.Block.map({'D6 (23)': '23', 'D7 (24)': '24', 'D8 (25)': '25', 'D9 (26)': '26','D10 (27)': '27'})
        
        df.Room = df.Block.astype(str) + '.' + df.Room.astype(str)

        df = df.drop(['Block'], axis = 1)

        #reading
        for _, row in df.iterrows():
            room_num = row['Room']
            id = row['Id']
            gender = row['Gender']
            
            student = Student(id = id, gender = gender)
            self.students[id] = student

            self.dorm.rooms[room_num].addStudent(student)
        
        return df

    def read_excel_students(self, input_name):
        df = pd.read_excel(input_name, header = 0)
        df.columns = ['Id', 'Gender']
        df.Gender = df.Gender.map({'Female': 'Female', 'Male': 'Male'})
        
        for _, row in df.iterrows():
            id = str(row['Id'])
            gender = str(row['Gender'])
            
            if id in self.students:
                student = self.students[id]
                if student.room is not None:
                    student.room.deleteStudent(self.students[id])
                else:
                    raise Exception("Something is wrong. Room is None!")
            else:
                self.students[id] = Student(id = id, gender = gender)
        
        students_to_accomodate = list(df.Id.astype(str))

        return students_to_accomodate
                
    def read(self, input_name):
        with open(input_name) as f:
            line = f.readline()
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip(',\n ').split(',')
                self.students[line[0]] = Student(line[0], line[1], line[2], line[3], line[4:])
                

    def match(self, A: Student, B: Student, roomate_num: int):
        roomate_is_free = (len(B.roomates) == 0)
        roomate_has_roomate_num = (len(B.roomate_ids) == roomate_num)
        
        if roomate_is_free and roomate_has_roomate_num:
            id_match = (B.roomate_ids.count(A.id) == 1) and (A.roomate_ids.count(B.id) == 1)
            gender_match = (B.gender == A.gender)
            
            # ------------------
            # Degree year match!
            # ------------------          

            if id_match and gender_match:
                return True
            else:
                return False

    def pair(self):
        for student in self.students.values():
            if len(student.roomates) != 0: continue
            
            if (len(student.roomate_ids) == 1 and 
                (student.roomate_ids[0] in self.students) and 
                (student.id != student.roomate_ids[0])):
                intended_roomate = self.students[student.roomate_ids[0]]

                if self.match(student, intended_roomate, 1):
                    student.roomates.append(intended_roomate)
                    intended_roomate.roomates.append(student)

            elif (len(student.roomate_ids) == 2 and
                  (student.roomate_ids[0] in self.students) and
                  (student.roomate_ids[1] in self.students) and 
                  len({student.id, student.roomate_ids[0], student.roomate_ids[1]}) == 3):
                
                intended_roomate1 = self.students[student.roomate_ids[0]]
                intended_roomate2 = self.students[student.roomate_ids[1]]
                
                if (self.match(student, intended_roomate1, 2) and
                    self.match(student,intended_roomate2, 2) and
                    self.match(intended_roomate1, intended_roomate2, 2)):

                    student.roomates.extend([intended_roomate1, intended_roomate2])
                    intended_roomate1.roomates.extend([intended_roomate2, student])
                    intended_roomate2.roomates.extend([intended_roomate1, student])
            
            elif (len(student.roomate_ids) == 3 and 
                  (student.roomate_ids[0] in self.students) and 
                  (student.roomate_ids[1] in self.students) and
                  (student.roomate_ids[2] in self.students) and
                  len({student.id, student.roomate_ids[0], student.roomate_ids[1], student.roomate_ids[2]}) == 4
                  ):
                
                intended_roomate1 = self.students[student.roomate_ids[0]]
                intended_roomate2 = self.students[student.roomate_ids[1]]
                intended_roomate3 = self.students[student.roomate_ids[2]]
                
                if (self.match(student, intended_roomate1, 3) and 
                    self.match(student,intended_roomate2, 3) and 
                    self.match(student,intended_roomate3, 3) and 
                    self.match(intended_roomate1, intended_roomate2, 3) and
                    self.match(intended_roomate1, intended_roomate3, 3) and
                    self.match(intended_roomate2, intended_roomate3, 3)
                    ):

                    student.roomates.extend([intended_roomate1, intended_roomate2, intended_roomate3])
                    intended_roomate1.roomates.extend([intended_roomate2, intended_roomate3, student])
                    intended_roomate2.roomates.extend([intended_roomate1, intended_roomate3, student])
                    intended_roomate3.roomates.extend([intended_roomate1, intended_roomate2, student])
                    
            if len(student.roomates) == 0:
                self.selfdestruction(student)

    def selfdestruction(self, dummy):
        if len(dummy.roomate_ids) == 0:
            return
        
        ls = dummy.roomate_ids.copy()
        dummy.roomate_ids = []

        for dummy_ids in ls:
            dummy_friend = self.students.get(dummy_ids)
            if dummy_friend != None and len(dummy_friend.roomate_ids) != 0 and dummy_friend.roomate_ids.count(dummy.id) > 0:
                self.selfdestruction(dummy_friend)

   
    def populate(self, students_list: List[str], rooms_list: List[str], randomize = True):
        if randomize:
            shuffle(rooms_list) 
        
        self.populate_gender([male_id for male_id in students_list if self.students[male_id].gender == 'Male'], rooms_list)
        self.populate_gender([female_id for female_id in students_list if self.students[female_id].gender == 'Female'], rooms_list)
        

        # Can comment this out because added this to Room.addStudent
        for room_num in rooms_list:
            room = self.dorm.rooms[room_num]
            for habitant in room.students:
                st = set(room.students)
                st.discard(habitant)
                habitant.roomates = list(st)
        
        not_accommodated = []
        for student_id in students_list:
            student = self.students[student_id]
            if student.room is None:
                not_accommodated.append(student_id)
        print("Were not accommodated:", not_accommodated)

    def populate_gender(self, students_list: List[str], rooms_list: List[str]):
        students_list.sort(key = lambda id: len(self.students[id].roomates), reverse = True)
        
        for student_id in students_list:
            student = self.students[student_id]
            
            if student.room is not None: continue

            group_len = len(student.roomates) + 1

            best_room = None
            for room_num in rooms_list:
                room = self.dorm.rooms[room_num]
                
                if room.gender is not None and room.gender != student.gender: continue

                if room.capacity >= group_len and (best_room is None or room.capacity < best_room.capacity):
                    best_room = room
                
            if best_room is not None:
                best_room.addStudent(student)
            
                for roomate in student.roomates:
                    best_room.addStudent(roomate)

    def to_csv(self, dir_name: str, file_name: str):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        path = os.path.join(dir_name, file_name)
        
        f = open(path, "w")
        f.write("block,room,id,gender\n")
        for room in self.dorm.rooms.values():
            for i in range(len(room.students)):
                s = room.students[i]
                f.write(f"{room.number[0:2]},{room.number[3:]},{s.id},{s.gender}\n")
        f.close()

        return pd.read_csv(path)
    
    def upload_csv(self, dir_name: str, file_name: str, student_ids: List[str] | None = None):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        path = os.path.join(dir_name, file_name)
        
        f = open(path, "w")
        f.write("ID card/Номер ID карты*,IIN/ИИН**,Lastname/Фамилия***,Firstname/Имя***,Complex/Комплекс*,Bulding (Block)/Блок*,Object number/Номер объекта*,Place number/Номер места*,Start date/Дата заселения*,End date/Дата выселения*,Comment/Комментарий,Reasons for accomodation/Основание заселения,Type of accomodation/Тип заселения*,Number of the agreement/Номер договора,Date of the agreement/Дата договора,Cost of living/Стоимость проживания,Discount/Скидка\n")
        for room in self.dorm.rooms.values():
            for i in range(len(room.students)):
                s = room.students[i]
                if student_ids is not None:
                    if s.id not in student_ids: continue
                f.write(f"{s.id},,,,Блок {room.number[0:2]},Блок {room.number[0:2]},{room.number[3:]},{i+1},,,,,,,,,\n")
        f.close()

    def __del__(self):
        self.to_csv('dorm', 'db')

    
        

            
                    

                
                


            



        



        

            

            




            

            












