from models_refactored import *
from random import shuffle
import pandas as pd
class Populator:
	def __init__(self, dorm: Dormitory):
		self.dorm = dorm
		self.students: dict[int, Student] = {}
	
	def update_dorm(self, dorm_input_file):
		df = pd.read_excel(dorm_input_file) # Header: Block, Room, ID, Gender, Degree, Year
		if df.shape[1] != 6:
			raise ValueError(f'Number of columns should be 6')
		
		df.columns = ['Block', 'Room', 'Id', 'Gender', 'Degree', 'Year']
		if df.isnull().sum().sum() > 0:
			raise ValueError(f'Following rows contain null values {df[df.isnull().any(axis=1)].index.tolist()}')
		if df.duplicated(subset=['Id']).sum() > 0:
			raise ValueError(f'Following rows contain duplicate Ids {df[df.duplicated(subset=["Id"])].index.tolist()}')
		# -------------------------------------
		# More Data Transformations (if needed)
		# -------------------------------------
		df.Block = df.Block.astype(int)
		df.Room = df.Room.astype(int)
		df.Id = df.Id.astype(int)

		for _, row in df.iterrows():
			new_student = Student(row['Id'], row['Gender'], row['Degree'], row['Year'])
			self.students[new_student.id] = new_student
			self.dorm.rooms[row['Block']][row['Room']].addStudent(new_student)
	
	def read_students_to_accommodate(self, students_input_file):
		df = pd.read_excel(students_input_file)
		if df.shape[1] != 7:
			raise ValueError(f'Number of columns should be 7')
		df.columns = ['Id', 'Gender', 'Degree', 'Year', 'Roommate1', 'Roommate2', 'Roommate3']
		if df[['Id', 'Gender', 'Degree', 'Year']].isnull().sum().sum() > 0:
			raise ValueError(f'Following rows contain null values {df[df[["Id", "Gender", "Degree", "Year"]].isnull().any(axis=1)].index.tolist()}')
		# -------------------------------------
		# More Data Transformations (if needed)
		# -------------------------------------
		df.Id = df.Id.astype(int)

		self.student_ids_with_rooms = []
		self.student_ids_to_accommodate = []
		for _, row in df.iterrows():
			id = row['Id']
			gender = row['Gender']
			degree = row['Degree']
			year = row['Year']
			roommates = []
			for i in range(1, 4):
				if not pd.isna(row[f'Roommate{i}']):
					roommates.append(int(row[f'Roommate{i}']))
			
			if id in self.students: # Student already in dorm
				if len(roommates) == 0:
					raise ValueError(f'Student {id} is already in dorm, did not specify roommates, but applied for accommodation. Contradiction.')
				self.student_ids_with_rooms.append(id)
				self.students[id].intended_roommate_ids = roommates
			else:
				self.students[id] = Student(id, gender, degree, year, roommates)
				self.student_ids_to_accommodate.append(id)
		# List of students to accommodate that do not have rooms

		return self.student_ids_with_rooms, self.student_ids_to_accommodate
				
	
	def match_roommates(self):
		self.student_ids_to_destroy: dict[int, str] = {}
		for student in self.students.values():
			if len(student.intended_roommate_ids) == 0: # Student did not apply for roommates matching.
				continue                                # That student either already has a room or applied as random (does not need to be paired)
			
			# Check if all roommates exist in students list
			for roommate_id in student.intended_roommate_ids: 
				if roommate_id not in self.students:
					self.student_ids_to_destroy[student.id] = f'Id error! Student {student.id} fault! Roommate {roommate_id} id does not exist or he/she did not apply for accommodation.'
					break
			
			if student.id in self.student_ids_to_destroy:
				continue

			# Check if all Ids are unique. Student did not apply for the same roommate twice or no one applied for himself/herself.
			set_of_roommates = set(student.intended_roommate_ids)
			set_of_roommates.add(student.id) # Now it is a set of all students that applied for each other
			if len(set_of_roommates) != len(student.intended_roommate_ids) + 1:
				self.student_ids_to_destroy[student.id] = f'Ids uniqueness error! Student {student.id} fault! Roommate Ids are not unique or student applied for himself/herself.'

			if student.id in self.student_ids_to_destroy:
				continue
			
			# Check if roommates have unique Ids. No one applied for the same roommate twice or no one applied for himself/herself.
			for roommate_id in student.intended_roommate_ids:
				if len(set_of_roommates) != len(self.students[roommate_id].intended_roommate_ids) + 1:
					self.student_ids_to_destroy[student.id] = f'Ids uniqueness error! Student {student.id} fault! Roommate {roommate_id} Ids are not unique or student applied for himself/herself.'
					break

			# Id matching
			# Now that we know all roommates exist and are unique, we need to check if each roommate applied for the other.
			# In case of 2, If A applied for B, then B must have applied for A. In case of 3, If A applied for B and C, then B must have applied for A, C and C must have applied for A, B.
			# double check this
			for roommate_id in student.intended_roommate_ids:
				set_of_intended_roommates = set(self.students[roommate_id].intended_roommate_ids)
				set_of_intended_roommates.add(roommate_id)
				if set_of_intended_roommates != set_of_roommates:
					self.student_ids_to_destroy[student.id] = f'Id match error. Student {student.id} or Roommate {roommate_id} did something wrong with Ids.'
					break
			
			if student.id in self.student_ids_to_destroy:
				continue

			# Gender matching
			for roommate_id in student.intended_roommate_ids:
				if self.students[roommate_id].gender != student.gender:
					self.student_ids_to_destroy[student.id] = f'Gender match error. Student {student.id} or Roommate {roommate_id} have different genders.'
					break
			
			if student.id in self.student_ids_to_destroy:
				continue
		
		for student_id in self.student_ids_to_destroy:
			print('Student', student_id, 'match will be destroyed.\n    Reason:', self.student_ids_to_destroy[student_id])
			self.students[student_id].intended_roommate_ids = []
	

	# Now we need to accommodate students who were paired with those who already have rooms.
	def assign_roommate(self):
		print("Assigning roommates to those who already had rooms...")
		number_of_accommodations = 0
		for student_id in self.student_ids_with_rooms:
			student = self.students[student_id]

			if len(student.intended_roommate_ids) == 0:
				continue

			if student.room is None:
				raise ValueError(f"Student {student.id} has no Room but was supposed to!")
			# We need to check if their pair (tuple or triple or guadriple) can fit into the room of student
			
			intended_roommate_ids_to_accommodate = list(set(student.intended_roommate_ids) - set(current_roommate.id for current_roommate in student.roommates))
			
			if student.room.capacity < len(intended_roommate_ids_to_accommodate):
				error_msg = f'Student {student.id} room has not enough capacity to accommodate his intended roommates.'
				self.student_ids_to_destroy[student.id] = error_msg
				print('Student', student_id, 'match will be destroyed.\n    Reason:', self.student_ids_to_destroy[student_id])
				student.intended_roommate_ids = []
				for roommate_id in student.intended_roommate_ids:
					self.student_ids_to_destroy[roommate_id] = error_msg
					print('Student', roommate_id, 'match will be destroyed.\n    Reason:', self.student_ids_to_destroy[roommate_id])
					self.students[roommate_id].intended_roommate_ids = []
			
			if student.id in self.student_ids_to_destroy:
				continue
			
			for intended_roomate_id_to_accommodate in intended_roommate_ids_to_accommodate:
				number_of_accommodations += 1
				student.room.addStudent(self.students[intended_roomate_id_to_accommodate])
		
		print("Done assigning roommates to those who already had rooms.")
		print("Number of successful accommodations", number_of_accommodations)
			
	def get_rooms(self, block_list: list[int], floor_list: list[int], occupancy: list[int], gender: list[str], specific_room: int | None = None) -> tuple[pd.DataFrame, list[Room]]:
		print("Getting rooms...")
		print('Parameters:')
		print('    block_list:', block_list)
		print('    floor_list', floor_list)
		print('    occupancy:', occupancy)
		print('    gender:', gender)
		print('    specific_room:', specific_room)

		list_of_rooms: list[Room] = []
		for block_num in block_list:
			for room_num in self.dorm.rooms[block_num]:
				
				room = self.dorm.rooms[block_num][room_num]
				
				if (room_num // 100) not in floor_list:
					continue
				
				if len(room.students) not in occupancy:
					continue
				
				if room.gender is not None and room.gender not in gender:
						continue

				if specific_room is not None and room_num != specific_room:
					continue

				list_of_rooms.append(room)
		
		print("List of rooms:", list_of_rooms)
		
		data = [(room.block_number, room.number, room.gender, str(room.students)) for room in list_of_rooms]
		df = pd.DataFrame(data, columns=['Block', 'Room', 'Gender', 'Students'])

		return df, list_of_rooms

	def refresh_df_students_to_accommodate(self):
		self.student_ids_to_accommodate = [student.id for student in self.students.values() if student.room is None]
		data = [(student.id, student.gender, student.degree, student.year, str(student.intended_roommate_ids)) for student in [self.students[id] for id in self.student_ids_to_accommodate]]
		columns = ['Id', 'Gender', 'Degree', 'Year', 'Intended Roommates']
		
		self.df_students_to_accommodate = pd.DataFrame(data, columns = columns)

	def filter_students(self, gender: list[str], degree: list[str], year: list[str], ids: list[int] | None = None) -> tuple[pd.DataFrame, list[int]]:
		self.refresh_df_students_to_accommodate()
		df = self.df_students_to_accommodate

		df = df[(df['Gender'].isin(gender)) & (df['Degree'].isin(degree)) & (df['Year'].isin(year))]
		
		if ids is not None:
			df = df[df['Id'].isin(ids)]

		
		return df, df['Id'].tolist()
		
	def populate(self, student_ids_to_populate: list[int], rooms_list: list[Room], random: bool = True):
		print("Poppulating...")
		if random:
			shuffle(rooms_list)

		student_ids_to_populate.sort(key = lambda student_id: len(self.students[student_id].intended_roommate_ids), reverse = True)

		for student_id in student_ids_to_populate:
			student = self.students[student_id]

			if student.room is not None:
				continue

			group_len = len(student.intended_roommate_ids) + 1
			best_room: Room | None = None
			for room in rooms_list:
				if room.gender is not None and room.gender != student.gender:
					continue

				if room.capacity < group_len:
					continue
				
				if best_room is None:
					best_room = room
					continue

				if room.capacity < best_room.capacity:
					best_room = room
			
			if best_room is not None:
				best_room.addStudent(student)
				
				for roommate_id in student.intended_roommate_ids:
					best_room.addStudent(self.students[roommate_id])
		
		were_not_populated = []
		for student_id in student_ids_to_populate:
			student = self.students[student_id]
			if student.room is None:
				were_not_populated.append(student_id)

		# Print Statistics
		print("Statistics:")
		print("    Number students were populated:", len(student_ids_to_populate) - len(were_not_populated))
		print("    Number students were not populated:", len(were_not_populated))
		print("    Student IDs were not populated:", were_not_populated)
		
		return were_not_populated
			
			
	def hard_population(self):
		pass
		# This will be useful when we need to destroy matches in order to accommodate students into rooms. But this is only applicabple when there are no other rooms availble.
		# We can use it later
		# if student.room is None:
		#     self.student_ids_to_destroy[student_id] = f'Student {student.id} could not be populated.'
		#     print('Student', student_id, 'match will be destroyed.\n    Reason:', self.student_ids_to_destroy[student_id])
		#     student.intended_roommate_ids = []
		#     for roommate_id in student.intended_roommate_ids:
		#         self.student_ids_to_destroy[roommate_id] = f'Student {roommate_id} could not be populated.'
		#         print('Student', roommate_id, 'match will be destroyed.\n    Reason:', self.student_ids_to_destroy[roommate_id])
		#         self.students[roommate_id].intended_roommate_ids = []
		


		

		
		

	
	



		

	

				

