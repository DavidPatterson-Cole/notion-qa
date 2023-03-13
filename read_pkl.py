import pickle

# with open('invoices.pkl', 'rb') as f:
#     invoices = pickle.load(f)
#     text = str(invoices)
#     print(text)

with open('zapier.pkl', 'rb') as f:
    while True:
        try:
            data = pickle.load(f)
            print(data)
        except EOFError:
            break