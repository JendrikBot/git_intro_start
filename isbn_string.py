# https://dodona.be/nl/courses/5023/series/57878/activities/326198308


# zet je oplossing in de functie main
def main():
    code = str(input())
    x = 1
    som = 0
    for i in range(0, 9):
        som += x * int(code[i])
        x += 1
    controle = som % 11
    if strcode[9] == "x" and controle == 10:
        print("OK")
    elif int(code[9]) == controle:
        print("OK")
    else:
        print("FOUT")


# enkel om lokaal te kunnen testen
if __name__ == "__main__":
    main()
