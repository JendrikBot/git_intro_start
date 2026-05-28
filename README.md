In dit project werd gewerkt rond slaapproblematiek bij jonge kinderen. Dit ontwerp dient te wekker als buffer tussen het ontwaken van een kind 's nachts en de tussenkomst door ouders. Zo moeten ouders 's nachts minder ontwaken, waardoor de nachtrust ononderbroken blijft en ze overdag minder stress ervaren. Het systeem is ontworpen rond een Raspberry pi zero W 2 met header als centrale rekenmodule. 
![RaspPi](./imgs/zero2-close-up.png)

Aan de Raspberry Pi wordt een projector bevestigd aan de HDMI uitgang en worden een microfoon en een breadboard aangesloten op de GPIO pinnen. 
![setup](./imgs/connectieschema.png)

De benodigdheden om dit project te maken staan hieronder in een Bill Of Materials. 

| **Onderdeel**               |**prijs (€)**|
| -----------------------     | --------------------|
| Mini-videoprojector         | 54,99               |
| Raspberry Pi Zero  2 W      | 20,56               |
| mini HDMI naar HDMI-adapter | 11,90               |
| Voeding (5.1 V 2.5 A)       | 8,82                |
| USB C female naar micro USB male adapter                       | 1,08                |
|USB C naar USB A hub         | 7,99                |
|Philips 16GB micro SD        | 9,95                |
|Breadboard                   | 4,99                |
| **Totaal**                  | **120,28**        |

Wanneer al deze onderdelen aan elkaar geconnecteerd worden bekom je: ![foto](./imgs/RPI_setup.JPEG)

Het breadboard dient in deze schakeling enkel voor visuele feedback, zo is het snel duideijk dat de projector zal projecteren. Dit is nodig omdat de Raspberry pi in combinatie met de projector zorgt voor latency, waardoor het uitgangssignaal wat vertraging heeft.

Uiteindelijk was [dit filmpje](./filmpje%20opktech.mp4) Het uiteindelijke resultaat dat bekomen was. 