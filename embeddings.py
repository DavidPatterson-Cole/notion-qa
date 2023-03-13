import openai
from openai.embeddings_utils import get_embedding, cosine_similarity
import os
import cohere
co = cohere.Client(os.environ.get('COHERE_API_KEY'))

cohere_doc3 = "SUBJECT: Your card has been charged $373.52 by Air Canada|EMAIL_FROM: Mercury hello@mercury.com|RECEIVED DATE: Tue, 22 Feb 2022 21:49:18 +0000|CONTENT: Hi DavidYour Mercury debit card ••4605 has been preauthorized for $373.52 by Air Canada.The settled amount may be different from this initial authorization and will be withdrawn from your companys Mercury checking account ••7681.https//mercury.com/transactions/3677f204-9429-11ec-a798-2b865b4c9cb5If you have any questions just reply to this email.If this transaction is in error you can raise a dispute atFrontendLink {frontendLinkToText = \"https//mercury.com/transactions/dispute/3677f204-9429-11ec-a798-2b865b4c9cb5\"}The Mercury TeamYou are receiving notifications for outgoing transactions over $100.00.Manage your subscriptions https//mercury.com/settings/notifications"
cohere_doc2 = "SUBJECT: Your receipt from ePropel #2447-9147|EMAIL_FROM: ePropel receipts+acct_1GHAJXBRDH6XiYeS@stripe.com|RECEIVED DATE: Wed, 20 Jan 2021 21:18:14 +0000|CONTENT: -moz-osx-font-smoothing grayscalefont-family -apple-system BlinkMacSystemFont Segoe UI Roboto Helvetica Neue Ubuntu sans-serifmso-line-height-rule exactlyvertical-align middlecolor #8898aafont-size 12pxline-height 16pxwhite-space nowrapfont-weight boldtext-transform uppercase\"> Amount paid     C$1750.00             Date paid     January 20 2021            <td class=\"Font Font--caption Font--uppercase Font--mute Font--noWrap\" style=\"border 0border-collapse collapsemargin 0padding 0-webkit-font-smoothing antialiased-moz-osx-font-smoothing grayscalefont-family -apple-system BlinkMacSystemFont Segoe UI Roboto Helvetica Neue Ubuntu sans-serifmso-line-height-rule exactlyvertical-align middlecolor #8898aa"
cohere_doc1 = "SUBJECT: Booking confirmation - heres a link to your tickets | Sun, 3 April - XJGM3J|EMAIL_FROM: Eurostar International LTD noreply@e.eurostar.com|RECEIVED DATE: Tue, 22 Feb 2022 15:16:17 -0600|CONTENT: margin0margin-bottom10pxmargin-top10pxpadding0text-alignleft\">If you need a little help getting to or from the train youll need to check our special assistance page to prebook our service before travellingFull details on special assistance Whats on boardIf you find yourself feeling peckish en route just head to Café Metropole our onboard bar buffet to pick up drinks snacks and meals to suit every taste and time of day.Log in to <a href=\"http//click.e.eurostar.com/?qs=5045cc0f3399a8d08e91bcc45eae37eb3ad59e5b3be84c1e5240078f367ee628a4602a2950449dfc3ab3609f00a72b26f1c82317e446c02744b44780a48774c1"


document1 = "SUBJECT: Re: Senior Account Manager Application - Lana Tang|EMAIL_FROM: Lana Tang lana.tang@mail.utoronto.ca|RECEIVED DATE: Thu, 24 Feb 2022 21:51:47 +0000|CONTENT: \nlana.tang@mail.utoronto.ca\n(647) 918-6991\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
document2 = "SUBJECT: Re: Senior Account Manager Application - Lana Tang|EMAIL_FROM: david@moonchaser.io|RECEIVED DATE: Thu, 24 Feb 2022 23:29:16 +0000|CONTENT: \n experience and project exposure. All in all I am willing to put in extra time and do whatever it takes to ensure that I am putting out quality work. \n\n\nMoonchaser's operating model intrigues me and I hope to have the opportunity to provide value to both Moonchaser and clients through developing processes negotiation strategies and more. I have attached a copy of my resume to this email as per the \n job posting instructions and I hope that you can find a time to take a quick look at it. Thank you in advance for your consideration and I look forward to the chance to further discuss my qualifications.\n\n\nSincerely \nLana Tang | Rotman Commerce Student Class of 2022\nlana.tang@mail.utoronto.ca\n(647) 918-6991\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
document3 = "SUBJECT: New Event: Lana Tang - 19:00 Tue, 8 Feb 2022 - Account Manager Interview 30min|EMAIL_FROM: Calendly notifications@calendly.com|RECEIVED DATE: Tue, 01 Feb 2022 21:51:15 +0000 (UTC)|CONTENT: \n\n\n\nCalendly\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n \n Hi David Patterson-Cole \n\n \n A new event has been scheduled. \n\n\n \n Event Type: \n \n \n Account Manager Interview 30min \n\n\n \n Invitee: \n \n \n Lana Tang \n\n\n \n Invitee Email: \n \n\nlana.tang@mail.utoronto.ca\n\n\n \n Text Reminder Number: \n \n\n+1 647-918-6991\n\n\n \n Event Date/Time: \n \n \n 19:00 - Tuesday 8 February 2022 (Eastern Time - US & Canada) \n\n\n \n Description: \n \n\nLet's meet on the Google Meet\n\n \n Location: \n \n\n\n \n This is a Google Meet web conference. \n Join now\n\n\n\n \n Invitee Time Zone: \n \n \n Eastern Time - US & Canada \n\nQuestions:\n\n \nLinkedIn \n\n\nhttps://linkedin.com/in/lana-tang\n\n \nPhone Number \n\n\n6479186991\n\n \nPlease share anything that will help prepare for our meeting. \n\n\nAccount Manager Interview\n\nView event in Calendly\n\n\n\n \n \nPro Tip! \n \n\n\n\n\n\n\n\n\n \nTake Calendly anywhere you work \n\n \nUse Calendly anywhere on the web without switching tabs! Access your event types share your Calendly link and create meetings right from your Gmail or Outlook. Get Calendly for Chrome Firefox or Outlook. \nSee all apps\n\n\n\n\n\n\n\n\n\n\n\n \n Sent from Calendly\n\n\n\n\n \n Report this event \n \n\n\n\n\n\n\n"

