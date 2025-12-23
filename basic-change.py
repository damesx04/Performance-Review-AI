# Basic Python script with some changes

# Initial version: simple print
print("Hello, World!")

# Change 1: Add a variable
name = "User"
print(f"Hello, {name}!")

# Change 2: Add a function
def greet(person):
    return f"Greetings, {person}!"

print(greet(name))

# Change 3: Add a list and loop
items = ["apple", "banana", "cherry"]
for item in items:
    print(f"Fruit: {item}")

print("Script completed with changes.")

# Change 4: Add a dictionary for data management
user_data = {
    "name": "Alice",
    "age": 30,
    "email": "alice@example.com"
}

print("User Information:")
for key, value in user_data.items():
    print(f"  {key}: {value}")

# Change 5: Add error handling
def divide(a, b):
    try:
        result = a / b
        return result
    except ZeroDivisionError:
        print("Error: Cannot divide by zero!")
        return None

print(f"10 / 2 = {divide(10, 2)}")
print(f"10 / 0 = {divide(10, 0)}")

# Change 6: Add a class definition
class Calculator:
    def __init__(self, name):
        self.name = name
    
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
    
    def display_result(self, operation, result):
        print(f"{self.name}: {operation} = {result}")

calc = Calculator("MyCalc")
calc.display_result("5 + 3", calc.add(5, 3))
calc.display_result("4 * 7", calc.multiply(4, 7))

# Change 7: Add list comprehension
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
print(f"Original numbers: {numbers}")
print(f"Squared numbers: {squared}")

print("All changes completed successfully!")
