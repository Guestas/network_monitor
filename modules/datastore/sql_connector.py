"""
takes care of the connection to the database
"""
from sqlalchemy.sql import func
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
import sqlite3 #  i have added this if you find better way to handle databases, you can remove it

from settings import DATASTORE_DATABASE
from modules.datastore.models import Response, Task, Address
from modules.datastore.models import make_tables
from modules.sql_connector import CommonSqlConnector

class DatastoreSqlConnector(CommonSqlConnector):
    """
    Extra sql operations required for Datastore.
    """

    def __init__(self):
        """
        Init the sql connector (connect, prepare tables).
        """
        engine = db.create_engine('sqlite:///{}'.format(DATASTORE_DATABASE), echo=False)
        make_tables(engine)
        self.sessions = sessionmaker(engine)
        
    def M_CE(self):
        """
        generate JSON of average response time of each ip addresses without date from and date to
        """ # TODO time selection
        outcome = []
        cur = sqlite3.connect("databases/datastore.db").cursor()
        table_list1 = [a for a in cur.execute("SELECT * FROM 'responses'")]
        for log in table_list1:
            outcome.append({"time": log[3], log[1]: log[4], "worker":log[5]})#https://currentmillis.com
        return outcome
    def M_CE2(self, data):
        """
        add new task
        """ # TODO add colors and name to database
        con = sqlite3.connect("databases/datastore.db")
        cur = con.cursor()
        if (len(cur.execute(f"SELECT address FROM tasks WHERE address='{data[0]}'").fetchall()) == 0):
            cur.execute("INSERT INTO tasks (address, task, frequency, worker) VALUES "
                    f"('{data[0]}', '{data[1]}', '{data[2]}', '{data[3]}')")
        con.commit()
        con.close()
        return "ok MCE2"

    def M_CE3(self, address):
        """
        dellete task with ressults
        """
        con = sqlite3.connect("databases/datastore.db")
        cur = con.cursor()
        cur.execute(f"DELETE FROM 'tasks' WHERE address='{address}'")
        cur.execute(f"DELETE FROM 'responses' WHERE address='{address}'")
        con.commit()
        con.close()
        return "ok MCE3"

    def M_CE4(self):
        """
        dellete all responses
        """
        con = sqlite3.connect("databases/datastore.db")
        cur = con.cursor()
        cur.execute("DELETE FROM 'responses'")
        con.commit()
        con.close()
        return "ok MCE4"

    def M_CE5(self, data):
        """
        update task (dell old and save new)
        """
        print(data)
        con = sqlite3.connect("databases/datastore.db")
        cur = con.cursor()
        cur.execute(f"DELETE FROM 'tasks' WHERE address='{data[4]}'")
        if (len(cur.execute(f"SELECT address FROM tasks WHERE address='{data[4]}'").fetchall()) == 0):
            cur.execute("INSERT INTO tasks (address, task, frequency, worker) VALUES "
                        f"('{data[0]}', '{data[1]}', '{data[2]}', '{data[3]}')")

        con.commit()
        con.close()
        return "ok MCE5"

    def M_CE6(self, data):
        """
        pause task just remove task from list
        """

        con = sqlite3.connect("databases/datastore.db")
        cur = con.cursor()
        if data[4]=='false':
            cur.execute(f"DELETE FROM 'tasks' WHERE address='{data[0]}'")
        else:
            if (len(cur.execute(f"SELECT address FROM tasks WHERE address='{data[0]}'").fetchall()) == 0):
                cur.execute("INSERT INTO tasks (address, task, frequency, worker) VALUES "
                            f"('{data[0]}', '{data[1]}', '{data[2]}', '{data[3]}')")

        con.commit()
        con.close()
        return "ok MCE6"

    def get_worker_tasks(self, worker):
        """
        Returns list of tasks for requested worker.
        """
        with self.sessions.begin() as session:
            query = session.query(Task).filter(Task.worker == worker)
            return [item.__dict__ for item in query.all()] # TODO make custom function in Task class (instead of __dict__)