# query = "Lana Tang LinkedIn"
# 0.848362197486316
# 0.8384604185314991
# 0.8339375551286695
# query = "Find the $ value paid to Air Canada. If multiple, record all $ values paid."
query = "Find Lana Tang's LinkedIn"
# query="Lana Tang LinkedIn"
# 0.8251070399703837
# 0.8176167684193523
# 0.8216513359615417
# document1 = "SUBJECT: Re: Senior Account Manager Application - Lana Tang|EMAIL_FROM: Lana Tang lana.tang@mail.utoronto.ca|RECEIVED DATE: Thu, 24 Feb 2022 21:51:47 +0000|CONTENT: \nlana.tang@mail.utoronto.ca\n(647) 918-6991\n"
# document2 = "SUBJECT: Re: Senior Account Manager Application - Lana Tang|EMAIL_FROM: david@moonchaser.io|RECEIVED DATE: Thu, 24 Feb 2022 23:29:16 +0000|CONTENT: \n experience and project exposure. All in all I am willing to put in extra time and do whatever it takes to ensure that I am putting out quality work. \nMoonchaser's operating model intrigues me and I hope to have the opportunity to provide value to both Moonchaser and clients through developing processes negotiation strategies and more. I have attached a copy of my resume to this email as per the job posting instructions and I hope that you can find a time to take a quick look at it. Thank you in advance for your consideration and I look forward to the chance to further discuss my qualifications.\nSincerely \nLana Tang | Rotman Commerce Student Class of 2022\nlana.tang@mail.utoronto.ca\n(647) 918-6991\n"
# document3 = "SUBJECT: New Event: Lana Tang - 19:00 Tue, 8 Feb 2022 - Account Manager Interview 30min|EMAIL_FROM: Calendly notifications@calendly.com|RECEIVED DATE: Tue, 01 Feb 2022 21:51:15 +0000 (UTC)|CONTENT: \nCalendly\n Hi David Patterson-Cole \nA new event has been scheduled. \n Event Type: \n Account Manager Interview 30min \nInvitee: Lana Tang\n Invitee Email: lana.tang@mail.utoronto.ca\nText Reminder Number: +1 647-918-6991\nEvent Date/Time: 19:00 - Tuesday 8 February 2022 (Eastern Time - US & Canada)\nDescription:Let's meet on the Google Meet\nLocation: This is a Google Meet web conference. \n Join now\n Invitee Time Zone: Eastern Time - US & Canad\nQuestions:\nLinkedIn\nhttps://linkedin.com/in/lana-tang\nPhone Number\n6479186991\nPlease share anything that will help prepare for our meeting. \nAccount Manager Interview\nView event in Calendly\nPro Tip!\nTake Calendly anywhere you work \nUse Calendly anywhere on the web without switching tabs! Access your event types share your Calendly link and create meetings right from your Gmail or Outlook. Get Calendly for Chrome Firefox or Outlook. \nSee all apps\n Sent from Calendly\n Report this event \n"
# 0.8295362336118601
# 0.8219661961935296
# 0.8272953444058048
# query = "Find Lana Tang's LinkedIn URL. LinkedIn. LinkedIn"
# 0.8175371508696839
# 0.8057601262176053
# 0.8067567854856251


response = openai.Embedding.create(
    input=document1,
    model="text-embedding-ada-002"
)
emb1 = response['data'][0]['embedding']

response = openai.Embedding.create(
    input=document2,
    model="text-embedding-ada-002"
)
emb2 = response['data'][0]['embedding']

response = openai.Embedding.create(
    input=document3,
    model="text-embedding-ada-002"
)
emb3 = response['data'][0]['embedding']

response = openai.Embedding.create(
    input=query,
    model="text-embedding-ada-002"
)
emb_query = response['data'][0]['embedding']

# for emb in [emb1, emb2, emb3]:
#     print(cosine_similarity(emb, emb_query))

print(f'{query=}')
reranked_vectors = co.rerank(query=query, documents=[document1, document2, document3], top_n=3)
for vector in reranked_vectors:
  formatted_vector = "{}".format(vector.document['text'].replace("\n", "\\n"))
  print(formatted_vector)
  print('\n')