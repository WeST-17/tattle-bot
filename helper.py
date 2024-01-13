from datetime import date, datetime, timedelta

# Helper Functions:
# Appends complaint to database
def gcFile(sheet, accused: str, tea: str, ban: str):
    currentDate = date.today().isoformat()
    all_values = sheet.get_all_values()
    sheet.append_row([accused, currentDate, tea.content, ban.content])

# Compiles complaint report for admins by username
def teaGet(sheet, user: str):
    complaint_values = sheet.get_all_values()
    filtered_complaints = [row for row in complaint_values if row[0] == user]
    return filtered_complaints

# Demotion checker
def demoCheck(sheet, user: str):
    demotion_check = sheet.get_all_values()
    userFilter = [row for row in demotion_check if row[0] == user]
    return userFilter

# Demotion adjuster
# Note for later:
    # elif userFilter and is_valid_date(weeks):
    #     # New end date for demotion
    #     weeksAdd = datetime.strptime(weeks.content, "%Y-%m-%d %H:%M:%S")
        
    #     target_row = userFilter[0]

    #     # Obtain cells to update
    #     cellUpdate = "B" + str(demoAdd.index(target_row) + 1)
    #     dateCellUpdate = "C" + str(demoAdd.index(target_row) + 1)
    #     target_col_index = 1
    #     target_date_index = 2

    #     current_end_date = datetime.strptime(target_row[target_date_index], "%Y-%m-%d %H:%M:%S")
    #     new_weeks_count = (weeksAdd - current_end_date) // 7 + 1 # calculate new weeks count from new end date and current end date

    #     current_weeks = int(target_row[target_col_index])
    #     totalWeeks = current_weeks + new_weeks_count

    #     sheet.update(values=str(totalWeeks), range_name=cellUpdate)
    #     sheet.update(values=str(weeksAdd), range_name=dateCellUpdate)
    #     return "User demotion length and end date updated!"

    # elif not userFilter and is_valid_date(weeks):
    #     end_date = datetime.strptime(weeks, "%Y-%m-%d")

    #     current_date = date.today().isoformat()
    #     new_weeks_count = (end_date - current_date) // 7 + 1 # calculate new weeks count from new end date and current end date

    #     sheet.update(values=str(new_weeks_count), range_name=cellUpdate)
    #     sheet.update(values=str(end_date), range_name=dateCellUpdate)
    #     return "New user demotion length and end date updated!"

def demotion(sheet, user: str, weeks: str):
    demoAdd = sheet.get_all_values()
    weeksAdd = int(weeks.content)
    userFilter = [row for row in demoAdd if row[0] == user]

    if userFilter:
        target_row = userFilter[0]

        # Obtain cells to update
        cellUpdate = "B" + str(demoAdd.index(target_row) + 1)
        dateCellUpdate = "C" + str(demoAdd.index(target_row) + 1)
        target_col_index = 1
        target_date_index = 2

        current_weeks = int(target_row[target_col_index])
        totalWeeks = current_weeks + weeksAdd

        current_end_date = datetime.strptime(target_row[target_date_index], "%Y-%m-%d %H:%M:%S")
        new_end_date = current_end_date + timedelta(days=7*weeksAdd)

        sheet.update(values=str(totalWeeks), range_name=cellUpdate)
        sheet.update(values=str(new_end_date), range_name=dateCellUpdate)
        return "User demotion length and end date updated!"
    
    else:
        end_date = date.today() + timedelta(days=7*weeksAdd)
        sheet.append_row([user, str(weeksAdd), str(end_date)])
        return "New user demotion length and end date updated!"

# integer check
def is_integer(message):
    try:
        int(message.content)
        return True
    except ValueError:
        return False
    
# valid date check:
def is_valid_date(message):
    try:
        # Try to parse the message content as a date
        datetime.strptime(message.content, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False