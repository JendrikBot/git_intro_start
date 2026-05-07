# https://dodona.be/nl/courses/5023/series/57878/activities/848884562


# zet je oplossing in de functie main
def main():
    zin = str(input())
    code = str()
    for i in zin:
        a = str(ord(i))
        if len(a) <= 3:
            b = "0" * (3 - len(a)) + a
        code += b
    print(code[::-1])


# enkel om lokaal te kunnen testen
if __name__ == "__main__":
    main()
