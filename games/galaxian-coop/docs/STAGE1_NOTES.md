# Galaxian NES DX — etap 1 (eksperymentalny, historyczny)

> Zastąpione przez Stage 2 – patrz CHANGELOG.md. Bufor `$07F0` okazał się zajęty przez grę.

## Docelowa mechanika
- Dwa statki jednocześnie, sterowanie P1/P2.
- Osobne 3 życia dla każdego gracza.
- Statki przenikają się wzajemnie.
- Osobne pociski, trafienia, wynik i kolizje z przeciwnikami.

## Potwierdzone w przesłanym ROM-ie
- NES 2.0, mapper 0, 8 KiB PRG, 8 KiB CHR.
- NMI: $E20C; reset/IRQ: $E020 (wektory na końcu PRG).
- $E54D: zapis 1 do $4016, następnie 0 (strobe).
- $E55F–$E573: osiem kolejnych odczytów $4016 i $4017; wejścia odkładane do RAM $EF i $F1.
- $E576–$E57F: bit 0 adresu $53 wybiera aktywnego gracza, a jego przyciski trafiają do $4C.

## Wykonany prototyp
`build.py` tworzy rozszerzony ROM NROM-256 (32 KiB PRG) i podmienia instrukcje przy `$E57A` na `JSR $8000` + NOP. Kod `$8000` wykonuje oryginalne instrukcje wyboru aktywnego pada, a dodatkowo kopiuje `$F1` do `$07F0` jako eksperymentalny bufor przycisków P2. Pozostawia A, X i flagi tak, jak oryginalna sekwencja.

**To jeszcze nie jest co-op:** nie powstaje drugi statek, nie ma drugich pocisków, osobnych żyć ani zmian w kolizjach. Bufor `$07F0` nie jest jeszcze zweryfikowany jako wolny w całej grze. Patch wymaga testu w emulatorze i może powodować błędy; zachowaj oryginalny ROM.

## Następne etapy (wymagana analiza debuggerem)
1. Zweryfikować w Mesen 2 wartości `$EF`, `$F1`, `$4C`, `$53`, `$07F0` oraz zapisy do `$07F0` (watchpoint).
2. Zlokalizować X/Y gracza w RAM, wpisy jego sprite'ów w OAM `$0200..$02FF` i kod ich aktualizacji.
3. Zidentyfikować pozycję i stan pocisku, sprawdzanie kolizji, życia i licznik punktów.
4. Dodać oddzielny stan P2, sprite i ruch; później pocisk, kolizje i odrębne życia.

Uruchom `python3 build.py` w katalogu projektu, z oryginalnym ROM-em w katalogu nadrzędnym.
