from pymongo import MongoClient
from datetime import datetime, timedelta
import secret_settings as secrets

class DBConnector():
    def __init__(self):
        self.password = secrets.PASSWORD 
        self.db_name = secrets.DB_NAME
        self.uri_string = secrets.URI_STRING
        self.client = MongoClient(self.uri_string)
        self.db = self.client[self.db_name]

    def access_collection(self, collection):
        col = self.db[collection]
        return col
    
    def insert_items(self, items, collection, access_client = None):
        """
        Function used to insert item in the collection

        Inputs
        ------
        items: Item to insert, type list \n
        collection: Collection name, type string \n
        access_client: Client that is used to access db. Client created in function if not provided. Type Collection.

        Returns
        -------
        None
        """
        #collection = items[0].collection
        if not isinstance(items, list):
            items = [items]
        if access_client is None:
            cli  = self.access_collection(collection)
        else:
            cli = access_client
        item_dicts = [item.__dict__ if type(item) != dict else item for item in items]
        try:
            print(f"{[item['name'] for item in item_dicts]} will be inserted into {collection}")
        except KeyError:
            print(f"Items will now be inserted into {collection}")
        cli.insert_many(item_dicts)

    def find_item(self, items, key, collection, access_client = None, all = False, single = False):
        """
        Function used to search for a single item in the collection, if item is not found empty list will be returned

        Inputs
        ------
        item: Item to search, type list \n
        key: Paramter key of item, type string \n
        collection: Collection name, type string \n
        access_client: Client that is used to access db. Client created in function if not provided. Type Collection.

        Returns
        -------
        Found document Return type: list of dictionaries
        """
        if access_client is None:
            cli = self.access_collection(collection)
        else:
            cli = access_client
        if all:
            found_item = cli.find({})
        elif single:
            found_item = cli.find({key:items[0]})
        else:
            found_item = cli.find({key:{"$in":items}})
        found_item = [doc for doc in found_item]
        return found_item
    
    def verify_and_insert(self, items, key, collection, obj_class, **kwargs):
        q = False
        item_dicts = []
        for item in items:
            result = self.search([item], key, collection)
            if not result:
                print(f"{str(item).capitalize()} does not exist")
                ans = get_input(None, str, message="Would you like to create it now? [y/N/q]", only_message=True)
                if ans.lower() == 'q':
                    q = True
                    break
                if ans.upper() == 'N':
                    continue
                new_item = obj_class.create(**kwargs)
                self.insert_items([new_item], collection)
                result = self.find_item([new_item.__dict__[key]], key, collection, single=True)
            if q:
                break
            item_dicts.append(result[0])
        if q:
            return []
        return item_dicts

    def search(self, item, key, collection, access_client = None):
        """
        Function used to search for a single item in the collection, if item is not found, items with similar names will be displayed for selection

        Inputs
        ------
        item: Item to search, type list \n
        key: Paramter key of item, type string \n
        collection: Collection name, type string \n
        access_client: Client that is used to access db. Client created in function if not provided. Type Collection. 

        Returns
        -------
        Found document Return type: list of dictionary
        """
        if isinstance(item, str):
            item = [item]
        documents = list(self.find_item(item, key, collection, access_client=access_client, single=True))
        if not documents:
            search_field = [{'$regex': f'.*{item[0]}.*'}]
            documents = [(i+1, doc) for i, doc in enumerate(self.find_item(search_field, key, collection, access_client=access_client, single=True))]
            if not documents:
                return []
            print([f'{doc[0]}: {doc[1]["name"]}' for doc in documents])
            while True:
                selection = get_input('number', int, 'of the correct item or 0 to quit: ')
                if selection == 0:
                    documents = []
                    break
                else:
                    try:
                        documents = [documents[selection-1][1]]
                        break
                    except IndexError:
                        print("Selection is not valid")
        return documents

    def clear_db(self):
        collections = self.db.list_collection_names()
        confirm = input("Are you sure you want to clear all documents? Once documents are deleted they cannot be recovered. [y/N] ")
        if confirm == 'y':
            for collection in collections:
                col = self.db[collection]
                result = col.delete_many({})
                print(f"{result.deleted_count} documents were deleted from {collection}")

    def close(self):
        self.client.close()


