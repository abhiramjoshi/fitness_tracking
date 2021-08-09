import mongo_utils
from datetime import datetime
from pprint import pprint
#search function so that you can choose an item if your item is not exactly the same name.
#change meal quantities and also meal to dish, where meal foods become ingredients.
#change create food so that you can addd multiple ingredients and can create a dish, which will be added into the

class Meal():
    """
    """
    collection = "Meals"
    #This class will be used to collate a meal. Each meal can have any number of food items. A meal will have total calories as well as total macros. We later may also want to add labels for the meal (healthy, unhealthy), maybe a meal score, and then also a label of what meal type of meal it was (breakfast, lunch, dinner)
    def __init__(self, food_dict, time=datetime.now().strftime('%y-%m-%d'), date=datetime.now().strftime('%H:%M'), user=None, name=None):
        self.name = name
        self.foods = [food_dict[f]["_id"] for f in food_dict]
        self.food_names = [food_dict[f]["name"] for f in food_dict]
        self.calories = self.calculate_totals(food_dict,"calories")
        self.carbs = self.calculate_totals(food_dict,"carbs")
        self.fats = self.calculate_totals(food_dict,"fats")
        self.protiens = self.calculate_totals(food_dict,"protiens")
        self.time = time
        self.date = date
        self.user = user

    def calculate_totals(self, foods, nutrient):
        total = 0
        for food in foods:
            total += foods[food][nutrient]*foods[food]["quantity"]
        return total

    @staticmethod
    def find_meal(meal_name, db = None):
        meal_dict = None
        if db is None:
            data_base = mongo_utils.DBConnector()
        else:
            data_base = db
        try:
            meal_dict = data_base.search([meal_name], 'name' ,collection='meals')[0]
        except IndexError:
            print("There are no meals that match your search")
        data_base.close()
        return meal_dict

    @classmethod
    def create(cls, food_names = None, quantities = None, user_id = None, create_dish = False):
        print("\nCreate meal\n-----------")
        db = mongo_utils.DBConnector()
        food_dicts = []
        if not food_names:
            while True:
                name = mongo_utils.get_input('food name', str, 'that you would like to add to the meal or [q] to quit', blank=False)
                if name.lower() == 'q':
                    return mongo_utils.EmptyClass()
                temp = db.verify_and_insert([name], 'name', 'food', Food)
                if temp:
                    food_dicts.append(temp[0])
                ans = mongo_utils.get_input(None, str, 'Would you like to add another food? [y/N]', only_message=True)
                if ans.upper() == 'N':
                    break
        else:
            food_dicts = db.verify_and_insert(food_names, 'name', 'food', Food)
        if not food_dicts:
            return mongo_utils.EmptyClass()
        meal_dict = {}
        for i,food in enumerate(food_dicts):
            meal_dict[food['name'].lower()] = food
            try:
                meal_dict[food['name'].lower()]['quantity'] = quantities[i]
            except (IndexError, TypeError):
                quantity = mongo_utils.get_input('quantity', float, f'(per {food["units"]}) of {food["name"].lower()} consumed: ')
                meal_dict[food['name'].lower()]['quantity'] = quantity
        if not create_dish:
            time, date = mongo_utils.getTime()
            if user_id is None:
                while True:
                    find_username = input('Which user will this meal be linked with? Please enter user name or enter [q] to not associate a user: ')
                    if find_username == "" or find_username.lower() == 'q':
                        break
                    user_id = Users.find_user(find_username, db=db)
                    if not user_id:
                        user_id = user_id['_id']
                        break
                    print("Username was not found")

            give_name = mongo_utils.get_input(None, str, "Would you like to give this meal a name? This will allow you to easily retrieve it later if you eat the same meal. [y/N] ", only_message=True)    
            if give_name.lower() == 'y':
                meal_name = mongo_utils.get_input("meal name", str)
            else:
                meal_name = None
                print("Meal name was not given")
        else:
            time = None
            date = None
            meal_name = None
        db.close()
        return cls(meal_dict, time, date, user_id, meal_name)

