import mongo_utils
import classes as c
import pprint

def login(username = None):
    q  = False
    if username is None:
        print('Please enter username to continue, enter q to quit')
        while not q:
            username = mongo_utils.get_input(None, str, message='Username: ', only_message=True)
            if username.lower() == 'q':
                return
            user = c.Users.load_user(username)
            if user.__dict__:
                break
            print("Press user does not exist")
    else:
        user = c.Users.load_user(username)
    return main_user_menu(user)

def signup():
    q = False
    print("Creating a new user")
    while not q:
        user = c.Users.create()
        db = mongo_utils.DBConnector()
        db.insert_items([user], 'users')
        print(f'User {user.__dict__["username"]} has been created.')
    return login(user.__dict__["username"])

def main_user_menu(user):
    options = {
            1:('Add meal', user.add_meal),
            2:('Create dish', user.create_dish),
            3:('Get macro counts',counts, [{'user': user}]),
            4:('Get Meals', meals, [{'user': user}]),
            5:('Update measurements',user.update_state),
            6:('Update user information',4),
            7:('Logout', end)
        }
    menu(options)

def get_dates():
        end_date = None
        print('Pleae specify the start date')
        _, start_date = mongo_utils.getTime(date_only=True)
        ans = mongo_utils.get_input(None, str, 'Would you like to specify an end date? If empty then only meals on the specified start date will be shown. [y/N]')
        if ans.upper() != 'N':
            print('Please specify the end date')
            _, end_date = mongo_utils.getTime(date_only=True)
        return {'start':start_date, 'end':end_date}

def choose_metrics():
    avi_metrics = {
        1:'Calories',
        2:'Carbs',
        3:'Fats',
        4:'Protiens',
        5:'All'
    }
    metrics = []
    while avi_metrics:
        print("Choose one of the following options below")
        print('\n'.join([f'[{key}]: {avi_metrics[key]}' for key in avi_metrics]))
        ans = mongo_utils.get_input(None, int, message="Please enter the value of the metric you would like to add ", only_message=True)
        if ans not in avi_metrics.keys():
            print('Option is invalid')
        else:
            if ans == 5:
                break
            else:
                metrics.append(avi_metrics[ans].lower())
                avi_metrics.pop(ans, None)
                avi_metrics.pop(5, None)
        print(f'You have selected the following metrics {metrics}')
        exit_loop = input('Would you like to add another metric? [y/N] ')
        if exit_loop.lower() != 'y':
            break

    return {'metrics': metrics}

def meals(user):    
    #user = c.Users
    options = {
        1: ('Today', user.get_meals_periodic, [{'period':'today'}]),
        2: ('Past Week', user.get_meals_periodic, [{'period':'week'}]),
        3: ('Past Month', user.get_meals_periodic, [{'period':'month'}]),
        4: ('Start of Calender month', user.get_meals_periodic, [{'period':'calender month'}]),
        5: ('Pick specific dates', user.get_meals , [get_dates, {'get_meals_only':True}]), 
        6: ('Quit', end)
    }
    menu(options)

def counts(user):
    #user = c.Users
    options = {
        1: ('Today', user.get_counts_periodic, [{'period':'today'}, choose_metrics]),
        2: ('Past Week', user.get_counts_periodic, [{'period':'week'}, choose_metrics]),
        3: ('Past Month', user.get_counts_periodic, [{'period':'month'}, choose_metrics]),
        4: ('Start of Calender month', user.get_counts_periodic, [{'period':'calender month'}, choose_metrics]),
        5: ('Pick specific dates', user.generate_counts, [get_dates, choose_metrics]), 
        6: ('Quit', end)
    }
    menu(options)

def end():
        global q
        q  = True

def restart():
    global q
    q = False

def menu(options):
    global q 
    q = False
    

    while not q:
        print("Choose one of the following options below")
        print('\n'.join([f'[{key}]: {options[key][0]}' for key in options]))
        ans = mongo_utils.get_input(None, int, message="", only_message=True)
        if ans > len(options):
            print('Option is invalid')
        else:
            try:
                arguments = {}
                for param in options[ans][2]:
                    try:
                        value = param()
                        arguments = {**arguments, **value}
                    except TypeError:
                        arguments = {**arguments, **param}
                options[ans][1](**arguments)    
            except:
                options[ans][1]()    
    
    restart()

def run():
    options = {
        1: ('Login', login),
        2: ('Sign up', signup),
        3: ('Exit', end),
        4: ('Print', pprint.pprint, [{'object':'Message'}])    
    }
    while True:
        print('\nWelcome to MyFitness made by Abhi\n---------------------------------')
        menu(options)
        ans = mongo_utils.get_input(None, str, message='Are you sure you want to exit? [y/N]', only_message=True)
        if ans.lower() == 'y':
            break
    print('Goodbye!')


if __name__ == '__main__':
    run()
    