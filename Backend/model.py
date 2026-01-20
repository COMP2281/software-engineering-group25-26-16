from ollama import generate

def test():
    # Regular response
    response = generate('granite4:350m', 'Why is the sky blue? Give response in 1 sentence with at most 3 clauses.')
    print(response['response'])

if __name__ == "__main__":
    test()