class Food():
    collection = "food"
    def __init__(self, name, quantity = 1, calories=0, carbs=0, fats=0,protiens=0, units = 'g', ingrdients = []):
        self.name = name.lower()
        self.ingredients = ingrdients
        self.calories = calories/quantity
        self.carbs = carbs/quantity
        self.fats = fats/quantity
        self.protiens = protiens/quantity
        self.units = units

    @classmethod
    def create(cls):
        results = mongo_utils.fill_info([
            ("name", str, "of food", False),
            ("serving size", float, "(ommit units)"),
            ("units", str, "of serving size (e.g 'g', 'ml', etc)", False),
            ("calories", float, "per serving"),
            ("carbs", float, "per serving"),
            ("fats", float, "per serving"),
            ("protiens", float, "per serving")
        ])
        try:
            name = results['name'].lower()
            quantity = results['serving size']
            calories = results['calories']
            carbs = results['carbs']
            fats = results['fats']
            protiens = results['protiens']
            units = results["units"]
        except TypeError:
            return results
        return cls(name, quantity, calories, carbs, fats, protiens, units)

    @classmethod
    def create_dish(cls):
        """
        Combine basic foods to create dish
        """
        print("\nCreate dish\n-----------")
        db = mongo_utils.DBConnector()
        while True:    
            meal_name = mongo_utils.get_input("meal name", str, message='to create dish from', blank=False)
            meal_dict = db.search([meal_name], 'name', 'meal')
            if meal_dict:
                meal_dict = meal_dict[0]
                break
            ans = input('There are no meals with that name, either create a meal first or search again.\nPress enter to continue or press [q] to quit ')
            if ans == 'q':
                return mongo_utils.EmptyClass()
            ans = mongo_utils.get_input(None, int, "[1] Search again\n[2] Create new meal\nEnter number that corresponds with your choice", only_message=True)
            if ans == 2:
                meal_dict = Meal.create(create_dish=True).__dict__
                break
        if not meal_dict:
            return mongo_utils.EmptyClass()
        dish_name = mongo_utils.get_input("dish name", str, f"or leave blank to name it {meal_name} ")
        if dish_name == "" or dish_name is None:
            dish_name = meal_name
        print(f'Dish was named {dish_name}')
        quantity = mongo_utils.get_input("quantity", float, "per serving of dish (how much did you make with added ingredients above?) ")
        units = mongo_utils.get_input("units", str, "of measuring quantity")
        db.close()
        return cls(dish_name, quantity=quantity, calories=meal_dict['calories'], carbs=meal_dict['carbs'], fats=meal_dict['fats'], protiens=meal_dict['protiens'], units=units, ingrdients=meal_dict['food_names'])
        #return cls(dish_name, dish_quantity, food_dict['calories'], food_dict['carbs'], food_dict["fats"], food_dict['protiens'], food_dict['ingredients'])


class Workouts():
    def __init__(self):
        pass

class Exercise():
    pass

class Day():
    pass

class FitnessState():
    """
    This class will record things that we wish to keep track of. For example, the user's weight, measurements, etc. Each state will have associated with it a time in which that measurement was taken.
    """
    def __init__(self, weight = None, height = None, chest = None, forearms = None, arms = None, waist = None, legs = None):
        self.weight = weight
        self. height = height
        self.chest = chest
        self.arms = arms
        self.forearms = forearms
        self.waist = waist
        self.legs = legs
        self.date = mongo_utils.getTime(time="NOW")

