# import win32com.client as win32
#
# recipients = "bgorman@live.com; bgorman@live.ca"
# cc_recipients = "brandon.gorman@englobecorp.com"
# subject = "97 Troop Avenue - Concrete Testing Results"
# with open("Signature/CONCRETE.htm", "r") as file:
#     body_text = file.read()
#
# attachment = r"C:\\Users\\gormbr\\OneDrive - EnGlobe Corp\\Desktop\\March 2020 District Contact Listings.pdf"
# # outlook = win32.Dispatch('outlook.application').GetNameSpace("MAPI")
# # for i in range(50):
# #     try:
# #         box = outlook.GetDefaultFolder(i)
# #         name = box.Name
# #         print(i, name)
# #     except:
# #         pass
#
# # outlook = win32.Dispatch('outlook.application')
# # mail = outlook.CreateItem(0)
# # mail.To = recipients
# # mail.CC = cc_recipients
# # mail.Subject = subject
# # mail.HtmlBody = body_text
# # mail.Attachments.Add(attachment)
# # mail.Save()
#
# try:
#     attachments = []
#     outlook = win32.Dispatch('outlook.application').GetNameSpace("MAPI")
#     drafts = outlook.GetDefaultFolder(16)  # 16 = drafts
#     emails = drafts.Items
#     for message in emails:
#         attachments = message.Attachments
#     if attachments:
#         for attachment in attachments:
#             print(attachment.filename)
# except Exception as e:
#     print(e)

value1 = 'Eec'


def hamming_distance(found_value, file_value):
    return sum(c1 != c2 for c1, c2 in zip(found_value, file_value))


def month_value(found_month):

    # If detected month is not found in the above dictionary, it is obviously a bad detected letter
    # To ease file renaming, find month closest in similarity and assume that was the one detected.
    closest_month = found_month
    if found_month not in months:
        similarity_highest = 999
        for month in months:
            similarity = hamming_distance(found_month, month)
            if similarity < similarity_highest:
                closest_month = month
                similarity_highest = similarity
    return closest_month, months[closest_month]


month1, value = month_value(value1)

string = 'Closest value to ' + value1 + ': ' + month1

print(string)
