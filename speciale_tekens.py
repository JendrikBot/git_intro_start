# https://dodona.be/nl/courses/5023/series/57878/activities/947407390

import string


# zet je oplossing in de functie main
def main():
    zin = str(input())
    tekens = 0
    spatie = 0
    for i in zin:
        if i in string.punctuation:
            tekens += 1
        if i in string.whitespace:
            spatie += 1
    print(tekens + spatie)


# enkel om lokaal te kunnen testen
if __name__ == "__main__":
    main()