# These top functions are what I had used.







    def add_response(self, address, time, value, task, worker):
        """
        write response of tested address to db
        """ # TODO update last time of task
        # TODO obsolete since worker sync
        result = Response(
            address=address,
            time=int(time),
            value=int(value),
            task=task,
            worker=worker
        )
        with self.sessions.begin() as session:
            session.add(result)

    def get_avrg_response_all(self, date_from=None, date_to=None):
        """
        generate JSON of average response time of each ip addresses, dateFrom and dateTo are optional
        """ # TODO time selection
        outcome = []
        with self.sessions.begin() as session:
            for item in session.query(Response.address).distinct():
                address = item[0]
                # TODO optimize query
                value = session.query(func.avg(Response.value)).filter(Response.address == address).one()[0]
                outcome.append({"address": address, "value": int(value)})
        return outcome

    def get_response_summary(self, worker=False, time_from=False, time_to=False):
        """
            get info is detailed list of addresses (generate: number of addr records,
            first time testing, last time testing and average responsing time)
            # TODO filter by worker and task
        """
        outcome = []
        with self.sessions.begin() as session:
            for item in session.query(Response.address).distinct():
                address = item[0]
                query = session.query(Response).filter(Response.address == address)
                if worker:
                    query = query.filter(Response.worker == worker)
                if time_from:
                    query = query.filter(Response.time > time_from)
                if time_to:
                    query = query.filter(Response.time < time_to)
                outcome.append({
                    "address": address,
                    "first_response": query.order_by(Response.time).first().time,
                    "last_response": query.order_by(Response.time.desc()).first().time,
                    "average": query.with_entities(func.avg(Response.value)).one()[0],
                    "count": query.count()
                })
        return {"status": "Ok", "data": outcome}

    def get_worker_tasks(self, worker):
        """
        Returns list of tasks for requested worker.
        """
        with self.sessions.begin() as session:
            query = session.query(Task).filter(Task.worker == worker)
            return [item.__dict__ for item in query.all()] # TODO make custom function in Task class (instead of __dict__)

    def sync_worker(self, data):
        """
        Sync worker - store responses and return tasks
        """
        with self.sessions.begin() as session:
            for response in data["responses"]:
                result = Response(
                    address=response["address"],
                    time=response["time"],
                    value=response["value"],
                    task=response["task"],
                    worker=data["worker"]
                )
                session.add(result)
                # TODO alter task last update

            tasks = session.query(Task).filter(Task.worker == data["worker"])
            return [item.__dict__ for item in tasks.all()] # TODO make custom function in Task class (instead of __dict__)

    def clear_all_tables(self):
        """
        Clear content from tables (for testing purposes mainly).
        """
        with self.sessions.begin() as session:
            session.query(Task).delete()
            session.query(Response).delete()
            session.query(Address).delete()

    def get_responses(self, worker=False, task="ping"):
        """
        Return list of responses.
        """
        with self.sessions.begin() as session:
            query = session.query(Response).filter(Response.task == task)
            if worker:
                query.filter(Response.worker == worker)
            return [item.__dict__ for item in query.all()] # TODO custom function

    def update_address(self, address_data):
        """
        Update address. If address does not exist, create it.
        """
        with self.sessions.begin() as session:
            address = session.query(Address).filter(Address.address == address_data["address"]).first()
            if address is None:
                address = Address(
                    address=address_data["address"],
                )
                session.add(address)
                status = {"status": "Created"}
            else:
                status = {"status": "Updated"}
            data_keys = ["location", "latitude", "longitude", "note"]
            for key in data_keys:
                if key in address_data:
                    setattr(address, key, address_data[key])
            return status

    def delete_address(self, address_data):
        """
        Delete address if exists - according ip address
        """
        with self.sessions.begin() as session:
            address = session.query(Address).filter(Address.address == address_data["address"]).first()
            if address is None:
                return {"status": "Not found"}
            else:
                session.delete(address)
                return {"status": "Deleted"}

    def get_address(self, address):
        """
        Get information about IP address
        """
        with self.sessions.begin() as session:
            address = session.query(Address).filter(Address.address == address).first()
            if address is None:
                return {"status": "Not found"}
            else:
                return {"status": "Ok", "data": address.values()}

    def get_address(self, address):
        """
        Get information about IP address
        """
        with self.sessions.begin() as session:
            address = session.query(Address).filter(Address.address == address).first()
            if address is None:
                return {"status": "Not found"}
            else:
                return {"status": "Ok", "data": address.values()}

    def get_all_addresses(self):
        """
        Return all addresses
        """
        with self.sessions.begin() as session:
            query = session.query(Address)
            return {"status": "Ok", "data": [item.values() for item in query.all()]}