class Users():
    def __init__(self, username, name, DOB, fitness_states=None, id=None):
        self.username = username
        self.name = name
        self.DOB = DOB
        self.id = id
        if fitness_states is None:
            self.fitness_states = []
        else:
            self.fitness_states = fitness_states
        self.weight = self.get_measurement('weight')
        self. height = self.get_measurement('height')
        self.chest = self.get_measurement('chest')
        self.arms = self.get_measurement('arms')
        self.forearms = self.get_measurement('forearms')
        self.waist = self.get_measurement('waist')
        self.legs = self.get_measurement('legs')

    def get_measurement(self, measurement):
        try:
            current_measurement = self.fitness_states[-1].__dict__[measurement]
        except (IndexError, KeyError):
            current_measurement = None
        return current_measurement

    def add_state(self, state):
        if isinstance(state, FitnessState):
            self.fitness_states.append(state)
            self.update_state(state)
        else:
            print(f"Type of {state} is incorrect. The state could not be added to the user")

    def update_state(self, state):
        for param in state.__dict__:
            setattr(self, param, state.__dict__[param])

    def add_meal(self, meal_name = None, food_names = None, quantities = None):
        meal = None
        if meal_name is None and food_names is None:
            ans = mongo_utils.get_input(None, str, "Would you like to retrieve a previous meal? [y/N] ", only_message=True)
            if ans.lower() == 'y':
                meal_name = mongo_utils.get_input("meal name", str, blank=False)
        if meal_name is not None:
            meal = Meal.find_meal(meal_name)
        if meal is not None:
            meal['user_id'] = self.id
        else:
            meal = Meal.create(food_names=food_names, quantities=quantities, user_id=self.id)
            meal = meal.__dict__
        if not meal:
            print("Meal was not added")
            return
        quit = input("Created meal will now be inserted into the database. Press enter or [q] to abort ")
        if quit.lower() == 'q':
            return 
        db = mongo_utils.DBConnector()
        pprint(meal)
        db.insert_items(meal, collection='meal')            
        db.close()
        
    def get_meals(self, start, end = None, get_meals_only = False):
        dates = mongo_utils.get_dates(start, end)
        db = mongo_utils.DBConnector()
        cursor = db.find_item(dates, 'date', 'meal')
        meals = [document for document in cursor if document['user'] == self.id]
        db.close()
        if not meals:
            print(f"There are no meals recorded for this user between the date range {dates[0]} - {dates[-1]}")
            return None
        if get_meals_only:
            print(f'\nMeals between {start} - {end} \n----------------------------')
            pprint(meals)
            print()
        return meals

    def get_meals_periodic(self, period, metrics=[]):
        period_dict = {
            'today': (datetime.now().strftime('%y-%m-%d'), None),
            'week': (datetime.now().strftime('%y-%m-%d'), -7),
            'month': (datetime.now().strftime('%y-%m-%d'), -30),
            'calender month': (datetime.now().strftime('%y-%m')+'-01', datetime.now().strftime('%y-%m-%d'))
        }
        meal_dict = self.get_meals(period_dict[period.lower()][0], period_dict[period.lower()][1], get_meals_only=True)
        return meal_dict

    def generate_counts(self, start, end = None, metrics = [], meals = None):
        if not metrics:
            metrics = ['calories', 'carbs', 'fats', 'protiens']
        if meals is None:    
            meals = self.get_meals(start, end)
        metrics_dict = {}
        if not meals:
            return
        for metric in metrics:
            total = 0
            total = sum([document[metric] for document in meals])
            metrics_dict[metric] = total
        print(f'\nMacro Totals for {start} - {end} \n----------------------------')
        pprint(metrics_dict)
        print()
        return metrics_dict

    def get_counts_periodic(self, period, metrics=[]):
        period_dict = {
            'today': (datetime.now().strftime('%y-%m-%d'), None),
            'week': (datetime.now().strftime('%y-%m-%d'), -7),
            'month': (datetime.now().strftime('%y-%m-%d'), -30),
            'calender month': (datetime.now().strftime('%y-%m')+'-01', datetime.now().strftime('%y-%m-%d'))
        }
        metric_dict = self.generate_counts(period_dict[period.lower()][0], period_dict[period.lower()][1], metrics=metrics)
        # if not metrics:
        #     metric_dict = self.generate_counts(period_dict[period.lower()][0], period_dict[period.lower()][1], ['calories', 'carbs', 'fats', 'protiens'])
        # else:
        #     metric_dict = self.generate_counts(period_dict[period.lower()][0], period_dict[period.lower()][1], metrics=metrics)
        # if period.lower() == 'today':
        #     period = 'day'
        # print(f'Macro Totals for past {period} \n----------------------------')
        # pprint(metric_dict)
        return metric_dict

    def create_dish(self):
        dish = Food.create_dish()
        if isinstance(dish, mongo_utils.EmptyClass):
            return
        db = mongo_utils.DBConnector()
        ans = input(f"Inserting {dish.__dict__['name']} into the database, press enter to continue or [q] to abort ")
        if ans.lower() == 'q':
            return
        db.insert_items(dish, 'food')

        
    @classmethod
    def load_user(cls, username):
        """
        Function used to load a user so that we can add, meals, fitness states etc.

        Inputs
        ------
        username: User to load, type string \n
        Returns
        -------
        User class instance of found user or EmptyClass if user not found.  Return type: Users class or EmptyClass
        """
        #will be used to load a user information from mongoDB so that states can be added or the user can be modified
        user = cls.find_user(username)
        if not user:
            return mongo_utils.EmptyClass()
        for attribute in ['name', 'username','DOB','fitness_states', '_id']:
            try:
                user[attribute]
            except KeyError:
                user[attribute] = None
        return cls(user['username'], user['name'], user['DOB'], user['fitness_states'], user['_id'])

    @classmethod
    def create(cls):
        db = mongo_utils.DBConnector()
        #Need to check if username is unique.
        while True:
            username = mongo_utils.get_input('username', str, blank=False)
            usernames = [document['username'] for document in db.find_item(None, None, 'users', all=True)]
            if username not in usernames:
                break
            print('Username is already in use, please choose another username')
        results = mongo_utils.fill_info([
            ("name", str),
            ("DOB", str, "in format dd/mm/yy")
        ])
        name = results['name']
        DOB = results['DOB']
        db.close()
        return cls(username, name, DOB)

    @staticmethod
    def find_user(username, db = None):
        """
        Function used to search for a user

        Inputs
        ------
        username: Username to search for, type string \n
        db: Database Connector to be used for process, type DBConnector \n

        Returns
        -------
        Found user dictionary Return type: dictionary
        """
        user_dict = mongo_utils.EmptyClass().__dict__
        if db is None:
            data_base = mongo_utils.DBConnector()
        else:
            data_base = db
        try:
            user_dict = data_base.find_item([username], 'username' ,collection='users')[0]
        except IndexError:
            all_users = data_base.find_item(None, None, 'users', all=True)
            all_users = [user['username'] for user in all_users]
            if not all_users:
                print("There are no users")
        data_base.close()
        return user_dict

    @staticmethod
    def new_user():
        print("We will now create a new user")
        new_user = Users.create()
        abort = input("The user will now be added to the database [Enter to continue or q to abort] ")
        print(new_user.__dict__)
        if abort.lower() == 'q':
            return
        con = mongo_utils.DBConnector()
        con.insert_items(new_user, collection='users')

if __name__ == "__main__":
    pass