class EmptyClass():
    def __init__(self):
        pass

def check_datetime_format(datetime_string, datetime_format):
    try:
        datetime.strptime(datetime_string, datetime_format)
        return True
    except ValueError:
        print(f"This is the incorrect format. It should be in {datetime_format}")
        return False

def getTime(time = None, date_only = False):
    while True:
        if not date_only:
            if time is None:
                while True:
                    time = input("Enter time in the format HH:MM, else enter NOW for current date/time: ")
                    if time.upper() == 'NOW':
                        break
                    if check_datetime_format(time, '%H:%M'):
                        break
            if time.upper() == "NOW":
                time = datetime.now().strftime('%H:%M')
                date = datetime.now().strftime('%y-%m-%d')
        if time is None:
            while True:    
                date = input("Enter date in the format yy-mm-dd, else enter today for todays date: ")
                if date.lower() == 'today':
                    date = datetime.now().strftime('%y-%m-%d')
                if check_datetime_format(date, '%y-%m-%d'):
                    break
        print("Date/time entered is", date,time)
        ans = input("Is this correct? [y/N]: ")
        if ans.lower() == 'y':
            break
        time = None
    return time, date

def get_input(input_parameter, parameter_type, message = "", blank = True, only_message = False):
    while True:
        try:
            if only_message:
                result = parameter_type(input(f"{message}: "))
            else:
                result = parameter_type(input(f"Please enter {input_parameter} {message}: "))
            if not blank:
                if result == "":
                    print("This value cannot be empty")
                    continue
            if parameter_type == str:
                if result == "":
                    result = None
            break
        except ValueError:
            print(f"The parameter type does not match the expected type of {parameter_type} ")
    return result

def fill_info(variables):
    while True:
        results = {}
        for variable in variables:
            if isinstance(variable[-1], bool):
                blank = variable[-1]
                variable = variable[:-2]
            else:
                blank = False
            try:
                results[variable[0]] = get_input(variable[0], variable[1], variable[2], blank=blank)
            except IndexError:
                results[variable[0]] = get_input(variable[0], variable[1], blank=blank)
        print("\n".join("{}:{}".format(str(k).capitalize(), v) for k, v in results.items()))
        confirm = input("Is this information correct? [y/N/q] ")
        if confirm == 'y':
            break
        if confirm == 'q':
            return EmptyClass()
    return results

def get_dates(start, end):
    if end is None:
        return [start]
    start = datetime.strptime(start, "%y-%m-%d")
    if not isinstance(end, int):
        end = datetime.strptime(end, "%y-%m-%d")
        delta = (end-start).days
    else:
        delta = abs(end)
        if end < 0:
            dates = [(start + timedelta(days=-x)).strftime("%y-%m-%d") for x in range(0, delta)]
        else:
            dates = [(start + timedelta(days=x)).strftime("%y-%m-%d") for x in range(0, delta)]
    return dates

def modify_food():
    db = DBConnector()
    foods = DBConnector().find_item(None, None, 'food', all=True)
    foods = [doc for doc in foods]
    print(foods[0]['name'])
    #food_ids = [food['_id'] for food in foods]
    food_names = []
    for food in foods:
        try:
            food_names.append(food['name'])
        except KeyError:
            print(food)
    for i, food in enumerate(foods):
        
        try:
            food['units']
        except KeyError:
            print(f"Modifying {food}")
            units = get_input("units", str)
            food_db = db.access_collection('food')
            food_db.update_one({'_id': foods[i]["_id"]}, {"$set":{'units':units}})
            print(food_db.find_one({'_id':foods[i]["_id"]}))

if __name__ == "__main__":
    pass