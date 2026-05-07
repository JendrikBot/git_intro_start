# https://dodona.be/nl/courses/5023/series/57878/activities/1432134608


# zet je oplossing in de functie main
def main():
    code = str(input())[::-1]
    zin = ""
    for i in range(0, len(code), 3):
        a = code[i : i + 3] + " "
        zin += chr(int(a))
    print(zin)


# enkel om lokaal te kunnen testen
if __name__ == "__main__":
    main()
