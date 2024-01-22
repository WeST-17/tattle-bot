from datetime import date, datetime, timedelta

# Helper Functions:
# Appends complaint to database
def gcFile(sheet, accused: str, tea: str, ban: str, author: str):
    currentDate = date.today().isoformat()
    all_values = sheet.get_all_values()
    sheet.append_row([accused, currentDate, tea.content, ban.content, author])

# Compiles complaint report for admins by username
# Need to update to include date range. Maybe default to past month? (01/15/2024)
def teaGet(sheet, user: str):
    complaint_values = sheet.get_all_values()
    filtered_complaints = [row for row in complaint_values if row[0] == user]
    return filtered_complaints

# Auto demotion updater:
def autoDemoUpdate(sheet):
    now = datetime.today()
    dataCheck = sheet.get_all_values()
    autoCheck = [row for row in dataCheck[1:] if datetime.strptime(row[2], "%Y-%m-%d") < now]
    
    if autoCheck:
        usersDemoOver = []
        for del_row in autoCheck:
            usersDemoOver.append(del_row[0])
            row_to_delete = dataCheck.index(del_row) + 1
            sheet.delete_rows(row_to_delete)
        return usersDemoOver

# Demotion checker
def demoCheck(sheet, user: str):
    demotion_check = sheet.get_all_values()
    userFilter = [row for row in demotion_check if row[0] == user]
    weeksPassed = datetime.today()

    if userFilter:
        target_row = userFilter[0]

        # Obtain cells to update
        cellUpdate = "B" + str(demotion_check.index(target_row) + 1)
        #dateCellUpdate = "C" + str(demotion_check.index(target_row) + 1)
        #target_col_index = 1
        target_date_index = 2

        current_end_date = datetime.strptime(target_row[target_date_index], "%Y-%m-%d")
        #current_weeks = int(target_row[target_col_index])
        totalWeeksLeft = (current_end_date - weeksPassed).days // 7 + 1

        sheet.update(values=str(totalWeeksLeft), range_name=cellUpdate)
        userFilter = [row for row in sheet.get_all_values() if row[0] == user]
        
    return userFilter


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