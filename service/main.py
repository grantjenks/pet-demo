import grpc
from concurrent import futures
import sqlite3
import pet_pb2
import pet_pb2_grpc

DB_NAME = 'pets.db'


def init_db():
    with sqlite3.connect(DB_NAME) as con:
        cursor = con.cursor()
        query = """
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY
                , name TEXT
                , date_of_birth TEXT
            )
        """
        cursor.execute(query)
        con.commit()


class PetService(pet_pb2_grpc.PetServiceServicer):
    def CreatePet(self, request, context):
        with sqlite3.connect(DB_NAME) as con:
            cursor = con.cursor()
            cursor.execute(
                'INSERT INTO pets (name, date_of_birth) VALUES (?, ?)',
                (request.pet_data.name, request.pet_data.date_of_birth),
            )
            con.commit()
            pet_id = cursor.lastrowid
        return pet_pb2.CreatePetResponse(
            pet=pet_pb2.Pet(id=pet_id, data=request.pet_data)
        )

    def ReadPet(self, request, context):
        with sqlite3.connect(DB_NAME) as con:
            cursor = con.cursor()
            cursor.row_factory = sqlite3.Row
            cursor.execute('SELECT * FROM pets WHERE id = ?', (request.id,))
            row = cursor.fetchone()
            if row:
                return pet_pb2.ReadPetResponse(
                    pet=pet_pb2.Pet(
                        id=row['id'],
                        data=pet_pb2.PetData(
                            name=row['name'],
                            date_of_birth=row['date_of_birth'],
                        ),
                    )
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Pet not found')
                return pet_pb2.ReadPetResponse()

    def UpdatePet(self, request, context):
        with sqlite3.connect(DB_NAME) as con:
            fields_to_update = {
                field: getattr(request.pet_data, field)
                for field in request.update_mask.paths
            }
            update_clause = ', '.join(
                f'{field} = ?' for field in fields_to_update.keys()
            )
            cursor = con.cursor()
            cursor.execute(
                f'UPDATE pets SET {update_clause} WHERE id = ?',
                tuple(fields_to_update.values()) + (request.id,),
            )
            if cursor.rowcount == 0:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Pet not found')
                return pet_pb2.UpdatePetResponse()
            con.commit()
            return self.ReadPet(pet_pb2.ReadPetRequest(id=request.id), context)

    def DeletePet(self, request, context):
        with sqlite3.connect(DB_NAME) as con:
            cursor = con.cursor()
            cursor.execute('DELETE FROM pets WHERE id = ?', (request.id,))
            if cursor.rowcount == 0:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Pet not found')
            con.commit()
        return pet_pb2.DeletePetResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pet_pb2_grpc.add_PetServiceServicer_to_server(PetService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    init_db()
    serve()
