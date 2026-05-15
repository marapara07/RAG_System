from services.rag_service import ask_rag

result = ask_rag("What is the purpose of the employee handbook?")

print("ANSWER:")
print(result["answer"])

print("\nSOURCES:")
for source in result["sources"]:
    print("-", source)