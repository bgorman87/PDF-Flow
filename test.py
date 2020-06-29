import win32com.client as win32

recipients = "bgorman@live.com; bgorman@live.ca"
cc_recipients = "brandon.gorman@englobecorp.com"
subject = "97 Troop Avenue - Concrete Testing Results"
with open("Signature/CONCRETE.htm", "r") as file:
    body_text = file.read()

attachment = r"C:\\Users\\gormbr\\OneDrive - EnGlobe Corp\\Desktop\\March 2020 District Contact Listings.pdf"

outlook = win32.Dispatch('outlook.application')
mail = outlook.CreateItem(0)
mail.To = recipients
mail.CC = cc_recipients
mail.Subject = subject
mail.HtmlBody = body_text
mail.Attachments.Add(attachment)
mail.Save()

